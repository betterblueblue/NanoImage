# NanoImage — 基于 Google Gemini API Imagen 的图片编辑网站（骨架）

本仓库包含：
- 后端（FastAPI）：`api/`，提供任务创建/查询接口，存储上传与结果，内置简易后台任务（可替换为 Celery）
- 前端（静态页先行）：`web/`，支持上传、选择功能、发起任务、轮询进度与展示结果网格
- 本地存储目录：`storage/`（运行后自动创建）

注意：当前未集成真实的 Google Imagen 调用，`api/services/imagen_adapter.py` 为占位接口，`api/tasks.py` 目前仅复制输入图作为占位结果。后续可按 README 指引接入官方 API。

## 目录结构
```
NanoImage/
  api/
    app.py                # FastAPI 入口
    config.py             # 配置加载
    models.py             # Pydantic 模型
    storage.py            # 本地文件存取 & URL 映射
    tasks.py              # 后台任务（占位，后续可替换 Celery）
    routes/
      jobs.py             # /api/jobs 接口
    services/
      imagen_adapter.py   # Imagen 适配器（待接入）
  web/
    index.html            # 静态前端
    app.js
    styles.css
  storage/                # 运行时生成
  README.md
```


## 快速启动（推荐：走老张代理 · Nano Banana 模型）
本项目已内置对“老张 OpenAI 兼容代理”的集成，默认模型为 `gemini-2.5-flash-image-preview`。

1) 准备环境（Python 3.10+）并安装依赖：
```
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install fastapi uvicorn[standard] pydantic python-multipart pillow httpx tenacity
```

2) 配置 .env（示例）：
```
# 使用代理
PROVIDER=proxy
PROXY_BASE_URL=https://api.laozhang.ai
PROXY_API_KEY=你的代理Key
PROXY_MODEL=gemini-2.5-flash-image-preview

# 可选：禁用失败回退（失败时不返回原图，直接报错）
IMAGEN_DISABLE_FALLBACK=false
```
> 如果想走官方通道，把 `PROVIDER` 改为 `google`，并设置 `GOOGLE_API_KEY`。

3) 启动服务：
```
python -m uvicorn api.app:app --port 8000
```
常用地址：
- 上传测试页：http://localhost:8000/web/
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 结果文件：http://localhost:8000/files/results/<job_id>/result_1.png

4) 一键冒烟测试（可选）：
```
python scripts/smoke_test.py
```
脚本会自动创建任务并轮询直至完成，终端输出最终图片地址。

### 常见问题
- 打开 http://localhost:8000 显示 `{"detail":"Not Found"}`？请访问 `/web/` 或 `/docs`。
- 端口被占用？改用 `--port 8080`，并在浏览器用 `http://localhost:8080/web/`。
- 结果为空或报 400？确认 `.env` 中代理 Key 与模型名正确；我们已适配老张的 `chat/completions` 图像编辑调用方式。
- 局域网其他设备访问？把地址里的 `localhost` 改为本机局域网 IP，并在系统防火墙放行相应端口。

## 运行（开发）
1) 创建虚拟环境并安装依赖（示例，以 pip 为例）：
```
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install fastapi uvicorn[standard] pydantic python-multipart pillow httpx tenacity
```
> 说明：此处仅给出命令建议，遵循“使用包管理器”的原则；如需我自动执行，请明确授权。

2) 启动 API：
```
python -m uvicorn api.app:app --reload --port 8000
```
访问健康检查：http://localhost:8000/health

3) 打开前端页面（方法其一）
- 直接用 VSCode Live Server 打开 `web/index.html`
- 或将 `web/` 挂到任意静态服务器

4) 体验流程
- 前端选择功能 + 上传图片 → 发起任务
- 后台当前会“占位”处理（约 1 秒）→ 返回结果网格

## 接入 Google Gemini API Imagen（后续）
1) 将 API Key 写入环境变量（建议 `.env`）：
```
GOOGLE_API_KEY=your_key_here
```

2) 在 `api/services/imagen_adapter.py` 中实现：
- `edit(image_path, prompt, mask_path, size, n, seed)` → 调用 `imagen-3.0-edit-001`
- `generate(prompt, size, n, seed)` → 调用生成模型（可选）
- `upscale(image_path, factor)` → 调用超分模型（可选）

3) 在 `api/tasks.py` 的 `_run_job()` 里：
- 根据 `job_type` 构造提示词（六大功能的模板），调用 `ImagenAdapter`
- 将返回的图片字节写入 `storage/results/{job_id}/result_*.png`

> 如需长耗时与批量稳定处理，建议引入 Celery + Redis，将 `process_job_background` 替换为 Celery 任务。

## 六大功能与提示词（草稿）
- 插画转手办：强调“盒子+Blender屏幕+圆形底座+室内布光”，并加入负面提示“无水印/文字/畸形”。
- 时代风格转换：参数化年代、性别风格、发型特征、面部特征、时代背景，强调“保留面部特征与身份”。
- 智能修图增强：适度增强对比/色彩/光线且“不过度饱和”，允许小幅裁剪删除干扰元素。
- 发型试换（九宫格）：逐张生成不同发型更稳定，后端将 9 张拼为网格。
- 老照片修复上色：修复划痕噪点并自然上色，保持时代质感与面部细节。
- 证件照制作：蓝底、正装、正脸、微笑；后处理裁切到 2 寸常用 413×531。

## 下一步
- [ ] 接入 Imagen 实际 API 调用
- [ ] 为“发型九宫格”添加后端拼图逻辑
- [ ] 增加 SSE 推进度（或 WebSocket）
- [ ] 切换到 Celery + Redis（生产可扩展）
- [ ] 升级前端为 Next.js + shadcn/ui（更美观与可扩展）

