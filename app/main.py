from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_routes import router as auth_router
from app.routes.master_routes import router as master_router
from app.routes.investment_routes import router as investment_router
from app.routes.investor_profile_routes import router as investor_profile_router
from app.routes.investor_dashboard_routes import router as investor_dashboard_router

from app.routes.admin.investor_management_route import (router as admin_investor_router,)
from app.routes.admin.investment_management_route import (
    router as admin_investment_router,
)
from app.routes.admin.admin_profile_route import (
    router as admin_profile_router,
)
from app.routes.admin.admin_dashboard_route import router as admin_dashboard_router
from app.routes.admin.report_route import (
    router as admin_report_router,
)

from app.routes.investment_bond_route import router as report_router


app = FastAPI(
    title="INRFS API",
    description="INRFS Investment Platform API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://187.52.115.32",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(master_router)
app.include_router(investment_router)
app.include_router(investor_profile_router)
app.include_router(investor_dashboard_router)

app.include_router(admin_investor_router)
app.include_router(admin_investment_router)
app.include_router(admin_profile_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_report_router)
@app.get("/")
def root():
    return {
        "success": True,
        "message": "INRFS API is running",
    }