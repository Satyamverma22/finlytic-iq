from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import settings


class LLMProvider(ABC):

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response given a system prompt and a user prompt."""
        ...

    @abstractmethod
    async def generate_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list,
    ) -> dict:
        """
        messages:
        [{"role": "user"|"model"|"tool", "content": ...}, ...]

        Returns:
        {"type": "tool_call", "name": str, "arguments": dict}
        or
        {"type": "text", "content": str}
        """
        ...


class GeminiLLMProvider(LLMProvider):

    MODEL_NAME = "gemini-3.6-flash"

    def __init__(self):
        # pyrefly: ignore [missing-import]
        from google import genai

        self._client = genai.Client(
            api_key=settings.llm_api_key
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        import asyncio

        # pyrefly: ignore [missing-import]
        from google.genai import types

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            ),
        )

        return response.text

    async def generate_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list,
    ) -> dict:
        import asyncio

        # pyrefly: ignore [missing-import]
        from google.genai import types

        function_declarations = [
            types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
            )
            for t in tools
        ]

        contents = []

        for message in messages:
            if message["role"] == "tool":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=message["name"],
                                response={"result": message["content"]},
                            )
                        ],
                    )
                )

            elif message["role"] == "model":
                contents.append(
                    types.Content(
                        role="model",
                        parts=[
                            types.Part(
                                text=message["content"]
                            )
                        ],
                    )
                )

            else:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part(
                                text=message["content"]
                            )
                        ],
                    )
                )

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                tools=[
                    types.Tool(
                        function_declarations=function_declarations
                    )
                ],
            ),
        )

        part = response.candidates[0].content.parts[0]

        if part.function_call:
            return {
                "type": "tool_call",
                "name": part.function_call.name,
                "arguments": dict(part.function_call.args),
            }

        return {
            "type": "text",
            "content": response.text,
        }


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:

    provider_name = settings.llm_provider or "gemini"

    if provider_name == "gemini":
        return GeminiLLMProvider()

    raise NotImplementedError(
        f"Unknown LLM provider: '{provider_name}'"
    )