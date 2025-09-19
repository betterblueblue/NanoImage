from __future__ import annotations
import base64
import logging
from pathlib import Path
from typing import List, Optional

import httpx

logger = logging.getLogger("imagen.proxy_adapter")


class ProxyAdapter:
    """
    老张API（OpenAI 兼容）适配器：使用 /v1/chat/completions 进行图像编辑/生成。
    - 模型：gemini-2.5-flash-image-preview（支持文生图/图像编辑）
    - 请求格式：messages[{ role: 'user', content: [ {type: 'text'}, {type: 'image_url'}... ] }]
    - 返回：message.content 中包含 data:image/...;base64,xxx 的字符串
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        if not api_key:
            raise ValueError("PROXY_API_KEY 未配置")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def edit(
        self,
        image_path: Path,
        prompt: str,
        mask_path: Optional[Path] = None,
        size: str = "1024x1024",
        n: int = 1,
        seed: Optional[int] = None,
    ) -> List[bytes]:
        # 将输入图片转为 data URL，作为 image_url 传给 /v1/chat/completions
        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            data_url = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
        except Exception:
            logger.exception("[proxy/edit] 读取输入图片失败: %s", image_path)
            return []

        if mask_path:
            logger.info("[proxy/edit] mask 参数暂未被老张API使用，将忽略 mask=%s", mask_path)

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or "Edit this image"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        logger.info("[proxy/edit] url=%s model=%s (using chat.completions)", url, self.model)

        try:
            async with httpx.AsyncClient(timeout=180, trust_env=False) as client:
                resp = await client.post(url, headers=headers, json=body)
            if resp.status_code != 200:
                logger.error("[proxy/edit] http %s: %s", resp.status_code, resp.text[:800])
                return []
            payload = resp.json()
            # 解析 choices[0].message.content 字符串中的 base64 图片
            text = (
                (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content")
            ) or ""
            if not text:
                logger.warning("[proxy/edit] 响应无 content 字段")
                return []

            import re
            m = re.search(r"data:image/([a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=]+)", text)
            if not m:
                logger.warning("[proxy/edit] 未发现 base64 图片数据，content 前200字: %s", text[:200])
                return []
            b64_data = m.group(2)
            try:
                img_out = base64.b64decode(b64_data)
                logger.info("[proxy/edit] 提取到 1 张图片 (%d bytes)", len(img_out))
                return [img_out]
            except Exception:
                logger.exception("[proxy/edit] base64 解码失败")
                return []
        except Exception:
            logger.exception("[proxy/edit] 请求失败")
            return []

