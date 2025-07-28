
from fastapi import APIRouter, Query
from ..models.schemas import QueryRequest, ChatQueryRequest, ChatResponse, ApiResponse
from ..services.chat_service import handle_chat_query_service
from ..chat.manager import get_all_chats_from_db, load_chat_history_from_db, delete_chat_from_db, chat_exists_in_db, save_chat_query, delete_chat_from_memory
from datetime import datetime

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def handle_chat_query(request: ChatQueryRequest):
    return await handle_chat_query_service(request)

@router.post("/query-simple", response_model=ChatResponse)
async def handle_simple_query(request: QueryRequest):
    chat_request = ChatQueryRequest(
        query=request.query,
        chat_type="new",
        chat_id=None
    )
    return await handle_chat_query_service(chat_request)

@router.get("/chats", response_model=ApiResponse)
async def get_all_chats():
    """Get all chat records from database as raw JSON objects."""
    try:
        raw_chats_data = await get_all_chats_from_db()
        
        chat_records = []
        for record in raw_chats_data:
            chat_records.append({
                "id": record['id'],
                "chat_id": record['chat_id'],
                "query": record['query'],
                "timestamp": record['timestamp'].isoformat() if record['timestamp'] else None,
            })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(chat_records)} chat records",
            data={"chats": chat_records, "count": len(chat_records)}
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to get chat records",
            error=str(e)
        )

@router.get("/chats/{chat_id}/history", response_model=ApiResponse)
async def get_chat_history_endpoint(chat_id: str):
    """Get message history for a specific chat from database."""
    try:
        db_history = await load_chat_history_from_db(chat_id)
        
        if not db_history:
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        first_msg = db_history[0] if db_history else None
        last_msg = db_history[-1] if db_history else None
        
        history = {
            "chat_id": chat_id,
            "messages": db_history,
            "created_at": first_msg['timestamp'].isoformat() if first_msg else datetime.now().isoformat(),
            "updated_at": last_msg['timestamp'].isoformat() if last_msg else datetime.now().isoformat()
        }
        
        return ApiResponse(
            success=True,
            message=f"Retrieved history for chat {chat_id}",
            data=history
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get chat history for {chat_id}",
            error=str(e)
        )

@router.delete("/chats/{chat_id}", response_model=ApiResponse)
async def delete_chat(chat_id: str):
    """Delete a specific chat conversation from database."""
    try:
        if not await chat_exists_in_db(chat_id):
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        success = await delete_chat_from_db(chat_id)
        
        if success:
            delete_chat_from_memory(chat_id)
            
            return ApiResponse(
                success=True,
                message=f"Chat {chat_id} deleted successfully",
                data={"deleted_chat_id": chat_id}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"Failed to delete chat {chat_id}",
                error="Database deletion failed"
            )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to delete chat {chat_id}",
            error=str(e)
        )

@router.put("/chats/{chat_id}/title", response_model=ApiResponse)
async def update_chat_title(chat_id: str, title: str = Query(..., description="New title for the chat")):
    """Update the title of a chat conversation."""
    try:
        if not await chat_exists_in_db(chat_id):
            return ApiResponse(
                success=False,
                message=f"Chat {chat_id} not found",
                error="Chat not found"
            )
        
        await save_chat_query(chat_id, f"[TITLE_UPDATE]: {title}", "title_update")
        
        return ApiResponse(
            success=True,
            message=f"Chat title updated successfully",
            data={
                "chat_id": chat_id,
                "new_title": title,
                "updated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to update chat title for {chat_id}",
            error=str(e)
        )
