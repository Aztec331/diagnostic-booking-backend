from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.centre import (
    create_centre,
    add_test_to_centre,
    get_all_centres,
    get_tests_for_centre,
)
from database import get_db
from schemas.centre import CentreCreate, CentreTestCreate
from core.dependencies import get_current_user
from models.user import User

router = APIRouter(
    prefix="/api/centres",
    tags=["Centres"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_diagnostic_centre(
    centre_data: CentreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre = create_centre(
        db=db,
        name=centre_data.name,
        location=centre_data.location,
    )

    return {
        "id": centre.id,
        "name": centre.name,
        "location": centre.location,
    }

@router.get("/")
def get_centres(
    db: Session = Depends(get_db),
):
    centres = get_all_centres(db)

    response = []

    for centre in centres:
        response.append({
            "id": centre.id,
            "name": centre.name,
            "location": centre.location,
        })

    return response

@router.post("/{centre_id}/tests/", status_code=status.HTTP_201_CREATED)
def add_test(
    centre_id: int,
    test_data: CentreTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre_test, error = add_test_to_centre(
        db=db,
        centre_id=centre_id,
        test_id=test_data.test_id,
        price=test_data.price,
    )

    if error == "centre_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    if error == "test_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    if error == "test_already_added":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Test is already offered by this centre",
        )

    return {
        "id": centre_test.id,
        "centre_id": centre_test.centre_id,
        "test_id": centre_test.test_id,
        "price": centre_test.price,
    }

@router.get("/{centre_id}/tests/")
def get_centre_tests(
    centre_id: int,
    db: Session = Depends(get_db),
):
    centre_tests = get_tests_for_centre(
        db=db,
        centre_id=centre_id,
    )

    response = []

    for centre_test in centre_tests:
        response.append({
            "test_id": centre_test.test_id,
            "price": centre_test.price,
        })

    return response