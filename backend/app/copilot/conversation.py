# app/copilot/conversation.py

# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_service import LLMProvider
from app.copilot.dispatcher import execute_tool, get_tool_schemas
from app.copilot.safety import contains_overclaim, SAFE_FALLBACK_REPLY

import logging

logger = logging.getLogger("copilot")


MAX_TOOL_CALLS = 5

COPILOT_SYSTEM_PROMPT = """You are the Financial Compass AI Copilot. You help \
users understand their own financial data using ONLY the tools provided.

STRICT RULES:
- NEVER state a financial fact (income, DTI, EMI, scheme eligibility, fraud risk) \
unless it came from a tool result. Never estimate or guess numbers yourself.
- If a tool returns an "error", explain it plainly to the user — do not invent \
a workaround or pretend the data exists.
- Never state or imply loan approval, guaranteed scheme eligibility, or that a \
message is definitely safe/a scam. Use the same cautious language the tools \
themselves use.
- If the user's request doesn't match any available tool, say so clearly instead \
of guessing an answer.
- Keep responses concise and in plain language.
"""


async def run_copilot_turn(
    db: AsyncSession,
    user_id,
    llm: LLMProvider,
    user_message: str,
    history: list[dict] | None = None,
) -> dict:
    messages = (history or []) + [
        {"role": "user", "content": user_message}
    ]

    tools = get_tool_schemas()

    for _ in range(MAX_TOOL_CALLS):
        response = await llm.generate_with_tools(
            COPILOT_SYSTEM_PROMPT,
            messages,
            tools,
        )

        if response["type"] == "text":
            reply = response["content"]

            if contains_overclaim(reply):
                logger.warning(
                    "Copilot reply contained an overclaim phrase and was replaced (length=%d)",
                    len(reply),
            )
                reply = SAFE_FALLBACK_REPLY

            messages.append({
                "role": "model",
                "content": reply,
            })

            return {
                "reply": reply,
                "messages": messages,
            }

        tool_name = response["name"]

        result = await execute_tool(
            db,
            user_id,
            tool_name,
            response["arguments"],
        )

        messages.append({
            "role": "model",
            "content": f"[called {tool_name}]",
        })

        messages.append({
            "role": "tool",
            "name": tool_name,
            "content": result,
        })

    fallback = (
        "I wasn't able to complete this request. "
        "Could you rephrase or ask something more specific?"
    )

    messages.append({
        "role": "model",
        "content": fallback,
    })

    return {
        "reply": fallback,
        "messages": messages,
    }