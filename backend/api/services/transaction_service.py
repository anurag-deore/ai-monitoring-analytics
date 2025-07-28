
import json
import asyncio
from fastapi import HTTPException
from ..models.schemas import ApiResponse, TransactionSummary, FailedTransactionRetryResponse, GrafanaWebhookRequest
from ..database.queries import execute_query
from ..ai.agents import failed_transaction_retry_agent
from ..chat.manager import transaction_details_from_db, insert_transaction_details_to_db
from ..config import AI_AGENT_TIMEOUT
from ..database.connection import get_chats_db_connection

async def with_timeout(coro, timeout_seconds: float, operation_name: str):
    """Wrapper to add timeout to any async operation."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, 
            detail=f"{operation_name} timed out. Please try a simpler query or check your connection."
        )

async def get_transaction_summary_service():
    sql_query = """
    WITH latest_events AS (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp::timestamptz DESC) as rn
        FROM transactions
    ),
    transaction_status AS (
        SELECT 
            transaction_id,
            event_type,
            CASE WHEN event_type = 'SettlementConfirmed' THEN 'SUCCESSFUL' ELSE 'FAILED' END as final_status
        FROM latest_events 
        WHERE rn = 1
    )
    SELECT 
        COUNT(*) as total_transactions,
        SUM(CASE WHEN final_status = 'SUCCESSFUL' THEN 1 ELSE 0 END) as successful_transactions,
        SUM(CASE WHEN final_status = 'FAILED' THEN 1 ELSE 0 END) as failed_transactions,
        ROUND(
            (SUM(CASE WHEN final_status = 'SUCCESSFUL' THEN 1 ELSE 0 END)::float / COUNT(*)) * 100, 2
        ) as success_rate
    FROM transaction_status;
    """
    
    result = await execute_query(sql_query)
    if result:
        data = result[0]
        summary = TransactionSummary(
            total_transactions=data['total_transactions'],
            successful_transactions=data['successful_transactions'],
            failed_transactions=data['failed_transactions'],
            success_rate=data['success_rate']
        )
        return summary
    return None

async def get_user_transactions_service(user_id: str, limit: int):
    sql_query = f"""
    WITH latest_events AS (
        SELECT *, 
               ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp::timestamptz DESC) as rn
        FROM transactions 
        WHERE user_id = '{user_id}'
    )
    SELECT 
        transaction_id,
        event_type,
        tx_status,
        fiat_amount,
        fiat_currency,
        crypto_amount,
        crypto_token,
        timestamp,
        CASE WHEN event_type = 'SettlementConfirmed' THEN 'SUCCESSFUL' ELSE 'FAILED' END as final_status
    FROM latest_events 
    WHERE rn = 1 
    ORDER BY timestamp::timestamptz DESC 
    LIMIT {limit};
    """
    
    return await execute_query(sql_query)

async def get_transaction_alerts_service():
    sql_query = f"""SELECT * FROM alerts ORDER BY timestamp::timestamptz desc;"""
    return await execute_query(sql_query)

async def update_alert_service(alert_id: str):
    conn = await get_chats_db_connection()
    sql_query = f"UPDATE alerts SET is_seen = true WHERE id ='{alert_id}'"
    await conn.execute(sql_query)
    await conn.close()

async def handle_grafana_webhook_service(request: GrafanaWebhookRequest):
    data = request.model_dump()
    
    if data.get('state') != 'alerting':
        return {"status": "ignored", "reason": f"State was '{data.get('state')}'"}

    transaction_id = data.get('message', {})
    
    if not transaction_id:
        raise HTTPException(status_code=400, detail="'transaction_id' tag not found in Grafana alert")

    transaction_details = await transaction_details_from_db(transaction_id)

    try:
        augmented_query = f"""
            User Query: Summary of the transaction
            Transaction Details: {json.dumps(transaction_details, indent=2)}
        """
        
        simple_result = await with_timeout(
            failed_transaction_retry_agent.run(augmented_query),
            AI_AGENT_TIMEOUT,
            "Failed transaction retry agent"    
        )
        simple_response = simple_result.data
    except HTTPException as e:
        if e.status_code == 408:
            simple_response = FailedTransactionRetryResponse(
                summary="I'm here to help with your payment and transaction questions. Could you please rephrase your question?",
                key_insights=["Response generation timed out"],
                recommendation="Please try asking your question again or be more specific."
            )
        else:
            raise

    await insert_transaction_details_to_db(transaction_id, simple_response.summary)
    
    return simple_response

async def get_failed_transaction_details_service(transaction_id: str):
    sql_query = f"""
    SELECT * FROM alerts WHERE transaction_id = '{transaction_id}';
    """
    return await execute_query(sql_query)
