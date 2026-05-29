from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.session import get_db
from sqlalchemy.orm import Session
from api.database import Role
from pydantic import BaseModel

router = APIRouter(
    prefix="/roles",  # ← ВОТ ПРЕФИКС
    tags=["roles"]     # Группировка в документации
)


class RoleCreate(BaseModel):
    name_role: str


@router.post("/")
def post_role(role_data: RoleCreate,
              db:Session = Depends(get_db)
              ):
    new_role = Role(
        name_role = role_data.name_role
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@router.get("/")
def get_role(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return roles

@router.delete("/{role_id}")
def delete_role(
        role_id: int,
        db: Session = Depends(get_db)
        ):
     role = db.query(Role).filter(Role.id_role == role_id).first()
     if role is None:
        raise HTTPException(status_code=404,detail="Роль не найдена")
     db.delete(role)
     db.commit()
     return {"message":f"Роль {role.name_role} удалена"}




