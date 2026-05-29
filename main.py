from api.database import Base
from api.session import engine, init_statuses
from fastapi import FastAPI
import uvicorn
from api.endpoints import employee_endpoints
from api.endpoints import role_endpoints
from api.endpoints import status_endpoints
from api.endpoints import space_endpoints
from api.endpoints import weekend_endpoints
from api.endpoints import request_endpoints
from api.endpoints import overtime_endpoints

app = FastAPI(title="Employee API", version="1.0.0")

app.include_router(employee_endpoints.router)
app.include_router(role_endpoints.router)
app.include_router(status_endpoints.router)
app.include_router(space_endpoints.router)
app.include_router(weekend_endpoints.router)
app.include_router(request_endpoints.router)
app.include_router(overtime_endpoints.router)


@app.get("/")
def read_root():
    return {"message": "Employee Management API"}
def init_database():
    Base.metadata.create_all(engine)
    print("✅ База данных и таблицы созданы!")

if __name__ == "__main__":
    init_database()
    init_statuses()
    uvicorn.run(app,host="0.0.0.0", port=8000)



