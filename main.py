from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Importar o router do login mágico
from app.api.endpoints.auth_credentials import router as auth_cred_routes

from app.routes.baby_routes import router as baby_routes
from app.routes.event_routes import router as event_routes
from app.routes.plan_routes import router as plan_routes
from app.routes.report_routes import router as report_routes
from app.routes.payment.payment import router as payment_routes

from app.routes.admin import router as admin_routes


# Cria a instância do FastAPI
app = FastAPI(
    title="NanaFácil API",
    version="0.1.0",
    description="Backend para coach de sono de bebês",
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # React local
        "https://nanafacil-web.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria o roteador principal com prefixo /api
routerAPI = APIRouter(prefix="/api")

# Adiciona as rotas do login mágico
routerAPI.include_router(auth_cred_routes)
routerAPI.include_router(baby_routes)
routerAPI.include_router(event_routes)
routerAPI.include_router(plan_routes)
routerAPI.include_router(report_routes)
routerAPI.include_router(payment_routes)
routerAPI.include_router(admin_routes)
# Anexa o roteador à aplicação principal
app.include_router(routerAPI)



@app.get("/", tags=["Root"])
async def read_root():
    return {"status": "NanaFácil API está no ar!"}