import os
from openai import OpenAI

def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars is None or max_chars <= 0:
        return text or ""
    if text is None:
        return ""
    return text if len(text) <= max_chars else text[-max_chars:]


def chat_with_openai(
    model: str,
    systemprompt: str,
    userprompt: str,
    stream: bool,
    *,
    max_tokens: int,
    temperature: float,
    top_p: float,
    num_completions: int,
    max_input_chars: int,
):
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    systemprompt = _truncate_text(systemprompt, max_input_chars)
    userprompt = _truncate_text(userprompt, max_input_chars)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": systemprompt},
            {"role": "user", "content": userprompt},
        ],
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        n=num_completions,
    )

    # 这里与 Deepseek 保持同样的返回逻辑，只取第一条 completion
    return response.choices[0].message.content





