from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.shared.config import get_settings
from src.shared.exceptions import LegajoNoEncontrado

# Importar routers de todos los módulos
from src.autenticacion.presentation.router import router as router_autenticacion
from src.inscripcion.presentation.router import router as router_inscripcion
from src.carga_academica.presentation.router import router as router_carga_academica
from src.seguimiento_graduacion.presentation.router import router as router_seguimiento
from src.analytics.presentation.router import router as router_analytics
from src.gestion_documental.presentation.router import router as router_documental

app = FastAPI(
    title="Sistema de Posgrado - Backend",
    description="API REST para la gestión académica de posgrado UTN FRLP",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",
)

# Configurar CORS: solo los orígenes definidos en CORS_ORIGINS (por defecto, Expo web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().lista_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de todos los módulos
app.include_router(
    router_autenticacion,
    prefix="/api/v1/auth",
    tags=["Autenticación"],
)
app.include_router(
    router_inscripcion,
    prefix="/api/v1/legajos",
    tags=["Legajos - Módulo Core"],
)
app.include_router(
    router_carga_academica,
    prefix="/api/v1/seminarios",
    tags=["Carga Académica - Módulo B"],
)
app.include_router(
    router_seguimiento,
    prefix="/api/v1/graduacion",
    tags=["Seguimiento de Graduación - Módulo C"],
)
app.include_router(
    router_analytics,
    prefix="/api/v1/analytics",
    tags=["Analytics - Módulo D"],
)
app.include_router(
    router_documental,
    prefix="/api/v1/documentos",
    tags=["Gestión Documental"],
)

@app.exception_handler(LegajoNoEncontrado)
async def manejar_legajo_no_encontrado(request: Request, exc: LegajoNoEncontrado):
    """Convierte la excepción de dominio en un 404 en lugar de un error 500."""
    return JSONResponse(status_code=404, content={"error": exc.message})

@app.on_event("startup")
async def startup_event():
    """Eventos que se ejecutan al iniciar la aplicación."""
    # Las tablas las crean las migraciones de Alembic (alembic upgrade head),
    # que docker-compose ejecuta antes de levantar la API.
    print("🚀 Sistema de Posgrado Backend iniciado")


@app.get("/", tags=["Root"])
async def read_root():
    """Endpoint raíz para verificación de salud."""
    return {
        "mensaje": "Sistema de Posgrado API",
        "version": "0.1.0",
        "estado": "operativo",
        "documentacion": "/api/docs",
    }

@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
