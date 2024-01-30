# main.py

from fastapi import FastAPI, Body, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.models.users import User
from app.config.database import get_db
from app.auth.auth import signJWT, verify_password
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.dto.users_schemas import ResponseData, UserLoginSchema
from app.models.users import Base as user_base
from app.models.tasks import Base as task_base
from app.config.database import engine
from app.modules.users.user_routers import router as user_router
from app.modules.tasks.task_routers import router as task_router
# from app.modules.authentication.auth_routers import router as auth_router
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Application description
description = """
FastAPI Task Management: A robust API for efficient task tracking and management, featuring user authentication, predefined(SUPERADMIN, MANAGER, AGENT) role-based access control that gives seamless integration with modern front-end technologies.
"""

# Async context manager for database setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    user_base.metadata.create_all(bind=engine)
    task_base.metadata.create_all(bind=engine)
    yield

# Create FastAPI app instance
app = FastAPI(
    title='Task Management System API',
    lifespan=lifespan,
    description=description,
    version="1.0.0",
    
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware, 
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)

# Mount the static directory for serving uploaded files
app.mount("/static", StaticFiles(directory="static"), name="static")



def check_user(data: UserLoginSchema, db: Session):
    """
    Helper function to check user credentials during login.

    Parameters:
    - data (UserLoginSchema): The login data containing email and password.
    - db (Session): The SQLAlchemy database session.

    Returns:
    - User: The user if credentials are valid, else None.
    """
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user and verify_password(data.password, db_user.password):
        return db_user
    return None



@app.post("/user/login", response_model=ResponseData, tags=["Authentication"])
async def user_login(user: UserLoginSchema = Body(...), db: Session = Depends(get_db)):
    """
    Endpoint to handle user login.

    Parameters:
    - user (UserLoginSchema): The login data containing email and password.
    - db (Session): The SQLAlchemy database session.

    Returns:
    - ResponseData: Status, message, user data, and JWT token if login is successful, otherwise an error message.
    """
    db_user = check_user(user, db)
    if db_user:
        user_data = {
            "ID": db_user.ID,
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role,
            "created_at": db_user.created_at,
            "token": signJWT(db_user.email),
        }
        return ResponseData(
            status=True,
            message="Logged in successfully",
            data=user_data,
        )
    else:
        return ResponseData(
            status=False,
            message="User not found",
            data={},
        )

# Root path endpoint
@app.get("/", tags=["General"])
def read_root():
    return {"message": "This is the root path"}

# Include routers
app.include_router(user_router)
app.include_router(task_router)
# app.include_router(auth_router)

# Run the application using uvicorn
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return ResponseData(
#             status=False,
#             message="Not enough permissions to access this resource",
#             data={}
#         )

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return ResponseData(
#             status=False,
#             message="Not enough permissions to access this resource",
#             data={}
#         )