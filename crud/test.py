from sqlalchemy.orm import Session

from models.test import DiagnosticTest


def create_test(db: Session, name: str):
    test = DiagnosticTest(
        name=name,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

def get_all_tests(db: Session):
    return db.query(DiagnosticTest).all()