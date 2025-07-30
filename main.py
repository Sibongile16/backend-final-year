from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.routes import (auth, teacher, students, 
                        classes, users, ml_model, dashboard, schedulers, academics,
                        grades, new_classes, subjects,
                        guardians, attendance
                        
)

                        
from app.middleware import add_cors_middleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with schedulers.lifespan(app):
        yield
        
app = FastAPI(title="School Management System", 
              description="A system for managing a school", 
              version="1.0.0",
              lifespan=lifespan)
add_cors_middleware(app)



@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to the API documentation
    """
    return RedirectResponse(url="/docs")

app.include_router(attendance.router)
app.include_router(guardians.router)
app.include_router(subjects.router)
app.include_router(schedulers.router)
app.include_router(new_classes.router)
app.include_router(grades.router)
app.include_router(academics.router)
app.include_router(dashboard.router)
app.include_router(ml_model.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teacher.router)
app.include_router(students.router)
app.include_router(classes.router)


