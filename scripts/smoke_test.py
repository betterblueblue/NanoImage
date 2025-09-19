import time
import json
from pathlib import Path
import httpx
from PIL import Image, ImageDraw

BASE = "http://127.0.0.1:8000"
TMP = Path("scripts/tmp")
TMP.mkdir(parents=True, exist_ok=True)
IMG = TMP / "test.png"

# generate a simple test image
if not IMG.exists():
    im = Image.new("RGB", (256, 256), (240, 240, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([32, 32, 224, 224], outline=(50, 120, 220), width=6)
    d.text((60, 115), "NanoImage", fill=(20, 20, 20))
    im.save(IMG)

with httpx.Client(trust_env=False) as client:
    files = {"file": (IMG.name, IMG.read_bytes(), "image/png")}
    data = {"type": "enhance", "params": json.dumps({"size": "512x512", "n": 1})}
    r = client.post(f"{BASE}/api/jobs", files=files, data=data)
    print("POST /api/jobs ->", r.status_code, r.text[:500])
    r.raise_for_status()
    job_id = r.json()["job_id"]
    print("job_id:", job_id)

    for _ in range(60):
        s_resp = client.get(f"{BASE}/api/jobs/{job_id}")
        print("GET /api/jobs/{job_id} ->", s_resp.status_code)
        s = s_resp.json()
        print("status:", s["status"], "progress:", s.get("progress"))
        if s["status"] in ("finished", "failed"):
            print("final:", s)
            break
        time.sleep(1)

