import os
from openai import OpenAI
from LLM.Chatter import Chatter

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
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=num_completions,
    )

    # 这里与 Deepseek 保持同样的返回逻辑，只取第一条 completion
    return response.choices[0].message.content


class OpenAIChat(Chatter):
    """
    OpenAI Chat 模型适配器，接口风格与 Deepseek / Ollama 一致：
    - __init__ 暴露 model / system_prompt / stream / name 以及若干可选生成参数
    - generate() 使用这些参数限制生成
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        system_prompt: str = "you are a helpful assistant",
        stream: bool = False,
        name: str = "OpenAIChat",
        *,
        max_tokens: int = Chatter.DEFAULT_MAX_TOKENS,
        temperature: float = Chatter.DEFAULT_TEMPERATURE,
        top_p: float = Chatter.DEFAULT_TOP_P,
        num_completions: int = Chatter.DEFUALT_NUM_COMPLETIONS,
        max_input_chars: int = Chatter.DEFAULT_MAX_INPUT_CHARS,
    ):
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            stream=stream,
            name=name,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            num_completions=num_completions,
            max_input_chars=max_input_chars,
        )

    def generate(self, userprompt: str):
        response = chat_with_openai(
            self.model,
            self.system_prompt,
            userprompt,
            self.stream,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            num_completions=self.num_completions,
            max_input_chars=self.max_input_chars,
        )
        return {"role": self.name, "content": response}


