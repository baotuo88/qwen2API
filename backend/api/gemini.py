from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import json
import logging
import asyncio
from backend.services.qwen_client import QwenClient
from backend.services.token_calc import calculate_usage
from backend.core.config import resolve_model

log = logging.getLogger("qwen2api.gemini")
router = APIRouter()

@router.post("/models/{model}:streamGenerateContent")
async def gemini_stream(model: str, request: Request):
    """
    Gemini API 协议转换层 -> 转入 OpenAI/Qwen 统一处理内核
    """
    app = request.app
    users_db = app.state.users_db
    client: QwenClient = app.state.qwen_client
    
    token = request.query_params.get("key")
    if not token:
        raise HTTPException(status_code=401, detail="Missing API Key")
        
    users = await users_db.get()
    user = next((u for u in users if u["id"] == token), None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    body = await request.json()
    resolved_model = resolve_model(model)
    contents = body.get("contents", [])
    
    content = ""
    for m in contents:
        if m.get("role") == "user":
            for part in m.get("parts", []):
                content += part.get("text", "") + "\n"
                
    try:
        events, chat_id, acc = await client.chat_stream_events_with_retry(resolved_model, content)
    except Exception as e:
        log.error(f"Gemini proxy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    async def generate():
        full_text = ""
        try:
            for evt in events:
                if evt.get("type") == "delta":
                    text = evt.get("content", "")
                    full_text += text
                    chunk = {
                        "candidates": [
                            {"content": {"parts": [{"text": text}], "role": "model"}}
                        ]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
            usage = calculate_usage(content, full_text)
            
            users = await users_db.get()
            for u in users:
                if u["id"] == token:
                    u["used_tokens"] += usage["total_tokens"]
                    break
            await users_db.save(users)
            
        finally:
            client.account_pool.release(acc)
            asyncio.create_task(client.delete_chat(acc.token, chat_id))
            
    return StreamingResponse(generate(), media_type="text/event-stream")
