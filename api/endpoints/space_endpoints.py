from fastapi import APIRouter, Depends, HTTPException, status, Body
from api.session import get_db
from sqlalchemy.orm import Session
from api.database import Space
from pydantic import BaseModel
import datetime

router = APIRouter(
    prefix="/spaces",  # ← ВОТ ПРЕФИКС
    tags=["spaces"]     # Группировка в документации
)


class SpaceCreate(BaseModel):
    name_space: str


@router.post("/")
def post_space(space_data: SpaceCreate,
              db:Session = Depends(get_db)
              ):
    new_space = Space(
        name_space = space_data.name_space,
        date_creation = datetime.datetime.now()
    )
    db.add(new_space)
    db.commit()
    db.refresh(new_space)
    return new_space

@router.get("/")
def get_space(db: Session = Depends(get_db)):
    spaces = db.query(Space).all()
    return spaces

@router.delete("/{space_id}")
def delete_space(
        space_id: int,
        db: Session = Depends(get_db)
        ):
     space = db.query(Space).filter(Space.id_space == space_id).first()
     if space is None:
        raise HTTPException(status_code=404,detail="Пространство не найдено")
     db.delete(space)
     db.commit()
     return {"message":f"Пространство {space.name_space} удалено"}