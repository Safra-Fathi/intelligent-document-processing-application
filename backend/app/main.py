from fastapi import FastAPI

from app.api.routes.auth import router as auth_router


app = FastAPI(
    title="Intelligent Document Processing API",
    version="0.1.0",
)

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "intelligent-document-processing-api",
    }