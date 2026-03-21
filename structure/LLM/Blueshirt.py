import aiohttp
from typing import List, Union, Optional
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    RetryCallState
)
from typing import Dict, Any
from dotenv import load_dotenv
import os
import json
import asyncio
import logging
# Configure logger
logger = logging.getLogger(__name__)

load_dotenv()
BLUESHIRT_BASE_URL = os.getenv('BLUESHIRT_BASE_URL', '')
BLUESHIRT_API = os.getenv('BLUESHIRT_API', '')

# Retry configuration
MAX_RETRIES = 5  # Maximum number of retries
MAX_WAIT_TIME = 60  # Maximum wait time (seconds)
MIN_WAIT_TIME = 1  # Minimum wait time (seconds)
# Timeout configuration: can be customized via environment variables; defaults are generous for complex requests.
REQUEST_TIMEOUT = int(os.getenv('BLUESHIRT_REQUEST_TIMEOUT', '120'))  # Request timeout (seconds), default 2 minutes
CONNECT_TIMEOUT = int(os.getenv('BLUESHIRT_CONNECT_TIMEOUT', '60'))  # Connection timeout (seconds), default 1 minute


def log_retry_attempt(retry_state: RetryCallState):
    """Log a retry attempt."""
    attempt_number = retry_state.attempt_number
    exception = retry_state.outcome.exception()
    wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
    logger.warning(
        f"BlueShirt API call failed (attempt {attempt_number}/{MAX_RETRIES + 1}): "
        f"{type(exception).__name__}: {str(exception)[:100]}. "
        f"Retrying in {wait_time:.2f} seconds..."
    )


