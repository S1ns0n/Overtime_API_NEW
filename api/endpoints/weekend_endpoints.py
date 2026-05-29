from fastapi import APIRouter, Depends, HTTPException, status
from api.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.database import Weekend, Employee, Status, Request, StatusKeys
from pydantic import BaseModel
from api.utils import parse_date
from api.session import get_status_by_key
from datetime import datetime, date

router = APIRouter(
    prefix="/weekends",
    tags=["weekends"]
)


class WeekendCreate(BaseModel):
    id_employee: int
    date_weekend: str
    id_request: int


@router.post("/")
def post_weekend(weekend_data: WeekendCreate,
                 db: Session = Depends(get_db)
                 ):
    # ========== 1. Проверка сотрудника ==========
    employee = db.query(Employee).filter(
        Employee.id_employee == weekend_data.id_employee
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сотрудник с таким id не найден"
        )

    # ========== 2. Проверка запроса ==========
    request = db.query(Request).filter(
        Request.id_request == weekend_data.id_request
    ).first()

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос с таким id не найден"
        )

    # ========== 3. Проверка: запрос должен быть "Подтверждён" ==========
    approved_status = get_status_by_key(db, StatusKeys.APPROVED)

    if approved_status is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Статус 'Подтверждён' не найден в системе"
        )

    if request.id_status != approved_status.id_status:
        # Получаем текущий статус запроса для информативного ответа
        current_status = db.query(Status).filter(
            Status.id_status == request.id_status
        ).first()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Нельзя создать выходной по неподтверждённому запросу",
                "request_id": request.id_request,
                "current_status": current_status.name_status if current_status else "неизвестно",
                "required_status": approved_status.name_status
            }
        )

    # ========== 4. Проверка: запрос и выходной для одного сотрудника ==========
    if request.id_employee != weekend_data.id_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Запрос принадлежит другому сотруднику",
                "request_employee_id": request.id_employee,
                "weekend_employee_id": weekend_data.id_employee
            }
        )

    # ========== 5. Преобразование даты ==========
    if isinstance(weekend_data.date_weekend, str):
        try:
            date_obj = parse_date(weekend_data.date_weekend)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат даты: {str(e)}. Используйте формат ГГГГ-ММ-ДД"
            )
    else:
        date_obj = weekend_data.date_weekend

    # Выделяем только дату
    if isinstance(date_obj, datetime):
        request_date = date_obj.date()
    else:
        request_date = date_obj

    today = date.today()

    # ========== 6. Проверка: дата не в прошлом ==========
    if request_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Нельзя создать выходной на прошедшую дату",
                "requested_date": str(request_date),
                "today": str(today)
            }
        )

    # ========== 7. Проверка на дубликат ==========
    existing_weekend = db.query(Weekend).filter(
        Weekend.id_employee == weekend_data.id_employee,
        func.date(Weekend.date_weekend) == request_date
    ).first()

    if existing_weekend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Выходной на эту дату уже существует",
                "existing_weekend_id": existing_weekend.id_weekend,
                "date": str(request_date)
            }
        )

    # ========== 8. Проверка: хватает ли часов ==========
    HOURS_PER_DAY = 8

    if employee.overtime_hours < HOURS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Недостаточно часов переработки для выходного",
                "required_hours": HOURS_PER_DAY,
                "available_hours": employee.overtime_hours,
                "shortage": HOURS_PER_DAY - employee.overtime_hours
            }
        )

    # ========== 9. Создание выходного + списание часов ==========
    clean_date = datetime.combine(request_date, datetime.min.time())

    new_weekend = Weekend(
        id_employee=weekend_data.id_employee,
        date_weekend=clean_date,
        id_status=StatusKeys.ACTIVE,
        id_request=weekend_data.id_request
    )

    # Списываем часы
    employee.overtime_hours -= HOURS_PER_DAY

    db.add(new_weekend)
    db.commit()
    db.refresh(new_weekend)

    return {
        "weekend": new_weekend,
        "employee_name": f"{employee.surname_employee} {employee.name_employee}",
        "request_id": request.id_request,
        "hours_spent": HOURS_PER_DAY,
        "remaining_overtime_hours": employee.overtime_hours
    }

@router.get("/")
def get_weekend(db: Session = Depends(get_db)):
    weekends = db.query(Weekend).all()
    return weekends

@router.delete("/{weekend_id}")
def delete_weekend(
        weekend_id: int,
        db: Session = Depends(get_db)
        ):
     weekend = db.query(Weekend).filter(Weekend.id_weekend == weekend_id).first()
     if weekend is None:
        raise HTTPException(status_code=404,detail="Выходной не найден")
     db.delete(weekend)
     db.commit()
     return {"message":f"Выходной на дату {weekend.date_weekend} удален"}




