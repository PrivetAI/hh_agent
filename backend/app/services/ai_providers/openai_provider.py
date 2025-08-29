import logging
import time
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    OpenAI provider using Responses API.
    Matches AIService expectations:
      - async generate(system_prompt, user_prompt, model) -> str
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = api_key
        self.models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
        logger.info("OpenAIProvider initialized (key length=%d)", len(api_key))

    async def generate(self, system_prompt: str, user_prompt: str, model: str = "gpt-5") -> str:
        """
        Call Responses API and return plain text.
        Fixed signature to match expected pattern with model parameter.
        """
        logger.info("OpenAIProvider.generate start - model=%s", model)
        start = time.time()

        try:
            async with AsyncOpenAI(api_key=self.api_key) as client:
                # Combine system and user prompts
                combined_input = f"{system_prompt}\n\n{user_prompt}"
                
                resp = await client.responses.create(
                    model=model,
                    input=combined_input,
                    reasoning={"effort": "low"},  # For faster responses
                    text={"verbosity": "low"}
                )

                elapsed = time.time() - start
                logger.info("Responses API completed in %.2fs", elapsed)

                # Debug: Log the response structure
                logger.info("Response type: %s", type(resp))
                logger.info("Response attributes: %s", [attr for attr in dir(resp) if not attr.startswith('_')])
                
                # Handle the response structure correctly
                if hasattr(resp, 'output_text') and resp.output_text:
                    # Direct text output
                    logger.info("Found output_text attribute")
                    return resp.output_text.strip()
                elif hasattr(resp, 'output') and resp.output:
                    # Handle different output formats
                    if isinstance(resp.output, str):
                        return resp.output.strip()
                    elif hasattr(resp.output, 'text'):
                        return resp.output.text.strip()
                    elif hasattr(resp.output, 'content'):
                        return resp.output.content.strip()
                    elif isinstance(resp.output, list):
                        # Handle list of output items - filter None values
                        text_parts = []
                        for item in resp.output:
                            if item is None:
                                logger.warning("Found None item in response output, skipping")
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
                
                # Try to extract from the raw response object
                logger.warning("Attempting to extract text from raw response object")
                logger.debug("Response object type: %s", type(resp))
                logger.debug("Response object attributes: %s", dir(resp))
                
                # Last resort: convert entire response to string and look for patterns
                response_str = str(resp)
                logger.debug("Raw response string: %s", response_str[:500])  # Log first 500 chars
                
                # If we still can't find text, raise a detailed error
                logger.error("Could not extract text from Responses API response")
                logger.error("Response type: %s", type(resp))
                logger.error("Response attributes: %s", [attr for attr in dir(resp) if not attr.startswith('_')])
                
                if hasattr(resp, 'output'):
                    logger.error("Output type: %s", type(resp.output))
                    logger.error("Output value: %s", resp.output)
                
                raise RuntimeError("Could not extract text from Responses API response")

        except Exception as e:
            elapsed = time.time() - start
            logger.error("OpenAI Responses API call failed after %.2fs: %s", elapsed, e, exc_info=True)
            raise