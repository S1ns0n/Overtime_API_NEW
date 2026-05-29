from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.database import Overtime, Employee, Weekend
from pydantic import BaseModel
from api.config import Config
from api.utils import parse_date

from fastapi.responses import StreamingResponse
from api.excel_generator import generate_overtime_report
import urllib.parse


router = APIRouter(
    prefix="/overtimes",
    tags=["overtimes"]
)


class OvertimeCreate(BaseModel):
    id_employee: int
    name_overtime: str
    overtime_hours: int
    date_overtime: str


@router.post("/")
def post_overtime(
        overtime_data: OvertimeCreate,
        db: Session = Depends(get_db)
):
    # ========== 1. Проверка сотрудника ==========
    employee = db.query(Employee).filter(
        Employee.id_employee == overtime_data.id_employee
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сотрудник с таким id не найден"
        )

    # ========== 2. Преобразование даты ==========
    if isinstance(overtime_data.date_overtime, str):
        try:
            overtime_date = parse_date(overtime_data.date_overtime)
            if isinstance(overtime_date, datetime):
                overtime_date = overtime_date.date()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат даты: {str(e)}. Используйте формат ГГГГ-ММ-ДД"
            )
    else:
        overtime_date = overtime_data.date_overtime

    # ========== 3. Проверка: нет ли выходного на эту дату ==========
    existing_weekend = db.query(Weekend).filter(
        Weekend.id_employee == overtime_data.id_employee,
        func.date(Weekend.date_weekend) == overtime_date
    ).first()

    if existing_weekend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Нельзя создать переработку на дату, когда у сотрудника выходной",
                "weekend_id": existing_weekend.id_weekend,
                "weekend_date": str(overtime_date)
            }
        )

    # ========== 4. Проверка: не больше 4 часов ==========
    if overtime_data.overtime_hours > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Переработка не может превышать 4 часа"}
        )

    # ========== 5. Проверка: нельзя два дня подряд ==========
    yesterday = overtime_date - timedelta(days=1)

    previous_overtime = db.query(Overtime).filter(
        Overtime.id_employee == overtime_data.id_employee,
        Overtime.date_overtime == yesterday
    ).first()

    if previous_overtime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Нельзя создавать переработки два дня подряд",
                "last_overtime_date": str(yesterday),
                "last_overtime_id": previous_overtime.id_overtime,
                "last_overtime_hours": previous_overtime.overtime_hours,
                "requested_date": str(overtime_date)
            }
        )

    # Проверяем, нет ли уже переработки на эту дату
    same_day_overtime = db.query(Overtime).filter(
        Overtime.id_employee == overtime_data.id_employee,
        Overtime.date_overtime == overtime_date
    ).first()

    if same_day_overtime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Переработка на эту дату уже существует",
                "existing_overtime_id": same_day_overtime.id_overtime,
                "date": str(overtime_date)
            }
        )

    # ========== 6. Проверка лимита часов ==========
    total_overtime = db.query(
        func.coalesce(func.sum(Overtime.overtime_hours), 0)
    ).filter(
        Overtime.id_employee == overtime_data.id_employee
    ).scalar()

    new_total = total_overtime + overtime_data.overtime_hours

    if new_total > Config.MAX_OVERTIME_HOURS:
        available = Config.MAX_OVERTIME_HOURS - total_overtime

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Превышен лимит переработок",
                "current_hours": total_overtime,
                "requested_hours": overtime_data.overtime_hours,
                "max_hours": Config.MAX_OVERTIME_HOURS,
                "available_hours": available,
                "exceeded_by": new_total - Config.MAX_OVERTIME_HOURS
            }
        )

    # ========== 7. Создание переработки ==========
    new_overtime = Overtime(
        id_employee=overtime_data.id_employee,
        name_overtime=overtime_data.name_overtime,
        overtime_hours=overtime_data.overtime_hours,
        date_overtime=overtime_date
    )

    db.add(new_overtime)
    employee.overtime_hours = new_total
    db.commit()
    db.refresh(new_overtime)

    return {
        "overtime": new_overtime,
        "total_overtime_hours": new_total,
        "remaining_hours": Config.MAX_OVERTIME_HOURS - new_total
    }

@router.get("/")
def get_overtime(db: Session = Depends(get_db)):
    overtimes = db.query(Overtime).all()
    return overtimes


@router.delete("/{overtime_id}")
def delete_overtime(
        overtime_id: int,
        db: Session = Depends(get_db)
):
    overtime = db.query(Overtime).filter(Overtime.id_overtime == overtime_id).first()
    if overtime is None:
        raise HTTPException(status_code=404, detail="Переработка не найдена")
    db.delete(overtime)
    db.commit()
    return {"message": f"Переработка {overtime.name_overtime} удалена"}


@router.get("/report/{employee_id}")
def get_overtime_report(
        employee_id: int,
        db: Session = Depends(get_db)
):
    """
    Скачать Excel отчёт по переработкам сотрудника
    """
    # ========== 1. Проверка сотрудника ==========
    employee = db.query(Employee).filter(
        Employee.id_employee == employee_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сотрудник с таким id не найден"
        )

    # ========== 2. Получаем все переработки ==========
    overtimes = db.query(Overtime).filter(
        Overtime.id_employee == employee_id
    ).order_by(Overtime.date_overtime).all()

    # ========== 3. Считаем общие часы ==========
    total_hours = db.query(
        func.coalesce(func.sum(Overtime.overtime_hours), 0)
    ).filter(
        Overtime.id_employee == employee_id
    ).scalar()

    remaining = Config.MAX_OVERTIME_HOURS - total_hours

    # ========== 4. Подготовка данных для Excel ==========
    employee_data = {
        'full_name': f"{employee.surname_employee} {employee.name_employee} {employee.patronymic_employee}",
        'post': employee.post_employee,
        'office': employee.office_employee,
        'email': employee.email_employee,
        'phone': employee.phone_employee,
        'total_hours': total_hours,
        'remaining_hours': remaining if remaining > 0 else 0,
    }

    overtimes_list = []
    for ot in overtimes:
        overtimes_list.append({
            'id_overtime': ot.id_overtime,
            'date_overtime': ot.date_overtime.strftime('%d.%m.%Y') if ot.date_overtime else '',
            'name_overtime': ot.name_overtime,
            'overtime_hours': ot.overtime_hours,
            'status': 'Активен',
        })

    # ========== 5. Генерируем Excel ==========
    excel_file = generate_overtime_report(employee_data, overtimes_list)

    # ========== 6. Формируем имя файла (БЕЗ КИРИЛЛИЦЫ) ==========
    filename = f"overtime_report_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Кодируем имя файла для HTTP заголовка
    encoded_filename = urllib.parse.quote(filename)

    # ========== 7. Отправляем файл ==========
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


