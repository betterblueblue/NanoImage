from __future__ import annotations
from pathlib import Path
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

from .config import settings
from .routes.jobs import router as jobs_router
from .storage import BASE_DIR

app = FastAPI(title="NanoImage API", version="0.1.0")

# CORS (dev permissive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(jobs_router)

# Static files: serve storage as /files
app.mount("/files", StaticFiles(directory=str(BASE_DIR), html=False), name="files")

# Serve web frontend from /web to avoid overshadowing /api and /health

# Startup config logging (masked API key)
@app.on_event("startup")
async def _log_config_on_startup():
    logger = logging.getLogger("imagen.config")
    key = settings.GOOGLE_API_KEY or ""
    masked = f"{key[:6]}...{key[-4:]}" if key else "<EMPTY>"
    in_env = "yes" if "GOOGLE_API_KEY" in os.environ else "no"
    msg1 = f"Config: GOOGLE_IMAGE_MODEL={settings.GOOGLE_IMAGE_MODEL}"
    msg2 = f"Config: GOOGLE_API_KEY masked={masked} len={len(key)} in_env={in_env}"
    logger.info(msg1)
    logger.info(msg2)
    # also print to stdout to ensure visibility under any logger config
    print(msg1)
    print(msg2)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

# Serve README.md at root for "项目说明" link
README_PATH = Path(__file__).resolve().parent.parent / "README.md"

@app.get("/README.md")
def get_readme():
    if README_PATH.exists():
        # 返回为 text/markdown，浏览器会直接显示文本（不强制下载）
        return FileResponse(str(README_PATH), media_type="text/markdown; charset=utf-8")
    return PlainTextResponse("README not found", status_code=404)


@app.get("/readme")
def readme_html():
    # fallback inline HTML when web/readme.html is missing
    HTML_README = WEB_DIR / "readme.html"
    if HTML_README.exists():
        return FileResponse(str(HTML_README), media_type="text/html; charset=utf-8")









    html = """
<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>项目说明 · README</title>
  <link rel=\"preconnect\" href=\"https://cdn.jsdelivr.net\" />
  <style>body{{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;max-width:900px;margin:24px auto;padding:0 16px;color:#0f172a;}}
  #md{{line-height:1.65;}}
  #md h1,#md h2,#md h3{{border-bottom:1px solid #e5e7eb;padding-bottom:.3rem;}}
  #md pre{{background:#0b1220;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto}}
  #md code{{background:#f1f5f9;padding:2px 6px;border-radius:4px}}
  a{{color:#2563eb}}</style>
</head>
<body>
  <a href=\"/web/\">← 返回上传页</a>
  <div id=\"md\">加载中...</div>
  <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>
  <script>
    fetch('/README.md').then(r=>r.text()).then(t=>{
      const html = marked.parse(t);
      document.getElementById('md').innerHTML = html;
    }).catch(()=>{document.getElementById('md').textContent='README 加载失败';});
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")



@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/ping")
def ping():
    return {"ok": True}

