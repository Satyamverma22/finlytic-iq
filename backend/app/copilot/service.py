# app/copilot/service.py

import json
import uuid

# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import LLMProvider
from app.copilot.conversation import run_copilot_turn
from app.copilot.models import CopilotConversation, CopilotMessage


class ConversationNotFoundError(Exception):
    pass


async def send_message(
    db: AsyncSession, user_id, llm: LLMProvider,
    message: str, conversation_id: uuid.UUID | None,
) -> dict:
    if conversation_id:
        result = await db.execute(
            select(CopilotConversation).where(
                CopilotConversation.id == conversation_id,
                CopilotConversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise ConversationNotFoundError()
    else:
        conversation = CopilotConversation(user_id=user_id, title=message[:100])
        db.add(conversation)
        await db.flush()

    msg_result = await db.execute(
        select(CopilotMessage)
        .where(CopilotMessage.conversation_id == conversation.id)
        .order_by(CopilotMessage.created_at)
    )
    stored = msg_result.scalars().all()
    history = [
        {
            "role": m.role,
            "content": json.loads(m.content) if m.role == "tool" else m.content,
            **({"name": m.tool_name} if m.tool_name else {}),
        }
        for m in stored
    ]

    turn = await run_copilot_turn(db, user_id, llm, message, history=history)
    new_messages = turn["messages"][len(history):]

    for m in new_messages:
        content = m["content"]
        db.add(CopilotMessage(
            conversation_id=conversation.id,
            role=m["role"],
            content=json.dumps(content) if not isinstance(content, str) else content,
            tool_name=m.get("name"),
        ))

    await db.commit()
    return {"conversation_id": conversation.id, "reply": turn["reply"]}