import asyncio
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from .connection import get_transactions_db_connection
from ..config import MAX_QUERY_RESULTS, DATABASE_TIMEOUT

async def with_timeout(coro, timeout_seconds: float, operation_name: str):
    """Wrapper to add timeout to any async operation."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, 
            detail=f"{operation_name} timed out. Please try a simpler query or check your connection."
        )

def validate_and_fix_query(sql_query: str) -> str:
    """Validate and attempt to fix common query issues."""
    fixed_query = sql_query
    
    # Fix references to computed columns that don't exist in the table
    common_fixes = [
        # final_status column references
        (r'SELECT\s+([^,]*,\s*)?final_status\b', r'SELECT \1CASE WHEN event_type = \'SettlementConfirmed\' THEN \'SUCCESSFUL\' ELSE \'FAILED\' END as final_status'),
        (r'WHERE\s+final_status\s*=\s*[\'"](\w+)[\'"]', r'WHERE (CASE WHEN event_type = \'SettlementConfirmed\' THEN \'SUCCESSFUL\' ELSE \'FAILED\' END) = \'\1\''),
        (r'ORDER BY\s+final_status\b', r'ORDER BY (CASE WHEN event_type = \'SettlementConfirmed\' THEN \'SUCCESSFUL\' ELSE \'FAILED\' END)'),
        
        # Fix success_rate references
        (r'WHERE\s+success_rate\s*[><=]', r'WHERE (SELECT success_rate FROM transaction_summary)'),
        
        # Fix common count references in WHERE clauses
        (r'WHERE\s+count\s*[><=]', r'WHERE transaction_count'),
        
        # Fix references to non-existent transaction_summary table
        (r'FROM\s+transaction_summary\b', r'FROM (WITH latest_events AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp::timestamptz DESC) as rn FROM transactions) SELECT COUNT(*) as total_transactions FROM latest_events WHERE rn = 1) as transaction_summary'),
    ]
    
    for pattern, replacement in common_fixes:
        fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
    
    # Ensure all timestamp references are properly cast
    timestamp_fixes = [
        (r'\btimestamp\s*([><=]+)\s*([^:]+?)(?=\s|$|;|\))', r'timestamp::timestamptz \1 \2'),
        (r'ORDER BY\s+timestamp\b(?!::)', r'ORDER BY timestamp::timestamptz'),
        (r'GROUP BY\s+timestamp\b(?!::)', r'GROUP BY timestamp::timestamptz'),
    ]
    
    for pattern, replacement in timestamp_fixes:
        fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
    
    return fixed_query

async def execute_query(sql_query: str) -> List[Dict[str, Any]]:
    """Execute SQL query with timeout and result limiting."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        # Add LIMIT to prevent memory issues if not already present
        limited_query = sql_query
        if "LIMIT" not in sql_query.upper() and "COUNT" not in sql_query.upper():
            limited_query = f"{sql_query.rstrip(';')} LIMIT {MAX_QUERY_RESULTS};"
        
        # Execute with timeout
        rows = await with_timeout(
            conn.fetch(limited_query),
            DATABASE_TIMEOUT,
            "Database query execution"
        )
        
        result = [dict(row) for row in rows]
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, 
            detail="Database query timed out. Please try a simpler query."
        )
    except Exception as e:
        error_msg = str(e)
        
        # Check for common computed column errors and provide helpful message
        if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
            if any(computed_col in error_msg.lower() for computed_col in ['final_status', 'success_rate', 'count']):
                raise HTTPException(
                    status_code=400, 
                    detail="Query references a computed column from previous conversation. Please rephrase your question - I'll generate a fresh query with proper column references."
                )
        
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")
    finally:
        # Close the connection properly
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

async def test_transactions_db_connection():
    """Test transactions database connectivity."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        await conn.fetchval("SELECT 1")
        return "connected"
    except Exception as e:
        return f"error: {str(e)[:50]}"
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass 


# --- Dashboard Database Operations ---

async def create_dashboard_in_db(dashboard_id: str, title: str) -> Optional[Dict[str, Any]]:
    """Create a new dashboard in the database."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        query = """
            INSERT INTO dashboards (id, title, charts_count, created_at, updated_at)
            VALUES ($1, $2, 0, NOW(), NOW())
            RETURNING id, title, charts_count, created_at, updated_at
        """
        
        result = await with_timeout(
            conn.fetchrow(query, dashboard_id, title),
            DATABASE_TIMEOUT,
            "Create dashboard"
        )
        
        return dict(result) if result else None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

async def add_chart_to_dashboard_in_db(chart_id: str, dashboard_id: str, chart_title: str, chart_data: Any) -> Optional[Dict[str, Any]]:
    """Add a chart to a dashboard in the database."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        # Start transaction
        async with conn.transaction():
            # Insert chart
            insert_chart_query = """
                INSERT INTO dashboard_charts (id, dashboard_id, chart_title, chart_data, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING id, dashboard_id, chart_title, chart_data, created_at
            """
            
            chart_result = await with_timeout(
                conn.fetchrow(insert_chart_query, chart_id, dashboard_id, chart_title, chart_data),
                DATABASE_TIMEOUT,
                "Insert chart"
            )
            
            # Update dashboard charts count
            update_dashboard_query = """
                UPDATE dashboards 
                SET charts_count = charts_count + 1, updated_at = NOW()
                WHERE id = $1
            """
            
            await with_timeout(
                conn.execute(update_dashboard_query, dashboard_id),
                DATABASE_TIMEOUT,
                "Update dashboard count"
            )
            
            return dict(chart_result) if chart_result else None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add chart to dashboard: {str(e)}")
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

async def get_all_dashboards_from_db() -> List[Dict[str, Any]]:
    """Get all dashboards from the database."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        query = """
            SELECT id, title, charts_count, created_at, updated_at
            FROM dashboards
            ORDER BY updated_at DESC
        """
        
        rows = await with_timeout(
            conn.fetch(query),
            DATABASE_TIMEOUT,
            "Get all dashboards"
        )
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboards: {str(e)}")
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

async def get_dashboard_charts_from_db(dashboard_id: str) -> List[Dict[str, Any]]:
    """Get all charts for a specific dashboard from the database."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        query = """
            SELECT id as chart_id, dashboard_id, chart_title, chart_data, created_at
            FROM dashboard_charts
            WHERE dashboard_id = $1
            ORDER BY created_at ASC
        """
        
        rows = await with_timeout(
            conn.fetch(query, dashboard_id),
            DATABASE_TIMEOUT,
            "Get dashboard charts"
        )
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard charts: {str(e)}")
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass

async def dashboard_exists_in_db(dashboard_id: str) -> bool:
    """Check if a dashboard exists in the database."""
    conn = None
    try:
        conn = await get_transactions_db_connection()
        
        query = "SELECT 1 FROM dashboards WHERE id = $1"
        
        result = await with_timeout(
            conn.fetchval(query, dashboard_id),
            DATABASE_TIMEOUT,
            "Check dashboard exists"
        )
        
        return result is not None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check dashboard existence: {str(e)}")
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:
                pass