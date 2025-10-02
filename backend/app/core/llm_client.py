# app/core/llm_client.py
from typing import Dict, Any, List, Optional
import logging
from google import genai
from google.genai import types
from app.config import settings

class GeminiAIClient:
    """
    Client for interacting with the Google Generative AI (Gemini) API using the latest SDK.

    This client uses the new client-centric pattern (genai.Client) for all interactions.
    It supports both simple text generation and manual tool-calling flows.

    Attributes:
        client (genai.Client): The configured genai client instance.
        model_name (str): The name of the Gemini model to use.
    """
    def __init__(self):
        """
        Initializes and configures the Gemini client.
        
        Raises:
            ValueError: If the GOOGLE_API_KEY is not configured.
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Missing Google GenAI configuration. Required: GOOGLE_API_KEY")
        
        # The client automatically picks up the GOOGLE_API_KEY from the environment.
        self.client = genai.Client()
        self.model_name = settings.GEMINI_MODEL_NAME
        logging.info(f"GeminiAIClient initialized with model: {self.model_name}")

    async def generate_text_async(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 2048
    ) -> str:
        """
        Generate a simple text response from the Gemini API.

        Args:
            prompt (str): The prompt to send to the API.
            temperature (float): Sampling temperature to control randomness.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The generated text content from the API.
        """
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        try:
            # Note the use of the `.aio` namespace for asynchronous operations
            response = await self.client.aio.models.generate_content(
                model=f"models/{self.model_name}",
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logging.error(f"Error calling Gemini API for text generation: {e}")
            raise

    async def generate_with_tools_async(
        self,
        prompt: str,
        function_declarations: List[Dict[str, Any]],
        temperature: float = 0.7,
        tool_config: Optional[types.ToolConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from Gemini, potentially requesting a tool call.
        This method handles the tool-calling flow manually.

        Args:
            prompt (str): The user prompt to send to the API.
            function_declarations (List[Dict[str, Any]]): A list of function declarations.
            temperature (float): Sampling temperature to control randomness.

        Returns:
            Dict[str, Any]: A dictionary containing either text content or tool call details.
        """
        try:
            # 1. Wrap the function declarations in the required Tool object
            tools = types.Tool(function_declarations=function_declarations)
            
            # 2. Create the generation config with the tools
            config = types.GenerateContentConfig(
                tools=[tools],
                temperature=temperature,
                tool_config=tool_config
            )

            # 3. Call the API
            response = await self.client.aio.models.generate_content(
                model=f"models/{self.model_name}",
                contents=prompt,
                config=config,
            )
            
            # 4. Check the response for a function call
            response_part = response.candidates[0].content.parts[0]
            
            if response_part.function_call:
                function_call = response_part.function_call
                arguments = dict(function_call.args)
                
                logging.info(f"Gemini requested tool call: {function_call.name} with args: {arguments}")
                return {
                    "type": "tool_call",
                    "name": function_call.name,
                    "arguments": arguments,
                }
            
            # Handle regular text response
            logging.info("Gemini returned a text response.")
            return {
                "type": "text",
                "content": response.text,
            }
        except Exception as e:
            logging.error(f"Error calling Gemini API with tools: {e}")
            raise

# Singleton instance for the Gemini client
_llm_client: Optional[GeminiAIClient] = None

def get_llm_client() -> GeminiAIClient:
    """
    Get the LLM client instance using the singleton pattern.
    This client handles both text and tool-based generation.

    Returns:
        GeminiAIClient: The singleton instance of the GeminiAIClient.
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = GeminiAIClient()
    return _llm_client

# class AzureOpenAIClient:
#     """

#         if not self.api_key or not self.resource_name:
#             raise ValueError("Missing Azure OpenAI configuration. Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_RESOURCE_NAME")
        
#         # Construct the API URL
#         self.api_url = f"https://{self.resource_name}.openai.azure.com/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
    
#     async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
#         """
#         Generate a response from Azure OpenAI.

#         Args:
#             prompt (str): The prompt to send to the Azure OpenAI API.
#             temperature (float): Sampling temperature to control randomness in responses.
#             max_tokens (int): The maximum number of tokens to generate in the response.

