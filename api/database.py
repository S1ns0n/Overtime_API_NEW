from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, date

Base = declarative_base()

class StatusKeys:
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Employee(Base):
    __tablename__ = 'employee'

    id_employee = Column(Integer, primary_key=True)
    surname_employee = Column(String(150), nullable=False)
    name_employee = Column(String(150), nullable=False)
    patronymic_employee = Column(String(150), nullable=False)
    login = Column(String(150), unique=True, nullable=False)
    password = Column(String(555), nullable=False)
    post_employee = Column(String(150), nullable=False)
    office_employee = Column(String(150), nullable=False)
    phone_employee = Column(String(12), nullable=False)
    email_employee = Column(String(150), unique=True,nullable=False)
    overtime_hours = Column(Integer,nullable=False)

    id_role = Column(Integer, ForeignKey('role.id_role'))
    id_status = Column(Integer,ForeignKey('status.id_status'))
    id_space = Column(Integer,ForeignKey('space.id_space'))


class Role(Base):
    __tablename__ = 'role'

    id_role = Column(Integer, primary_key=True)
    name_role = Column(String(555),nullable=False)



class Space(Base):
    __tablename__ = 'space'

    id_space = Column(Integer,primary_key=True)
    name_space = Column(String(555),nullable=False)
    date_creation = Column(Date,nullable=False)


class Weekend(Base):
    __tablename__ = 'weekend'

    id_weekend = Column(Integer,primary_key=True)
    date_weekend = Column(Date,nullable=False)

    id_employee = Column(Integer,ForeignKey('employee.id_employee'))
    id_status = Column(Integer, ForeignKey('status.id_status'))
    id_request = Column(Integer,ForeignKey('request.id_request'))


class Status(Base):
    __tablename__ = 'status'

    id_status = Column(Integer,primary_key=True)
    name_status = Column(String(255),nullable=False)


class Request(Base):
    __tablename__ = 'request'

    id_request = Column(Integer,primary_key=True)
    reques_date_weekend = Column(Date,nullable=False)
    description = Column(String(655),nullable=False)

    id_employee = Column(Integer, ForeignKey('employee.id_employee'))
    id_status = Column(Integer, ForeignKey('status.id_status'))


class Overtime(Base):
    __tablename__ = 'overtime'

    id_overtime = Column(Integer,primary_key=True)
    name_overtime = Column(String(555),nullable=False)
    date_overtime = Column(Date, nullable=False, default=date.today)
    overtime_hours = Column(Integer,nullable=False)

    id_employee = Column(Integer, ForeignKey('employee.id_employee'))


