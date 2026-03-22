import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件中的环境变量
load_dotenv()




def chat_with_blueshirt(
    model: str,
    systemprompt: str,
    userprompt: str,
    stream: bool,
    *,
    temperature: float,
    top_p: float,
    num_completions: int,
    max_input_chars: int,
) -> str:
    """
    使用 BlueShirt 提供的 OpenAI 兼容接口进行对话。
    通过环境变量配置：
      - BLUESHIRT_API      ：API Key
      - BLUESHIRT_BASE_URL ：API base url，例如 https://api.blueshirt.ai
    """
    api_key = os.environ.get("BLUESHIRT_API")
    base_url = os.environ.get("BLUESHIRT_BASE_URL", "")
    
    if not api_key:
        raise ValueError("环境变量 BLUESHIRT_API 未设置")
    if not base_url:
        raise ValueError("环境变量 BLUESHIRT_BASE_URL 未设置")
    
    # OpenAI 客户端期望 base_url 包含 /v1 路径
    # 如果用户提供的 base_url 不包含 /v1，自动添加
    base_url = base_url.rstrip("/")  # 移除末尾的斜杠
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"
    
    # 打印调试信息（不打印完整 API key）
    print(f"[BlueShirtChat] 使用模型: {model}, Base URL: {base_url}, Stream: {stream}")
    
    # 设置超时时间（默认 60 秒，对于复杂任务可以更长）
    timeout = float(os.environ.get("BLUESHIRT_TIMEOUT", "120.0"))
    
    import httpx
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=httpx.Timeout(timeout, connect=30.0),  # 连接超时30秒，总超时120秒
    )

    # 重试机制
    max_retries = int(os.environ.get("BLUESHIRT_MAX_RETRIES", "2"))
    retry_delay = float(os.environ.get("BLUESHIRT_RETRY_DELAY", "2.0"))
    
    import time
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            # 如果 stream=True，需要特殊处理
            if stream:
                # 流式响应处理
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
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            full_content += delta.content
                
                if not full_content:
                    raise ValueError("BlueShirt API 流式响应为空")
                return full_content
            else:
                # 非流式响应处理
                resp = client.chat.completions.create(
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
            
            # 检查响应类型：如果返回的是字符串，说明可能是错误消息或 HTML 页面
            if isinstance(resp, str):
                # 如果是 HTML，说明 URL 可能不正确
                if resp.strip().startswith("<!DOCTYPE") or resp.strip().startswith("<html"):
                    raise ValueError(
                        f"BlueShirt API 返回了 HTML 页面而不是 JSON 响应。\n"
                        f"这可能是因为 Base URL 不正确。\n"
                        f"当前 Base URL: {base_url}\n"
                        f"请确保 Base URL 指向正确的 API 端点（通常以 /v1 结尾）。\n"
                        f"响应前200字符: {resp[:200]}"
                    )
                else:
                    raise ValueError(f"BlueShirt API 返回了字符串响应（可能是错误）: {resp[:500]}")
            
            # 检查响应对象是否有 choices 属性
            if not hasattr(resp, 'choices'):
                raise ValueError(f"BlueShirt API 返回了无效的响应类型: {type(resp)}, 内容: {str(resp)[:500]}")
            
            if not resp.choices:
                raise ValueError("BlueShirt API 返回空响应（choices 为空）")
            
            content = resp.choices[0].message.content
            if content is None:
                raise ValueError("BlueShirt API 返回的 content 字段为空")
            
            return content
        except ValueError as e:
            # ValueError 直接抛出（这些是我们自己定义的错误）
            raise
        except Exception as e:
            last_error = e
            error_msg = str(e)
            error_type = type(e).__name__
            
            # 打印详细的错误信息用于调试
            print(f"[BlueShirtChat] API 调用异常 (尝试 {attempt + 1}/{max_retries + 1}): {error_type}: {error_msg}")
            
            # 对于超时错误，进行重试
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower() or "APITimeoutError" in error_type:
                if attempt < max_retries:
                    print(f"[BlueShirtChat] 检测到超时错误，{retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"[BlueShirtChat] 达到最大重试次数，放弃重试")
            
            # 对于其他错误，如果是最后一次尝试，则抛出
            if attempt >= max_retries:
                print(f"[BlueShirtChat] API Key 前10字符: {api_key[:10] if api_key else 'None'}...")
                print(f"[BlueShirtChat] Base URL: {base_url}")
                
                if "Internal Server Error" in error_msg or "500" in error_msg:
                    raise RuntimeError(f"BlueShirt API 服务器错误: {error_msg}")
                elif "401" in error_msg or "Unauthorized" in error_msg:
                    raise ValueError(f"BlueShirt API 认证失败: 请检查 BLUESHIRT_API 是否正确")
                elif "404" in error_msg or "Not Found" in error_msg:
                    raise ValueError(f"BlueShirt API 端点不存在: 请检查 BLUESHIRT_BASE_URL 是否正确")
                else:
                    raise RuntimeError(f"BlueShirt API 调用失败 ({error_type}): {error_msg}")
            else:
                # 其他错误也重试一次
                print(f"[BlueShirtChat] 其他错误，{retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                continue
    
    # 如果所有重试都失败，抛出最后一个错误
    if last_error:
        raise last_error
    raise RuntimeError("BlueShirt API 调用失败：未知错误")




