from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import bcrypt
from jose import jwt
from datetime import datetime, timedelta

from backend.app.database import get_database_connection


router = APIRouter()


# JWT configuration
SECRET_KEY = "warehouse-digital-twin-secret-key-change-this"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "Viewer"


@router.post("/register")
def register_user(user: RegisterRequest):

    if user.role not in ["Admin", "Manager", "Viewer"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    # Hash password using bcrypt
    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    db = get_database_connection()
    cursor = db.cursor()

    query = """
        INSERT INTO users
        (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """

    try:
        cursor.execute(
            query,
            (
                user.username,
                user.email,
                password_hash,
                user.role
            )
        )

        db.commit()

        user_id = cursor.lastrowid

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    finally:
        cursor.close()
        db.close()

    return {
        "message": "User registered successfully",
        "user_id": user_id
    }


@router.post("/login")
def login_user(credentials: LoginRequest):

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            user_id,
            username,
            email,
            password_hash,
            role
        FROM users
        WHERE email = %s
        """,
        (credentials.email,)
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    password_valid = bcrypt.checkpw(
        credentials.password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create JWT token
    expire = datetime.utcnow() + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    token_data = {
        "sub": str(user["user_id"]),
        "username": user["username"],
        "role": user["role"],
        "exp": expire
    }

    access_token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }