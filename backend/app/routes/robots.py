from fastapi import APIRouter, HTTPException, status
from backend.app.database import get_database_connection

router = APIRouter()


@router.get("/robots")
def get_robots():
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            robot_id,
            robot_name,
            status,
            battery_level,
            current_location,
            current_task,
            last_updated
        FROM robots
        ORDER BY robot_id
    """)

    robots = cursor.fetchall()

    cursor.close()
    db.close()

    return robots


@router.get("/robots/{robot_id}")
def get_robot(robot_id: int):
    db = get_database_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            robot_id,
            robot_name,
            status,
            battery_level,
            current_location,
            current_task,
            last_updated
        FROM robots
        WHERE robot_id = %s
    """, (robot_id,))

    robot = cursor.fetchone()

    cursor.close()
    db.close()

    if robot is None:
        raise HTTPException(
            status_code=404,
            detail="Robot not found"
        )

    return robot


@router.post("/robots", status_code=status.HTTP_201_CREATED)
def create_robot(
    robot_name: str,
    status: str = "Idle",
    battery_level: int = 100,
    current_location: str | None = None,
    current_task: str | None = None
):
    if battery_level < 0 or battery_level > 100:
        raise HTTPException(
            status_code=400,
            detail="Battery level must be between 0 and 100"
        )

    db = get_database_connection()
    cursor = db.cursor()

    query = """
        INSERT INTO robots (
            robot_name,
            status,
            battery_level,
            current_location,
            current_task
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        robot_name,
        status,
        battery_level,
        current_location,
        current_task
    )

    try:
        cursor.execute(query, values)
        db.commit()

        robot_id = cursor.lastrowid

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:
        cursor.close()
        db.close()

    return {
        "message": "Robot created successfully",
        "robot_id": robot_id
    }