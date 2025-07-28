
import json
from datetime import datetime
from fastapi import HTTPException
from ..models.schemas import (
    ChatQueryRequest, ChatResponse, QueryResponse,
    ApiResponse, ChatHistory, SQLGenerationResponse, DataSummaryResponse
)
from ..ai.agents import sql_agent, summary_agent, response_summary_agent, query_type_agent, bar_chart_agent
from ..database.queries import execute_query, validate_and_fix_query, with_timeout
from ..chat.manager import (
    create_new_chat, update_chat_history, load_chat_messages_from_db,
    get_all_chats_from_db, load_chat_history_from_db, delete_chat_from_db,
    chat_exists_in_db, delete_chat_from_memory, save_chat_query
)
from ..config import TRANSACTION_COLUMNS, AI_AGENT_TIMEOUT

async def handle_chat_query_service(request: ChatQueryRequest):
    start_time = datetime.now()
    
    try:
        if request.chat_type == "new":
            chat_id = create_new_chat()
            message_history = []
        else:
            if not request.chat_id:
                raise HTTPException(status_code=400, detail="chat_id is required when chat_type is 'existing'")
            
            chat_id = request.chat_id
            
            from ..chat.manager import chat_message_cache
            chat_exists = await chat_exists_in_db(chat_id) or chat_id in chat_message_cache
            if not chat_exists:
                raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
            
            message_history = await load_chat_messages_from_db(chat_id)
        
        try:
            query_type_result = await with_timeout(
                query_type_agent.run(request.query, message_history=message_history if message_history else []),
                AI_AGENT_TIMEOUT,
                "Query type classification"
            )
            query_type = query_type_result.data.query_type
        except HTTPException as e:
            if e.status_code == 408:
                query_type = "sql"
            else:
                raise
        except Exception:
            query_type = "sql"
        
        if query_type == "simple":
            return await handle_simple_llm_query_service(request, chat_id, message_history, start_time)
        
        augmented_query = f"""
        User Query: {request.query}
        Available Dataset Columns: {json.dumps(TRANSACTION_COLUMNS, indent=2)}
        Please generate a PostgreSQL query to answer this question.
        """
        
        try:
            if message_history:
                sql_result = await with_timeout(
                    sql_agent.run(augmented_query, message_history=message_history),
                    AI_AGENT_TIMEOUT,
                    "SQL generation"
                )
            else:
                sql_result = await with_timeout(
                    sql_agent.run(augmented_query),
                    AI_AGENT_TIMEOUT,
                    "SQL generation"
                )
        except HTTPException as e:
            if e.status_code == 408:
                raise HTTPException(
                    status_code=408,
                    detail="AI query generation timed out. Please try a simpler question."
                )
            raise
        
        sql_response: SQLGenerationResponse = sql_result.data
        
        validated_query = validate_and_fix_query(sql_response.sql_query)
        if validated_query != sql_response.sql_query:
            sql_response.sql_query = validated_query
        
        try:
            data = await execute_query(sql_response.sql_query)
        except HTTPException as e:
            if e.status_code == 400 and "computed column" in e.detail:
                fresh_sql_result = await with_timeout(
                    sql_agent.run(augmented_query),
                    AI_AGENT_TIMEOUT,
                    "Fresh SQL generation"
                )
                fresh_sql_response: SQLGenerationResponse = fresh_sql_result.data
                fresh_validated_query = validate_and_fix_query(fresh_sql_response.sql_query)
                
                data = await execute_query(fresh_validated_query)
                sql_response.sql_query = fresh_validated_query
            else:
                raise
        
        try:
            if data:
                summary_data = data[:50] if len(data) > 50 else data
                data_context = f"""
                Original Query: {request.query}
                Retrieved Data ({len(data)} rows, showing first {len(summary_data)}):
                {json.dumps(summary_data, indent=2, default=str)}
                {"... (additional rows truncated for analysis)" if len(data) > 50 else ""}
                Total rows: {len(data)}
                """
                
                summary_result = await with_timeout(
                    summary_agent.run(data_context, message_history=sql_result.all_messages()),
                    AI_AGENT_TIMEOUT,
                    "AI summary generation"
                )
                summary_response: DataSummaryResponse = summary_result.data
                
                # Check if data can be visualized as bar chart
                try:
                    bar_chart_context = f"""
                    User Query: {request.query}
                    SQL Query: {sql_response.sql_query}
                    """
                    
                    bar_chart_result = await with_timeout(
                        bar_chart_agent.run(bar_chart_context),
                        AI_AGENT_TIMEOUT,
                        "Bar chart analysis"
                    )
                    bar_chart_response = bar_chart_result.data
                    print(f"Bar chart analysis: {bar_chart_response}")
                    
                    # Convert to dict to allow adding chart_data
                    if bar_chart_response:
                        if hasattr(bar_chart_response, 'dict'):
                            bar_chart_response = bar_chart_response.dict()
                        elif hasattr(bar_chart_response, '__dict__'):
                            bar_chart_response = bar_chart_response.__dict__.copy()
                    
                    # Execute modified SQL if chart is possible and modified_sql is provided
                    if (bar_chart_response and 
                        bar_chart_response.get('chart_possible') and
                        bar_chart_response.get('modified_sql')):
                        
                        try:
                            validated_chart_query = validate_and_fix_query(bar_chart_response['modified_sql'])
                            chart_data = await execute_query(validated_chart_query)
                            print(chart_data)
                            
                            # Add the chart data to the dict
                            bar_chart_response['chart_data'] = chart_data
                            print(bar_chart_response)
                            print(f"Chart data executed successfully: {len(chart_data)} rows")
                        except Exception as chart_e:
                            print(f"Failed to execute chart SQL: {str(chart_e)}")
                            # Add error info to the dict
                            bar_chart_response['chart_data_error'] = str(chart_e)
                                
                except Exception as e:
                    print(f"Bar chart analysis failed: {str(e)}")
                    bar_chart_response = None
            else:
                summary_response = DataSummaryResponse(
                    summary="No data found matching the query criteria.",
                    key_insights=["No transactions found for the specified criteria"],
                    recommendation="Try adjusting search parameters or check transaction IDs",
                    transaction_status=None
                )
                
                summary_result = await with_timeout(
                    summary_agent.run("No data found for the query.", message_history=sql_result.all_messages()),
                    AI_AGENT_TIMEOUT,
                    "AI summary generation"
                )
        except HTTPException as e:
            if e.status_code == 408:
                summary_response = DataSummaryResponse(
                    summary=f"Query executed successfully. Retrieved {len(data)} records.",
                    key_insights=[f"Found {len(data)} matching records"],
                    recommendation="Data retrieved successfully. Summary generation timed out.",
                    transaction_status=None
                )
                summary_result = sql_result
            else:
                raise
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        print(bar_chart_response)
        chat_response = ChatResponse(
            success=True,
            chat_id=chat_id,
            query=request.query,
            sql_query=sql_response.sql_query,
            data=data,
            summary=summary_response.summary,
            insights=summary_response.key_insights,
            recommendation=summary_response.recommendation,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=len(data),
            bar_chart=bar_chart_response if bar_chart_response else None
        )

        response_summary = None
        try:
            response_context = f"""
            User Query: {request.query}
            SQL Query: {sql_response.sql_query}
            Data Summary: {summary_response.summary}
            Key Insights: {', '.join(summary_response.key_insights)}
            Recommendation: {summary_response.recommendation or 'None'}
            Records Found: {len(data)}
            Execution Time: {execution_time:.0f}ms
            Success: {chat_response.success}
            """
            
            summary_agent_result = await with_timeout(
                response_summary_agent.run(response_context),
                AI_AGENT_TIMEOUT,
                "Response summary generation"
            )
            response_summary = summary_agent_result.data.summary + " " + str(summary_agent_result.data.metadata)    
        except HTTPException as e:
            if e.status_code == 408:
                response_summary = f"Summary: {summary_response.summary[:100]}... (Summary generation timed out)"
            else:
                response_summary = f"Summary generation failed: {str(e)}"
        except Exception as e:
            response_summary = f"Summary generation error: {str(e)}"
        
        chat_response.response_summary = response_summary
        
        try:
            all_messages = summary_result.all_messages() if 'summary_result' in locals() else sql_result.all_messages()
            await update_chat_history(chat_id, all_messages, request.query, chat_response.dict(), response_summary)
        except Exception:
            pass
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ChatResponse(
            success=False,
            chat_id=request.chat_id or "unknown",
            query=request.query,
            sql_query="",
            data=[],
            summary=f"Error: {str(e)}",
            insights=[],
            recommendation=None,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=0,
            bar_chart=None
        )

