
from fastapi import APIRouter, Query
from ..models.schemas import ApiResponse, GrafanaWebhookRequest
from ..services.transaction_service import (
    get_transaction_summary_service,
    get_user_transactions_service,
    get_transaction_alerts_service,
    update_alert_service,
    handle_grafana_webhook_service,
    get_failed_transaction_details_service
)

router = APIRouter()

@router.get("/summary", response_model=ApiResponse)
async def get_transaction_summary():
    try:
        summary = await get_transaction_summary_service()
        if summary:
            return ApiResponse(
                success=True,
                message="Transaction summary retrieved",
                data=summary.dict()
            )
        else:
            return ApiResponse(
                success=False,
                message="No transaction data found",
                data=None
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get transaction summary",
            error=str(e)
        )

@router.get("/users/{user_id}/transactions", response_model=ApiResponse)
async def get_user_transactions(user_id: str, limit: int = Query(10, ge=1, le=100)):
    try:
        data = await get_user_transactions_service(user_id, limit)
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(data)} transactions for user {user_id}",
            data={
                "user_id": user_id,
                "transactions": data,
                "count": len(data)
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get transactions for user {user_id}",
            error=str(e)
        )

@router.get("/alerts", response_model=ApiResponse)
async def get_transaction_events():
    try:
        data = await get_transaction_alerts_service()
        return ApiResponse(
            success=True,
            message="Alerts retrieved", 
            data=data
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get alerts",
            error=str(e)
        ) 

@router.post("/alerts/{alert_id}", response_model=ApiResponse)
async def update_alert(alert_id: str):
    try:
        await update_alert_service(alert_id)
        return ApiResponse(success=True, message="Alert updated")
    except Exception as e:
        return ApiResponse(success=False, message="Failed to update alert", error=str(e))

@router.post('/webhook', response_model=ApiResponse)
async def grafana_webhook(request: GrafanaWebhookRequest):
    try:
        result = await handle_grafana_webhook_service(request)
        return ApiResponse(
            success=True,
            message="Alert processed and analyzed.",
            data=result.model_dump()
        )
    except Exception as e:
        return ApiResponse(success=False, message="Internal server error", error=str(e))

@router.get("/failed-transactions/{transaction_id}", response_model=ApiResponse)
async def get_failed_transaction_details(transaction_id: str):
    try:
        data = await get_failed_transaction_details_service(transaction_id)
        return ApiResponse(
            success=True,
            message=f"Retrieved details for failed transaction {transaction_id}",
            data=data
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get details for failed transaction {transaction_id}",
            error=str(e)
        )
