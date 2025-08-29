# app/services/ai_providers/openai_provider.py
import logging
import time
import asyncio
from openai import AsyncOpenAI
from typing import Optional

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    OpenAI provider with proper timeout handling and connection management
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = api_key
        # self.models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
        self.timeout = 120  # Maximum time for AI request
        logger.info("OpenAIProvider initialized (key length=%d)", len(api_key))

    async def generate(self, system_prompt: str, user_prompt: str, model: str = "gpt-5") -> str:
        """
        Call Responses API with timeout protection
        """
        logger.info("OpenAIProvider.generate start - model=%s", model)
        start = time.time()

        try:
            # Create client with timeout
            client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=self.timeout,  # Add timeout
                max_retries=2  # Limit retries
            )
            
            # Combine prompts
            combined_input = f"{system_prompt}\n\n{user_prompt}"
            
            # Wrap in asyncio timeout for additional protection
            try:
                resp = await asyncio.wait_for(
                    client.responses.create(
                        model=model,
                        input=combined_input,
                        reasoning={"effort": "low"},  
                        text={"verbosity": "low"}
                    ),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"OpenAI request timed out after {self.timeout}s")
                raise TimeoutError(f"OpenAI request timed out after {self.timeout}s")
            finally:
                # Always close the client
                await client.close()

            elapsed = time.time() - start
            logger.info("Responses API completed in %.2fs", elapsed)

            # Handle response extraction (keeping your existing logic)
            if hasattr(resp, 'output_text') and resp.output_text:
                return resp.output_text.strip()
            elif hasattr(resp, 'output') and resp.output:
                if isinstance(resp.output, str):
                    return resp.output.strip()
                elif hasattr(resp.output, 'text'):
                    return resp.output.text.strip()
                elif hasattr(resp.output, 'content'):
                    return resp.output.content.strip()
                elif isinstance(resp.output, list):
                    text_parts = []
                    for item in resp.output:
                        if item is None:
                            continue
                        
                        if hasattr(item, 'text') and item.text:
                            text_parts.append(str(item.text))
                        elif hasattr(item, 'content') and item.content:
                            text_parts.append(str(item.content))
                        elif isinstance(item, str):
                            text_parts.append(item)
                        elif hasattr(item, 'type') and item.type == 'text' and hasattr(item, 'text'):
                            text_parts.append(str(item.text))
                    
                    if text_parts:
                        result = "".join(text_parts).strip()
                        logger.info("Assembled response from %d text parts", len(text_parts))
                        return result
                    else:
                        logger.warning("No valid text parts found in response output list")
            
            logger.error("Could not extract text from Responses API response")
            raise RuntimeError("Could not extract text from Responses API response")

        except TimeoutError:
            # Re-raise timeout errors
            raise
        except Exception as e:
            elapsed = time.time() - start
            logger.error("OpenAI Responses API call failed after %.2fs: %s", elapsed, e, exc_info=True)
            raise