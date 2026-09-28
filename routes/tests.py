from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from crud.test import create_test, get_all_tests
from database import get_db
from schemas.test import TestCreate
from core.dependencies import get_current_user
from models.user import User


router = APIRouter(
    prefix="/api/tests",
    tags=["Tests"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_diagnostic_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = create_test(
        db=db,
        name=test_data.name,
    )

    return {
        "id": test.id,
        "name": test.name,
    }

@router.get("/")
def get_tests(
    db: Session = Depends(get_db),
):
    tests = get_all_tests(db)

    response = []

    for test in tests:
        response.append({
            "id": test.id,
            "name": test.name,
        })

    return response