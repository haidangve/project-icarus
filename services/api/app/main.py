from fastapi import FastAPI

from app.routers.health import router as health_router

app = FastAPI(
    title="Icarus API",
    description="Wildfire and environmental intelligence API.",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "name": "Icarus API",
        "status": "operational",
    }