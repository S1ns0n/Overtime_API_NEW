from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base, Status, StatusKeys



engine = create_engine('sqlite:///todo_app.db', echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)



STATUSES = [
    {
        "key": StatusKeys.ACTIVE,
        "name": "Активен",
    },
    {
        "key": StatusKeys.INACTIVE,
        "name": "Неактивен",
    },
    {
        "key": StatusKeys.PENDING,
        "name": "В ожидании",
    },
    {
        "key": StatusKeys.APPROVED,
        "name": "Подтверждён",
    },
    {
        "key": StatusKeys.REJECTED,
        "name": "Отклонён",
    },
]


def init_statuses():
    db = SessionLocal()

    try:
        existing = db.query(Status).count()

        if existing == 0:
            print("📝 Создаю статусы...")
            for status_data in STATUSES:
                status = Status(
                    name_status=status_data["name"]
                )
                db.add(status)

            db.commit()
            print(f"✅ Создано {len(STATUSES)} статусов")
        else:
            print(f"📋 Статусы уже существуют ({existing} шт.)")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании статусов: {e}")
    finally:
        db.close()


def get_status_by_key(db, key: str):
    status_map = {s["key"]: s["name"] for s in STATUSES}
    name = status_map.get(key)

    if name:
        return db.query(Status).filter(Status.name_status == name).first()
    return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()