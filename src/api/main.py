from fastapi import FastAPI

app = FastAPI(
    title="CogniStream API",
    description="Backend API for Developer Flow-State and Cognitive Load Analytics",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CogniStream API",
        "message": "API is running successfully",
    }
