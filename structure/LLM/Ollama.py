import ollama


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars is None or max_chars <= 0:
        return text or ""
    if text is None:
        return ""
    return text if len(text) <= max_chars else text[-max_chars:]


DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.95
DEFAULT_NUM_COMPLETIONS = 1
DEFAULT_MAX_INPUT_CHARS = 12000


def chat_with_ollama(
    model: str,
    systemprompt: str,
    userprompt: str,
    stream: bool,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    num_completions: int = DEFAULT_NUM_COMPLETIONS,
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
) -> str:
    # 与其它 chat_with_* 保持一致：先做输入截断。
    systemprompt = _truncate_text(systemprompt, max_input_chars // 2)
    userprompt = _truncate_text(userprompt, max_input_chars // 2)
    prompt = f"{systemprompt}\n\n{userprompt}"

    if stream:
        stream_resp = ollama.generate(
            model=model,
            prompt=prompt,
            stream=True,
            options={
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
            },
        )
        chunks = []
        for chunk in stream_resp:
            if hasattr(chunk, "model_dump"):
                data = chunk.model_dump()
            elif isinstance(chunk, dict):
                data = chunk
            else:
                data = {}
            piece = data.get("response")
            if piece:
                chunks.append(piece)
        return "".join(chunks)

    # 注意：Ollama 通常不支持一次返回多条 completion，这里仅保留参数以对齐接口。
    _ = num_completions
    response = ollama.generate(
        model=model,
        prompt=prompt,
        stream=False,
        options={
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        },
    )

    if hasattr(response, "model_dump"):
        data = response.model_dump()
    elif isinstance(response, dict):
        data = response
    else:
        return str(response)
    return data.get("response", "")