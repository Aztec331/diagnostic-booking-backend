from fastapi import FastAPI, Depends
from core.dependencies import get_current_user
from models.user import User
from routes.auth import router as auth_router
from routes.centres import router as centres_router
from routes.tests import router as tests_router


app = FastAPI(
    title="Diagnostic Booking API",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(centres_router)
app.include_router(tests_router)

@app.get("/")
def root():
    return {
        "message": "Diagnostic Booking API is running"
    }

@app.get("/api/auth/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }

