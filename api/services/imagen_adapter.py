from __future__ import annotations
import logging
from typing import List, Optional
from pathlib import Path
from io import BytesIO

logger = logging.getLogger("imagen.adapter")
# lazy imports will be done inside methods to keep server bootable if deps missing

# 采用 Google 官方 SDK（google-genai），与您示例保持一致
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image-preview"


class ImagenAdapter:
    """Wrap Google Gemini image generation/editing via google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY 未配置。请在 .env 或环境变量中设置 GOOGLE_API_KEY")
        self.api_key = api_key
        self.model = model or DEFAULT_IMAGE_MODEL
        self._client = None  # lazy init to avoid hard import at module load

    # ---- Text-to-image ----
    async def generate(self, prompt: str, size: str = "1024x1024", n: int = 1, seed: Optional[int] = None) -> List[bytes]:
        # google-genai 的生成在一个响应中可能混合文本与图片，我们仅提取图片 part
        logger.info("[generate] using model=%s", self.model)
        try:
            # lazy import to keep startup resilient if package is not installed yet
            from google import genai  # type: ignore
            client = self._client or genai.Client(api_key=self.api_key)
            self._client = client
            resp = client.models.generate_content(
                model=self.model,
                contents=[prompt],
            )
            imgs = _extract_images(resp)
            if not imgs:
                logger.warning("[generate] google response had no images extracted")
            else:
                logger.info("[generate] extracted %d image(s) from google response", len(imgs))
            return imgs
        except Exception:
            logger.exception("[generate] google-genai call failed, falling back to empty list")
            # 降级：返回空列表，调用方将处理为占位
            return []

    # ---- Image-to-image edit ----
    async def edit(
        self,
        image_path: Path,
        prompt: str,
        mask_path: Optional[Path] = None,  # 目前示例未使用掩膜，保留参数以兼容接口
        size: str = "1024x1024",
        n: int = 1,
        seed: Optional[int] = None,
    ) -> List[bytes]:
        # 直接将 prompt 与 PIL Image 作为 contents 传入（lazy imports）
        logger.info("[edit] using model=%s, image=%s, prompt_len=%d", self.model, image_path, len(prompt or ""))
        try:
            from PIL import Image as PILImage  # type: ignore
            from google import genai  # type: ignore
            client = self._client or genai.Client(api_key=self.api_key)
            self._client = client
            img = PILImage.open(image_path)
            resp = client.models.generate_content(
                model=self.model,
                contents=[prompt, img],
            )
            imgs = _extract_images(resp)
            if not imgs:
                logger.warning("[edit] google response had no images extracted; prompt sample=%.60s", (prompt or "")[:60])
            else:
                logger.info("[edit] extracted %d image(s) from google response", len(imgs))
            return imgs
        except Exception:
            logger.exception("[edit] google-genai call failed, falling back to original image bytes")
            try:
                with open(image_path, 'rb') as f:
                    data = f.read()
                logger.warning("[edit] FALLBACK used: returning original image bytes (%d bytes)", len(data))
                return [data]
            except Exception:
                logger.exception("[edit] fallback failed to read original image")
                return []

    # ---- Upscale / super-resolution (暂留) ----
    async def upscale(self, image_path: Path, factor: int = 2) -> bytes:
        raise NotImplementedError("upscale 暂未实现")


# ---- helpers ----
def _extract_images(resp) -> List[bytes]:
    images: List[bytes] = []
    # 参考官方示例：从 candidates[0].content.parts 中提取 inline_data
    for cand in getattr(resp, "candidates", []) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None) is not None:
                data = inline.data
                # data 可能是 bytes 或 base64 编码后的 bytes，PIL 可直接识别 bytes
                if isinstance(data, bytes):
                    images.append(data)
                else:
                    # 某些实现返回 memoryview/bytearray
                    images.append(bytes(data))
    return images
