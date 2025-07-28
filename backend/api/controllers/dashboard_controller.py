from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    CreateDashboardRequest, AddChartToDashboardRequest,
    DashboardResponse, DashboardChartsResponse, ApiResponse
)
from ..services.dashboard_service import (
    create_dashboard_service, add_chart_to_dashboard_service,
    get_all_dashboards_service, get_dashboard_charts_service
)

router = APIRouter()

@router.post("/create", response_model=DashboardResponse)
async def create_dashboard(request: CreateDashboardRequest):
    """Create a new dashboard."""
    return await create_dashboard_service(request)

@router.post("/add-chart", response_model=ApiResponse)
async def add_chart_to_dashboard(request: AddChartToDashboardRequest):
    """Add a chart to an existing dashboard."""
    return await add_chart_to_dashboard_service(request)

@router.get("/", response_model=ApiResponse)
async def get_all_dashboards():
    """Get all dashboards."""
    return await get_all_dashboards_service()

@router.get("/{dashboard_id}/charts", response_model=DashboardChartsResponse)
async def get_dashboard_charts(dashboard_id: str):
    """Get all charts for a specific dashboard."""
    return await get_dashboard_charts_service(dashboard_id) 