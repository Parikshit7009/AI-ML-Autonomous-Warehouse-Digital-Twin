from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from backend.app.database import get_database_connection


SECRET_KEY = "warehouse-digital-twin-secret-key-change-this"
ALGORITHM = "HS256"

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT user_id, username, email, role
        FROM users
        WHERE user_id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user