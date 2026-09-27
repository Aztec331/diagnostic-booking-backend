from fastapi import FastAPI

app = FastAPI(
    title="Diagnostic Booking API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Diagnostic Booking API is running"}