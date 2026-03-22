import os

from openai import OpenAI


DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
DEFAULT_NUM_COMPLETIONS = 1
DEFAULT_MAX_INPUT_CHARS = 12000




def chat_with_deepseek(
    userprompt: str,
    systemprompt: str = "you are a helpful assistant",
    *,
    model: str = "deepseek-reasoner",
    stream: bool = False,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    num_completions: int = DEFAULT_NUM_COMPLETIONS,
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


    if stream:
        full_content = ""
        stream_resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": systemprompt},
                {"role": "user", "content": userprompt},
            ],
            stream=True,
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



