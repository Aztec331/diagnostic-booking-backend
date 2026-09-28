from sqlalchemy.orm import Session

from models.centre import DiagnosticCentre
from models.centre_test import CentreTest
from models.test import DiagnosticTest

def create_centre(
    db: Session,
    name: str,
    location: str,
):
    centre = DiagnosticCentre(
        name=name,
        location=location,
    )

    db.add(centre)
    db.commit()
    db.refresh(centre)

    return centre

def add_test_to_centre(
    db: Session,
    centre_id: int,
    test_id: int,
    price: float,
):
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == centre_id
    ).first()

    if not centre:
        return None, "centre_not_found"

    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.id == test_id
    ).first()

    if not test:
        return None, "test_not_found"

    existing = db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id,
        CentreTest.test_id == test_id,
    ).first()

    if existing:
        return None, "test_already_added"

    centre_test = CentreTest(
        centre_id=centre_id,
        test_id=test_id,
        price=price,
    )

    db.add(centre_test)
    db.commit()
    db.refresh(centre_test)

    return centre_test, None

def get_all_centres(db: Session):
    return db.query(DiagnosticCentre).all()

def get_tests_for_centre(db: Session, centre_id: int):
    return db.query(CentreTest).filter(
        CentreTest.centre_id == centre_id
    ).all()