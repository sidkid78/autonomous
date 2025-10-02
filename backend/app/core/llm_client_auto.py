from typing import Dict, Any, List, Optional, Callable 
import logging 
from google import genai 
from google.genai import types 
from app.config import settings 

class GeminiAIClientWithAutoTools:
    """
    An enhanced client for Gemini that leverages the Python SDK's 
    automatic function calling feature.
    """
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Missing Google GenAI configuration. Required: GOOGLE_API_KEY")

        self.client = genai.Client()
        self.model_name = settings.GEMINI_MODEL_NAME
        logging.info(f"GeminiAIClientWithAutoTools initialized with model: {self.model_name}")

    async def chat_with_tools_async(
        self, 
        prompt: str,
        tools: List[Callable],
        temperature: float = 0.7,
    ) -> str:
        """
        Generates a final text resonse by automatically handling tool calls.
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=f"models/{self.model_name}",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=temperature
                ),
            )

            return response.text 
        except Exception as e:
            logging.error(f"Error calling Gemini API with tools: {e}")
            raise