async def handle_simple_llm_query_service(request: ChatQueryRequest, chat_id: str, message_history: list, start_time: datetime) -> ChatResponse:
    try:
        simple_context = f"""
        User Query: {request.query}
        
        This is a simple conversational query that doesn't require database analysis.
        Provide a helpful, informative response based on general knowledge about 
        financial transactions, payment processing, or answer the user's question directly.
        """
        
        try:
            simple_result = await with_timeout(
                summary_agent.run(simple_context, message_history=message_history if message_history else []),
                AI_AGENT_TIMEOUT,
                "Simple query response generation"
            )
            simple_response = simple_result.data
        except HTTPException as e:
            if e.status_code == 408:
                simple_response = DataSummaryResponse(
                    summary="I'm here to help with your payment and transaction questions. Could you please rephrase your question?",
                    key_insights=["Response generation timed out"],
                    recommendation="Please try asking your question again or be more specific.",
                    transaction_status=None
                )
            else:
                raise
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        chat_response = ChatResponse(
            success=True,
            chat_id=chat_id,
            query=request.query,
            sql_query="",
            data=[],
            summary=simple_response.summary,
            insights=simple_response.key_insights,
            recommendation=simple_response.recommendation,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=0,
            bar_chart=None
        )
        
        response_summary = None
        try:
            response_context = f"""
            User Query: {request.query}
            Query Type: Simple conversational query (no SQL needed)
            Response Summary: {simple_response.summary}
            Key Insights: {', '.join(simple_response.key_insights)}
            Recommendation: {simple_response.recommendation or 'None'}
            Execution Time: {execution_time:.0f}ms
            Success: {chat_response.success}
            """
            
            summary_agent_result = await with_timeout(
                response_summary_agent.run(response_context),
                AI_AGENT_TIMEOUT,
                "Response summary generation"
            )
            response_summary = summary_agent_result.data.summary + " " + str(summary_agent_result.data.metadata)    
        except HTTPException as e:
            if e.status_code == 408:
                response_summary = f"Summary: {simple_response.summary[:100]}... (Summary generation timed out)"
            else:
                response_summary = f"Summary generation failed: {str(e)}"
        except Exception as e:
            response_summary = f"Summary generation error: {str(e)}"
        
        chat_response.response_summary = response_summary
        
        try:
            all_messages = simple_result.all_messages() if 'simple_result' in locals() else []
            await update_chat_history(chat_id, all_messages, request.query, chat_response.dict(), response_summary)
        except Exception:
            pass
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ChatResponse(
            success=False,
            chat_id=chat_id,
            query=request.query,
            sql_query="",
            data=[],
            summary=f"Error handling simple query: {str(e)}",
            insights=[],
            recommendation=None,
            response_summary=None,
            execution_time_ms=execution_time,
            record_count=0,
            bar_chart=None
        )