#         Returns:
#             str: The generated response content from the Azure OpenAI API.
#         """
#         headers = {
#             "api-key": self.api_key,
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             "messages": [{"role": "user", "content": prompt}],
#             "max_tokens": max_tokens,
#             "temperature": temperature
#         }
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(self.api_url, json=payload, headers=headers) as response:
#                     if response.status != 200:
#                         error_text = await response.text()
#                         logging.error(f"Azure OpenAI API error: {error_text}")
#                         raise Exception(f"Azure OpenAI API returned status {response.status}: {error_text}")
                    
#                     result = await response.json()
#                     return result["choices"][0]["message"]["content"]
#         except Exception as e:
#             logging.error(f"Error calling Azure OpenAI API: {str(e)}")
#             raise

# class AzureOpenAIFunctions:
#     """
#     Client for Azure OpenAI with support for function calling.

#     This client extends the basic Azure OpenAI client to handle function calling capabilities,
#     allowing for more complex interactions with the API.

#     Attributes:
#         api_key (str): The API key for authenticating with Azure OpenAI.
#         resource_name (str): The name of the Azure OpenAI resource.
#         deployment_id (str): The deployment ID for the specific model.
#         api_version (str): The version of the Azure OpenAI API to use.
#         api_url (str): The constructed URL for making API requests.
#     """
#     def __init__(self):
#         self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
#         self.resource_name = os.getenv("AZURE_OPENAI_RESOURCE_NAME")
#         self.deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4o")
#         self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
#         if not self.api_key or not self.resource_name:
#             raise ValueError("Missing Azure OpenAI configuration. Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_RESOURCE_NAME")
        
#         # Construct the API URL
#         self.api_url = f"https://{self.resource_name}.openai.azure.com/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
    
#     async def generate_with_functions(
#         self, 
#         prompt: str, 
#         functions: list, 
#         function_call: str = "auto",
#         temperature: float = 0.7, 
#         max_tokens: int = 1500
#     ) -> Dict[str, Any]:
#         """
#         Generate a response from Azure OpenAI with function calling.

#         Args:
#             prompt (str): The user prompt to send to the Azure OpenAI API.
#             functions (list): List of function definitions to be used in the API call.
#             function_call (str): Specifies whether to call a function automatically or by name.
#             temperature (float): Sampling temperature to control randomness in responses.
#             max_tokens (int): The maximum number of tokens to generate in the response.

#         Returns:
#             Dict[str, Any]: A dictionary containing either the message content or function call details.
#         """
#         headers = {
#             "api-key": self.api_key,
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             "messages": [{"role": "user", "content": prompt}],
#             "functions": functions,
#             "function_call": function_call,
#             "max_tokens": max_tokens,
#             "temperature": temperature
#         }
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(self.api_url, json=payload, headers=headers) as response:
#                     if response.status != 200:
#                         error_text = await response.text()
#                         logging.error(f"Azure OpenAI API error: {error_text}")
#                         raise Exception(f"Azure OpenAI API returned status {response.status}: {error_text}")
                    
#                     result = await response.json()
#                     message = result["choices"][0]["message"]
                    
#                     # Handle function call response
#                     if "function_call" in message:
#                         function_call = message["function_call"]
#                         return {
#                             "type": "function_call",
#                             "name": function_call["name"],
#                             "arguments": json.loads(function_call["arguments"])
#                         }
                    
#                     # Handle regular text response
#                     return {
#                         "type": "text",
#                         "content": message["content"]
#                     }
#         except Exception as e:
#             logging.error(f"Error calling Azure OpenAI API with functions: {str(e)}")
#             raise

# # Singleton instances
# _regular_client = None
# _functions_client = None

# def get_llm_client() -> AzureOpenAIClient:
#     """
#     Get the basic LLM client instance (singleton pattern).

#     Returns:
#         AzureOpenAIClient: The singleton instance of the AzureOpenAIClient.
#     """
#     global _regular_client
#     if _regular_client is None:
#         _regular_client = AzureOpenAIClient()
#     return _regular_client

# def get_functions_client() -> AzureOpenAIFunctions:
#     """
#     Get the functions-enabled LLM client instance (singleton pattern).

#     Returns:
#         AzureOpenAIFunctions: The singleton instance of the AzureOpenAIFunctions.
#     """
#     global _functions_client
#     if _functions_client is None:
#         _functions_client = AzureOpenAIFunctions()
#     return _functions_client