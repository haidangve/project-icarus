from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.alerts import router as alerts_router
from app.routers.fires import router as fires_router
from app.routers.health import router as health_router


app = FastAPI(
    title="Icarus API",
    description=(
        "Wildfire and environmental situational-awareness API."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(fires_router)
app.include_router(alerts_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": "Icarus API",
        "status": "operational",
        "documentation": "/docs",
    }