import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.config.settings import get_settings
from app.routes.ai_routes import router as ai_router
from app.routes.health_routes import router as health_router

logging.basicConfig( 
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("intellilink")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing IntelliLink AI Intelligence Layer...")
    yield
    logger.info("Shutting down IntelliLink AI Engine...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="IntelliLink AI - Infrastructure Document Intelligence & Human Review Proposal System (SIH 2026)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ai_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def serve_demo():
    demo_file = STATIC_DIR / "demo.html"
    if demo_file.exists():
        with open(demo_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>IntelliLink AI Engine Active</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.DEBUG)