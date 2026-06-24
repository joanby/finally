from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services import chat

router = APIRouter(prefix="/api/chat")


class ChatRequest(BaseModel):
    message: str


@router.post("")
def post_chat(req: ChatRequest, request: Request) -> dict:
    return chat.handle_message(req.message, request.app.state.provider)
