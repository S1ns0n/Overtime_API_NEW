from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.session import get_db
from sqlalchemy.orm import Session
from api.database import Status
from pydantic import BaseModel

router = APIRouter(
    prefix="/status",  # ← ВОТ ПРЕФИКС
    tags=["status"]     # Группировка в документации
)

class StatusCreate(BaseModel):
    name_status: str

@router.post("/")
def post_status(status_data: StatusCreate,
                db : Session = Depends(get_db)
                ):
    new_status = Status(
        name_status=status_data.name_status
    )
    db.add(new_status)
    db.commit()
    db.refresh(new_status)
    return new_status

@router.get("/")
def get_status(db: Session = Depends(get_db)):
    status = db.query(Status).all()
    return status

@router.delete("/{status_id}")
def delete_status(
        status_id: int,
        db: Session = Depends(get_db)
        ):
    status = db.query(Status).filter(Status.id_status == status_id).first()
    if status is None:
        raise HTTPException(status_code=404,detail="Статус не найден")
    db.delete(status)
    db.commit()
    return {"message": f"Статус {status.name_status} удалён"}