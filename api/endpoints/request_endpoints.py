from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.session import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.database import Request, Employee, Status, StatusKeys
from pydantic import BaseModel
from api.utils import parse_date
from datetime import datetime, date


router = APIRouter(
    prefix="/requests",
    tags=["requests"]
)


class RequestCreate(BaseModel):
    request_date_weekend: str
    description: str
    id_employee: int

class StatusUpdate(BaseModel):
    id_status: int


@router.post("/")
def post_request(request_data: RequestCreate,
                 db: Session = Depends(get_db)
                 ):
    employee = db.query(Employee).filter(Employee.id_employee == request_data.id_employee).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Сотрудник с таким id не найден")

    if isinstance(request_data.request_date_weekend, str):
        try:
            date_obj = parse_date(request_data.request_date_weekend)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат даты: {str(e)}. Используйте формат ГГГГ-ММ-ДД"
            )
    else:
        date_obj = request_data.request_date_weekend

    if isinstance(date_obj, datetime):
        request_date = date_obj.date()
    else:
        request_date = date_obj

    today = date.today()

    if request_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Нельзя создать заявку на прошедшую дату",
                "requested_date": str(request_date),
                "today": str(today)
            }
        )

    existing_request = db.query(Request).filter(
        Request.id_employee == request_data.id_employee,
        func.date(Request.reques_date_weekend) == request_date
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Заявка на эту дату уже существует",
                "existing_request_id": existing_request.id_request,
                "date": str(request_date)
            }
        )

    clean_date = datetime.combine(request_date, datetime.min.time())

    new_request = Request(
        reques_date_weekend=clean_date,
        description=request_data.description,
        id_status=StatusKeys.PENDING,
        id_employee=request_data.id_employee
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@router.get("/")
def get_request(db: Session = Depends(get_db)):
    requests = db.query(Request).all()
    return requests


@router.put("/{request_id}/status")
def update_request_status(
        request_id: int,
        status_data: StatusUpdate,
        db: Session = Depends(get_db)
):

    request = db.query(Request).filter(Request.id_request == request_id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос не найден"
        )

    new_status = db.query(Status).filter(Status.id_status == status_data.id_status).first()
    if new_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Статус с таким id не найден"
        )

    old_status_id = request.id_status

    request.id_status = status_data.id_status
    db.commit()
    db.refresh(request)

    return {
        "message": "Статус запроса обновлён",
        "request_id": request_id,
        "old_status_id": old_status_id,
        "new_status_id": status_data.id_status,
        "new_status_name": new_status.name_status
    }

@router.delete("/{request_id}")
def delete_request(
        request_id: int,
        db: Session = Depends(get_db)
):
    request = db.query(Request).filter(Request.id_request == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Запрос не найден")
    db.delete(request)
    db.commit()
    return {"message": f"Запрос на выходной на {request.reques_date_weekend} удален"}




