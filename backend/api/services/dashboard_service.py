import json
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
from ..models.schemas import (
    CreateDashboardRequest, AddChartToDashboardRequest,
    DashboardResponse, DashboardChartsResponse, DashboardInfo, DashboardChart,
    ApiResponse
)
from ..database.queries import (
    create_dashboard_in_db, add_chart_to_dashboard_in_db,
    get_all_dashboards_from_db, get_dashboard_charts_from_db,
    dashboard_exists_in_db
)

async def create_dashboard_service(request: CreateDashboardRequest) -> DashboardResponse:
    """Service to create a new dashboard."""
    try:
        dashboard_id = str(uuid.uuid4())
        
        result = await create_dashboard_in_db(dashboard_id, request.title)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create dashboard")
        
        return DashboardResponse(
            success=True,
            dashboard_id=result['id'],
            title=result['title'],
            charts_count=result['charts_count'],
            created_at=result['created_at'].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating dashboard: {str(e)}")

async def add_chart_to_dashboard_service(request: AddChartToDashboardRequest) -> ApiResponse:
    """Service to add a chart to an existing dashboard."""
    try:
        # Check if dashboard exists
        if not await dashboard_exists_in_db(request.dashboard_id):
            raise HTTPException(status_code=404, detail=f"Dashboard {request.dashboard_id} not found")
        
        chart_id = str(uuid.uuid4())
        
        result = await add_chart_to_dashboard_in_db(
            chart_id, 
            request.dashboard_id, 
            request.chart_title, 
            request.chart_data
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to add chart to dashboard")
        
        return ApiResponse(
            success=True,
            message="Chart added to dashboard successfully",
            data={
                "chart_id": result['id'],
                "dashboard_id": result['dashboard_id'],
                "chart_title": result['chart_title'],
                "created_at": result['created_at'].isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding chart to dashboard: {str(e)}")

async def get_all_dashboards_service() -> ApiResponse:
    """Service to get all dashboards."""
    try:
        dashboards_data = await get_all_dashboards_from_db()
        
        dashboards = []
        for data in dashboards_data:
            dashboard = DashboardInfo(
                id=data['id'],
                title=data['title'],
                charts_count=data['charts_count'],
                created_at=data['created_at'].isoformat(),
                updated_at=data['updated_at'].isoformat()
            )
            dashboards.append(dashboard.dict())
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(dashboards)} dashboards",
            data={
                "dashboards": dashboards,
                "total_count": len(dashboards)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboards: {str(e)}")

async def get_dashboard_charts_service(dashboard_id: str) -> DashboardChartsResponse:
    """Service to get all charts for a specific dashboard."""
    try:
        # Check if dashboard exists
        if not await dashboard_exists_in_db(dashboard_id):
            raise HTTPException(status_code=404, detail=f"Dashboard {dashboard_id} not found")
        
        charts_data = await get_dashboard_charts_from_db(dashboard_id)
        
        charts = []
        for data in charts_data:
            # Ensure chart_data is a dict
            chart_data_raw = data['chart_data']
            chart_data: Dict[str, Any]
            
            if isinstance(chart_data_raw, str):
                try:
                    chart_data = json.loads(chart_data_raw)
                except json.JSONDecodeError:
                    # If parsing fails, wrap in dict
                    chart_data = {"raw_data": chart_data_raw}
            elif isinstance(chart_data_raw, dict):
                chart_data = chart_data_raw
            else:
                chart_data = {"data": chart_data_raw}
            
            chart = DashboardChart(
                chart_id=data['chart_id'],
                dashboard_id=data['dashboard_id'],
                chart_title=data['chart_title'],
                chart_data=chart_data,
                created_at=data['created_at'].isoformat()
            )
            charts.append(chart)
        
        return DashboardChartsResponse(
            success=True,
            dashboard_id=dashboard_id,
            charts=charts,
            total_charts=len(charts)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard charts: {str(e)}") 