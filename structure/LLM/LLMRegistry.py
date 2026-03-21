from typing import Dict, Type, List, Optional

from .Chatter import Chatter


class LLMRegistry:
    """
    LLM 注册表：统一管理可用的 LLM 适配器（Chatter 子类）。
    上层只需要通过字符串 name 访问，不再直接依赖具体类/实例。
    """

    def __init__(self) -> None:
        # name -> Chatter 子类（类本身，而不是实例）
        self._registry: Dict[str, Type[Chatter]] = {}

    def register(self, name: str, llm_cls: Type[Chatter]) -> None:
        """
        注册一个 LLM 适配器类。

        Args:
            name: 对外暴露的模型名称（如 "deepseek", "ollama", "openai"）
            llm_cls: 继承自 Chatter 的类
        """
        if not name or llm_cls is None:
            return
        self._registry[name] = llm_cls

    def create(self, name: str, **kwargs) -> Chatter:
        """
        通过名称创建一个新的 LLM 实例。

        额外的 **kwargs 会直接传入对应 Chatter 子类的 __init__，
        方便上层在需要时覆盖 model / system_prompt / temperature 等参数。
        """
        if name not in self._registry:
            available = ", ".join(self._registry.keys())
            raise ValueError(f"未在 LLMRegistry 中找到名称为 '{name}' 的模型，可用模型：[{available}]")
        llm_cls = self._registry[name]
        return llm_cls(**kwargs)

    def get_registered_names(self) -> List[str]:
        """返回当前已注册的所有模型名称。"""
        return list(self._registry.keys())

    # ====== 全局访问风格（类似 AgentTailor 的 LLMRegistry.get） ======
    _global_registry: Optional["LLMRegistry"] = None

    @classmethod
    def _get_global_registry(cls) -> "LLMRegistry":
        """
        获取（或懒加载创建）一个全局默认注册表。
        这样上层可以直接使用 LLMRegistry.get("deepseek")，而无需显式传入 registry 实例。
        """
        if cls._global_registry is None:
            cls._global_registry = create_default_llm_registry()
        return cls._global_registry

    @classmethod
    def get(cls, name: str, **kwargs) -> Chatter:
        """
        通过全局默认注册表按名称获取一个 LLM 实例。
        用法示例：
            llm = LLMRegistry.get("deepseek")
        """
        registry = cls._get_global_registry()
        return registry.create(name, **kwargs)


def create_default_llm_registry() -> LLMRegistry:
    """
    创建一个包含内置 LLM 适配器的默认注册表。
    约定的名称：
        - "deepseek"   -> Deepseek
        - "ollama"     -> Ollama
        - "openai"     -> OpenAIChat
        - "blueshirt"  -> BlueShirtChat（默认模型 gpt-4o）
    """
    registry = LLMRegistry()

    # 说明：这些 provider 依赖第三方包（如 openai / ollama）。
    # 为了让“只用其中一个 provider”的场景可运行，这里使用可选导入：
    # - 未安装依赖时：跳过注册，不影响其他 provider 使用
    # - 真正使用缺失 provider 时：create() 会给出明确的 ValueError
    try:
        from .Deepseek import Deepseek  # 依赖 openai 包
        registry.register("deepseek", Deepseek)
    except Exception:
        pass

    try:
        from .Ollama import Ollama  # 依赖 ollama 包
        registry.register("ollama", Ollama)
    except Exception:
        pass

    try:
        from .OpenAI import OpenAIChat  # 依赖 openai 包
        registry.register("openai", OpenAIChat)
    except Exception:
        pass

    try:
        from .BlueShirtChat import BlueShirtChat  # 依赖 openai 包
        registry.register("blueshirt", BlueShirtChat)
        print(f"[LLMRegistry] 成功注册 blueshirt 模型")
    except Exception as e:
        print(f"[LLMRegistry] 警告：注册 blueshirt 模型失败: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[LLMRegistry] 错误堆栈:\n{traceback.format_exc()}")

    return registry
