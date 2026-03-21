import os

from openai import OpenAI


DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
DEFAULT_NUM_COMPLETIONS = 1
DEFAULT_MAX_INPUT_CHARS = 12000


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars is None or max_chars <= 0:
        return text or ""
    if text is None:
        return ""
    return text if len(text) <= max_chars else text[-max_chars:]


def chatwith(
    userprompt: str,
    systemprompt: str = "you are a helpful assistant",
    *,
    model: str = "deepseek-reasoner",
    stream: bool = False,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    num_completions: int = DEFAULT_NUM_COMPLETIONS,
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    systemprompt = _truncate_text(systemprompt, max_input_chars)
    userprompt = _truncate_text(userprompt, max_input_chars)

    if stream:
        full_content = ""
        stream_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": systemprompt},
                {"role": "user", "content": userprompt},
            ],
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        for chunk in stream_resp:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content is not None:
                    full_content += delta.content

        if not full_content:
            raise ValueError("Deepseek API 流式响应为空")
        return full_content

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": systemprompt},
            {"role": "user", "content": userprompt},
        ],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=num_completions,
    )

    if not hasattr(response, "choices") or not response.choices:
        raise ValueError("Deepseek API 返回空响应（choices 为空）")

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Deepseek API 返回的 content 字段为空")
    return content


# 保留旧函数名，避免外部调用断裂
def chatwithdeepseek(
    model: str,
    systemprompt: str,
    userprompt: str,
    stream: bool = False,
    *,
    max_tokens: int,
    temperature: float,
    top_p: float,
    num_completions: int,
    max_input_chars: int,
) -> str:
    return chatwith(
        userprompt=userprompt,
        systemprompt=systemprompt,
        model=model,
        stream=stream,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        num_completions=num_completions,
        max_input_chars=max_input_chars,
    )

