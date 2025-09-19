from __future__ import annotations
import json
import threading
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("imagen.tasks")
from .storage import job_json_path, RESULTS_DIR, result_url, save_bytes
from .config import settings
from .services.imagen_adapter import ImagenAdapter
from .services.proxy_adapter import ProxyAdapter
from .services.prompts import TEMPLATES, build_prompt, HAIRSTYLES


def _update(job_id: str, **patch: Any) -> Dict[str, Any]:
    p = job_json_path(job_id)
    data = json.loads(p.read_text(encoding="utf-8"))
    data.update(patch)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def _load(job_id: str) -> Dict[str, Any]:
    p = job_json_path(job_id)
    return json.loads(p.read_text(encoding="utf-8"))


# Background worker without Celery (dev-friendly)
def process_job_background(job_id: str) -> None:
    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    t.start()


def _run_job(job_id: str) -> None:
    try:
        _update(job_id, status="running", progress=5)
        data = _load(job_id)
        job_type = data.get("type")
        params: Dict[str, Any] = data.get("params") or {}
        input_path = Path(data.get("input_path"))
        logger.info("[job %s] start type=%s input=%s params=%s", job_id, job_type, input_path, params)

        # Dispatch to async pipeline
        results = asyncio.run(_execute(job_id, job_type, input_path, params))
        logger.info("[job %s] pipeline returned %d image(s)", job_id, len(results or []))

        _update(job_id, progress=95)
        # Save results to disk
        out_dir = RESULTS_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        urls: List[str] = []
        for i, img_bytes in enumerate(results, start=1):
            out_img = out_dir / f"result_{i}.png"
            save_bytes(img_bytes, out_img)
            urls.append(result_url(out_img))

        _update(job_id, status="finished", progress=100, results=urls)
        logger.info("[job %s] finished with %d outputs", job_id, len(urls))
    except Exception as e:
        logger.exception("[job %s] failed: %s", job_id, e)
        _update(job_id, status="failed", error=str(e))


async def _execute(job_id: str, job_type: str, image_path: Path, params: Dict[str, Any]) -> List[bytes]:
    # Choose provider
    if settings.PROVIDER.lower() == "proxy":
        model = (settings.PROXY_MODEL or settings.GOOGLE_IMAGE_MODEL)
        adapter = ProxyAdapter(api_key=(settings.PROXY_API_KEY or ""), base_url=settings.PROXY_BASE_URL, model=model)
        provider_desc = f"proxy base={settings.PROXY_BASE_URL} model={model}"
    else:
        adapter = ImagenAdapter(api_key=settings.GOOGLE_API_KEY, model=settings.GOOGLE_IMAGE_MODEL)
        provider_desc = f"google model={settings.GOOGLE_IMAGE_MODEL}"

    size = params.get("size", "1024x1024")
    n = int(params.get("n", 1))
    seed = params.get("seed")
    logger.info("[job %s] execute type=%s provider=%s size=%s n=%s seed=%s", job_id, job_type, provider_desc, size, n, seed)

    if job_type == "figurine":
        prompt = build_prompt(TEMPLATES["figurine"], params)
        imgs = await adapter.edit(image_path, prompt, size=size, n=n, seed=seed)
        logger.info("[job %s] figurine -> %d image(s)", job_id, len(imgs or []))
        return imgs

    if job_type == "era_style":
        prompt = build_prompt(TEMPLATES["era_style"], params)
        imgs = await adapter.edit(image_path, prompt, size=size, n=n, seed=seed)
        logger.info("[job %s] era_style -> %d image(s)", job_id, len(imgs or []))
        return imgs

    if job_type == "enhance":
        prompt = build_prompt(TEMPLATES["enhance"], params)
        imgs = await adapter.edit(image_path, prompt, size=size, n=n, seed=seed)
        logger.info("[job %s] enhance -> %d image(s)", job_id, len(imgs or []))
        return imgs

    if job_type == "old_photo_restore":
        prompt = build_prompt(TEMPLATES["old_photo_restore"], params)
        imgs = await adapter.edit(image_path, prompt, size=size, n=n, seed=seed)
        logger.info("[job %s] old_photo_restore -> %d image(s)", job_id, len(imgs or []))
        return imgs

    if job_type == "id_photo":
        prompt = build_prompt(TEMPLATES["id_photo"], params)
        imgs = await adapter.edit(image_path, prompt, size=size, n=n, seed=seed)
        logger.info("[job %s] id_photo -> %d image(s)", job_id, len(imgs or []))
        return imgs

    if job_type == "hairstyle_grid":
        # 逐个发型生成，收集 9 张
        results: List[bytes] = []
        for name in HAIRSTYLES:
            hair_prompt = f"为此人更换为{name}发型，保持脸部特征不变，正面头像构图，均匀光线，背景干净，高分辨率。"
            prompt = build_prompt(hair_prompt, params)
            imgs = await adapter.edit(image_path, prompt, size=size, n=1, seed=seed)
            logger.info("[job %s] hairstyle %s -> %d image(s)", job_id, name, len(imgs or []))
            if imgs:
                results.append(imgs[0])
        logger.info("[job %s] hairstyle_grid total -> %d image(s)", job_id, len(results))
        return results

    # default fallback: return original via no-op edit prompt to keep pipeline stable
    prompt = "Keep the image, minor enhance for clarity."
    return await adapter.edit(image_path, prompt, size=size, n=1, seed=seed)

