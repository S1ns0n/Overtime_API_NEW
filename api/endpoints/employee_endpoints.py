from fastapi import APIRouter, Depends, HTTPException, status
from api.session import get_db
from sqlalchemy.orm import Session
from api.database import Employee, Role, Status, Space, StatusKeys
from pydantic import BaseModel

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)

class EmployeeCreate(BaseModel):
    surname_employee: str
    name_employee: str
    patronymic_employee: str
    login:str
    password: str
    post_employee: str
    office_employee: str
    phone_employee: str
    email: str
    overtime_hours:int
    id_role: int
    id_space:int

@router.get("/")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees

@router.post("/")
def post_employee(employee_data: EmployeeCreate,
                  db: Session = Depends(get_db)
                  ):
    role = db.query(Role).filter(Role.id_role == employee_data.id_role).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Роль с таким id не найдена")


    space = db.query(Space).filter(Space.id_space == employee_data.id_space).first()
    if space is None:
        raise HTTPException(status_code=404, detail="Пространство с таким id не найдено")


    new_employee = Employee(
        surname_employee = employee_data.surname_employee,
        name_employee = employee_data.name_employee,
        patronymic_employee = employee_data.patronymic_employee,
        login = employee_data.login,
        password = employee_data.password,
        post_employee = employee_data.post_employee,
        office_employee = employee_data.office_employee,
        phone_employee = employee_data.phone_employee,
        email_employee = employee_data.email,
        overtime_hours = employee_data.overtime_hours,
        id_role = employee_data.id_role,
        id_status = StatusKeys.ACTIVE,
        id_space = employee_data.id_space
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

@router.delete("/{employee_id}")
def delete_employee(
        employee_id: int,
        db: Session = Depends(get_db)
        ):
    employee = db.query(Employee).filter(Employee.id_employee == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404,detail="Сотрудник не найден")
    db.delete(employee)
    db.commit()
    return {"message": f"Сотрудник {employee.name_role} удален"}