@retry(
    wait=wait_random_exponential(multiplier=1, min=MIN_WAIT_TIME, max=MAX_WAIT_TIME),
    stop=stop_after_attempt(MAX_RETRIES + 1),  # In total, try MAX_RETRIES + 1 times
    retry=retry_if_exception_type((aiohttp.ClientError, aiohttp.ClientOSError, asyncio.TimeoutError, KeyError)),
    before_sleep=log_retry_attempt,
    reraise=True
)
async def ablueshirt_chat(
        model: str,
        msg: List[Dict],
        stream: bool = False,
        stream_options: Optional[Dict] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
):
    """
    Asynchronously call the BlueShirt API.

    Parameters:
    - model: Model name.
    - msg: List of messages (supports multimodal; content can be a string or array).
    - stream: Whether to use streaming output.
    - stream_options: Stream options (e.g., {"include_usage": True}).
    - max_tokens: Maximum number of tokens.
    - temperature: Sampling temperature.
    """
    url = f"{BLUESHIRT_BASE_URL}/v1/chat/completions"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {BLUESHIRT_API}'
    }

    payload = {
        "model": model,
        "messages": msg,
        "stream": stream
    }

    if stream_options is not None:
        payload["stream_options"] = stream_options

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    if temperature is not None:
        payload["temperature"] = temperature

    import time
    start_time = time.time()
    logger.info(f"BlueShirt API request started: model={model}, timeout={REQUEST_TIMEOUT}s, stream={stream}")

    try:
        async with aiohttp.ClientSession() as session:
            # For streaming responses, use a longer timeout
            timeout_value = REQUEST_TIMEOUT * 2 if stream else REQUEST_TIMEOUT
            timeout = aiohttp.ClientTimeout(total=timeout_value, connect=CONNECT_TIMEOUT)

            async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"BlueShirt API returned non-200 status {response.status}: {error_text}")

                if stream:
                    # Handle streaming responses
                    full_response = ""
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                json_data = json.loads(data)
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    # Safely extract the content field
                                    if 'content' in delta and delta['content'] is not None:
                                        content = delta['content']
                                        full_response += content
                                    elif 'text' in delta and delta['text'] is not None:
                                        # Try alternative field names
                                        full_response += delta['text']
                            except json.JSONDecodeError:
                                continue
                            except KeyError as e:
                                # Log and continue processing without terminating the stream
                                logger.warning(f"Missing field in streaming response: {e}")
                                continue

                    if not full_response:
                        raise ValueError("Empty streaming response")

                    # Streaming responses may not provide accurate token usage; try to approximate
                    import tiktoken
                    try:
                        encoder = tiktoken.get_encoding("cl100k_base")
                        # Extract text for token counting
                        prompt_text = ""
                        for m in msg:
                            content = m.get('content', '')
                            if isinstance(content, str):
                                prompt_text += content + "\n"
                            elif isinstance(content, list):
                                # Handle multimodal content
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'text':
                                        prompt_text += item.get('text', '') + "\n"
                        cost_count(prompt_text, full_response, model)
                    except:
                        pass

                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"BlueShirt API streaming response completed: elapsed={elapsed_time:.2f}s, "
                        f"response_len={len(full_response)} chars"
                    )
                    return full_response
                else:
                    # Handle non-streaming responses
                    result = await response.json()

                    # Validate response format
                    if 'choices' not in result or len(result['choices']) == 0:
                        raise KeyError("Missing or empty 'choices' field in response")

                    if 'message' not in result['choices'][0]:
                        raise KeyError("Missing 'message' field in choices[0]")

                    # Safely extract content, handling missing fields
                    message = result['choices'][0]['message']
                    if 'content' not in message:
                        # Log the actual response structure for debugging
                        logger.error(
                            "BlueShirt API response missing 'content'. Full response: "
                            f"{json.dumps(result, indent=2, ensure_ascii=False)}"
                        )
                        # Try other possible fields for fallback
                        if 'text' in message:
                            response_content = message['text']
                        elif 'text_content' in message:
                            response_content = message['text_content']
                        else:
                            # If there is no content at all, return an empty string or raise a clearer error
                            raise KeyError(
                                "Missing 'content' field in message. Message object: "
                                f"{json.dumps(message, indent=2, ensure_ascii=False)}"
                            )
                    else:
                        response_content = message['content']

                    # Handle cases where content is None
                    if response_content is None:
                        response_content = ""

                    # Extract usage info and count tokens
                    usage = result.get('usage', {})
                    prompt_tokens = usage.get('prompt_tokens', 0) if usage else 0
                    completion_tokens = usage.get('completion_tokens', 0) if usage else 0

                    # If usage is missing, try to estimate from messages
                    if prompt_tokens == 0:
                        import tiktoken
                        try:
                            encoder = tiktoken.get_encoding("cl100k_base")
                            # Extract text for token counting
                            prompt_text = ""
                            for m in msg:
                                content = m.get('content', '')
                                if isinstance(content, str):
                                    prompt_text += content + "\n"
                                elif isinstance(content, list):
                                    # Handle multimodal content
                                    for item in content:
                                        if isinstance(item, dict) and item.get('type') == 'text':
                                            prompt_text += item.get('text', '') + "\n"
                            prompt_tokens = len(encoder.encode(prompt_text))
                            completion_tokens = len(encoder.encode(response_content)) if response_content else 0
                        except:
                            prompt_tokens = 0
                            completion_tokens = 0

                    # Count tokens and cost
                    prompt_text = ""
                    for m in msg:
                        content = m.get('content', '')
                        if isinstance(content, str):
                            prompt_text += content + "\n"
                        elif isinstance(content, list):
                            # Handle multimodal content
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    prompt_text += item.get('text', '') + "\n"
                    cost_count(prompt_text, response_content, model)

                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"BlueShirt API non-streaming response completed: elapsed={elapsed_time:.2f}s, "
                        f"response_len={len(response_content)} chars"
                    )
                    return response_content

    except asyncio.TimeoutError as e:
        elapsed_time = time.time() - start_time
        error_msg = (
            f"BlueShirt API request timeout (waited {elapsed_time:.2f}s, "
            f"timeout={REQUEST_TIMEOUT}s, stream={stream})"
        )
        logger.error(error_msg)
        logger.error(f"Request details: model={model}, url={url}")
        raise
    except aiohttp.ClientConnectorError as e:
        error_msg = f"BlueShirt API connection failed: {str(e)}"
        logger.error(error_msg)
        raise
    except aiohttp.ClientOSError as e:
        error_msg = f"BlueShirt API network error: {str(e)}"
        logger.error(error_msg)
        raise
    except aiohttp.ClientResponseError as e:
        error_msg = f"BlueShirt API HTTP error: {e.status} - {e.message}"
        logger.error(error_msg)
        raise
    except aiohttp.ClientError as e:
        error_msg = f"BlueShirt API client error: {str(e)}"
        logger.error(error_msg)
        raise
    except KeyError as e:
        error_msg = f"Failed to parse BlueShirt response: {str(e)}"
        logger.error(error_msg)
        logger.error(f"KeyError details: missing key '{str(e)}'. Please check response format.")
        raise
    except json.JSONDecodeError as e:
        error_msg = f"BlueShirt API JSON decode failed: {str(e)}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"BlueShirt API unknown error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise


@LLMRegistry.register('BlueShirtChat')
class BlueShirtChat(LLM):

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def agen(
            self,
            messages: List[Message],
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            num_comps: Optional[int] = None,
            stream: bool = False,
            stream_options: Optional[Dict] = None,
    ) -> Union[List[str], str]:

        if max_tokens is None:
            max_tokens = self.DEFAULT_MAX_TOKENS
        if temperature is None:
            temperature = self.DEFAULT_TEMPERATURE
        if num_comps is None:
            num_comps = self.DEFUALT_NUM_COMPLETIONS

        # Convert messages to API format
        if isinstance(messages, str):
            messages = [{'role': 'user', 'content': messages}]
        else:
            # Convert Message objects to dictionaries
            msg_list = []
            for msg in messages:
                if isinstance(msg, Message):
                    msg_dict = msg.dict()
                    msg_list.append(msg_dict)
                elif isinstance(msg, dict):
                    msg_list.append(msg)
                else:
                    msg_list.append({'role': 'user', 'content': str(msg)})
            messages = msg_list

        response = await ablueshirt_chat(
            model=self.model_name,
            msg=messages,
            stream=stream,
            stream_options=stream_options,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response

    def gen(
            self,
            messages: List[Message],
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            num_comps: Optional[int] = None,
    ) -> Union[List[str], str]:
        pass
