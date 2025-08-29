import logging
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class GeminiProvider:
    def __init__(self, api_key: str):
        """Initialize Gemini provider with API key"""
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        self.model = "gemini-2.5-pro"
        logger.info(f"Gemini provider initialized with key length: {len(api_key)}")
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Google Gemini API"""
        logger.info(f"Prompt lengths - system: {len(system_prompt)}, user: {len(user_prompt)}")
        
        start_time = time.time()
        
        try:
            # Safety settings to avoid blocking
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_NONE,
                },
            ]
            
            # Create model instance
            gemini_model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "temperature": 1.1,
                    "top_p": 0.7,
                    "max_output_tokens": 10000,
                },
                safety_settings=safety_settings
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate response
            response = gemini_model.generate_content(full_prompt)
            
            elapsed = time.time() - start_time
            logger.info(f"Gemini request completed in {elapsed:.2f}s")
            
            # Check for response
            if not response.parts or not response.text:
                if response.candidates and response.candidates[0].finish_reason:
                    logger.warning(f"Gemini response blocked: {response.candidates[0].finish_reason}")
                raise Exception("Empty response from Gemini")
            
            text = response.text.strip()
            
            # Log token usage if available
            if hasattr(response, 'usage_metadata'):
                logger.info(
                    f"Gemini token usage - prompt: {response.usage_metadata.prompt_token_count}, "
                    f"completion: {response.usage_metadata.candidates_token_count}, "
                    f"total: {response.usage_metadata.total_token_count}"
                )
            
            logger.info(f"Generated response length: {len(text)} characters")
            return text
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Gemini request failed after {elapsed:.2f}s: {e}")
            raise