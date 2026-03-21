import ollama
from LLM.Chatter import Chatter


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars is None or max_chars <= 0:
        return text or ""
    if text is None:
        return ""
    return text if len(text) <= max_chars else text[-max_chars:]


class Ollama(Chatter):
    """
    调用本地 Ollama 模型的适配器，实现与 Deepseek 相同的 Chatter 接口：
    - __init__ 中提供可选参数（max_tokens / temperature / top_p / num_completions / max_input_chars）
    - generate() 中使用这些参数限制生成行为
    """

    def __init__(
        self,
        model: str = "mistral",
        system_prompt: str = "you are a helpful assistant",
        stream: bool = False,
        name: str = "Ollama",
        debug: bool = False,
        *,
        max_tokens: int = Chatter.DEFAULT_MAX_TOKENS,
        temperature: float = Chatter.DEFAULT_TEMPERATURE,
        top_p: float = Chatter.DEFAULT_TOP_P,
        num_completions: int = Chatter.DEFUALT_NUM_COMPLETIONS,
        max_input_chars: int = Chatter.DEFAULT_MAX_INPUT_CHARS,
    ):
        # 统一走基类初始化，保持参数含义一致
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
        self.debug = debug
        # 打印初始化参数（仅调试时）
        if self.debug:
            print(
                f"[Ollama] 初始化完成：model={self.model}, "
                f"max_tokens={self.max_tokens}, temperature={self.temperature}, "
                f"top_p={self.top_p}, max_input_chars={self.max_input_chars}"
            )

    def generate(self, userprompt: str):
        if self.debug:
            print("[Ollama] 开始生成")
            print(f"[Ollama] 原始 system_prompt 长度: {len(self.system_prompt)}")
            print(f"[Ollama] 原始 userprompt 长度: {len(userprompt)}")

        # 上下文截断（system + user 合并前先各自截断，简单近似）
        system_prompt = _truncate_text(self.system_prompt, self.max_input_chars // 2)
        userprompt = _truncate_text(userprompt, self.max_input_chars // 2)
        prompt = f"{system_prompt}\n\n{userprompt}"
        if self.debug:
            print(f"[Ollama] 截断后 system_prompt 长度: {len(system_prompt)}")
            print(f"[Ollama] 截断后 userprompt 长度: {len(userprompt)}")
            print(f"[Ollama] 最终提示词长度: {len(prompt)}")

        # 注意：Ollama 的 generate 暂不支持一次返回多条 completion，这里忽略 num_completions>1 的情况
        if self.debug:
            print("[Ollama] 调用 ollama.generate")
        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            options={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
        )

        # 兼容新版 ollama 客户端（返回 pydantic 模型）和旧版（返回 dict）
        if hasattr(response, "model_dump"):
            data = response.model_dump()
        elif isinstance(response, dict):
            data = response
        else:
            # 非预期类型，直接转字符串
            if self.debug:
                print(f"[Ollama] 警告：未知返回类型 {type(response)}, 将直接转为字符串")
            result_text = str(response)
            if self.debug:
                print(f"[Ollama] 返回文本长度: {len(result_text)}")
            return {"role": self.name, "content": result_text}

        if self.debug:
            print("[Ollama] 调用完成，原始返回 keys:", list(data.keys()))

        result_text = data.get("response", "")
        if self.debug:
            print(f"[Ollama] 返回文本长度: {len(result_text)}")
        return {"role": self.name, "content": result_text}