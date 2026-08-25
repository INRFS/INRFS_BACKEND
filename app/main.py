from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth_routes import router as auth_router
from app.routes.master_routes import router as master_router
from app.routes.investment_routes import router as investment_router
from app.routes.investor_profile_routes import router as investor_profile_router
from app.routes.investor_dashboard_routes import router as investor_dashboard_router

from app.routes.admin.investor_management_route import (
    router as admin_investor_router,
)
from app.routes.admin.investment_management_route import (
    router as admin_investment_router,
)
from app.routes.admin.admin_profile_route import (
    router as admin_profile_router,
)
from app.routes.admin.admin_dashboard_route import (
    router as admin_dashboard_router,
)
from app.routes.admin.report_route import (
    router as admin_report_router,
)
from app.routes.admin.admin_tenure_timeout import (
    router as admin_tenure_timeout_router,
)

from app.routes.superadmin.investment_management_route import (
    router as superadmin_investment_management_router,
)

from app.routes.superadmin.superadmin_dashboard_route import router as superadmin_dashboard_router
from app.routes.superadmin.investor_management_route import router as superadmin_investor_management_router
from app.routes.superadmin.branch_management_route import router as superadmin_branch_management_router
from app.routes.superadmin.admin_management_route import router as admin_management_router
from app.routes.superadmin.profile_route import router as superadmin_profile_router
from app.routes.superadmin.payment_route import router as superadmin_payment_router
from app.routes.superadmin.superadmin_reports_route import router as superadmin_reports_router
from app.routes.landing_route import router as landing_router


app = FastAPI(
    title="INRFS API",
    description="INRFS Investment Platform API",
    version="1.0.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://187.52.115.32",
        "https://app.inrfs.com",
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
app.include_router(admin_tenure_timeout_router)



app.include_router(superadmin_dashboard_router)
app.include_router(superadmin_investor_management_router)
app.include_router(superadmin_investment_management_router)
app.include_router(superadmin_branch_management_router)
app.include_router(admin_management_router)
app.include_router(superadmin_profile_router)
app.include_router(superadmin_payment_router)
app.include_router(superadmin_reports_router)
app.include_router(landing_router)




@app.get("/")
def root():
    return {
        "success": True,
        "message": "INRFS API is running",
    }