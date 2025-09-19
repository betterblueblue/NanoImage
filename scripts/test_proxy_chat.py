import os, json, argparse
import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base", default=os.getenv("PROXY_BASE", "https://api.laozhang.ai"))
parser.add_argument("--key", default=os.getenv("LAOZHANG_API_KEY", ""))
parser.add_argument("--model", default=os.getenv("PROXY_MODEL", "gemini-2.5-flash-image-preview"))
args = parser.parse_args()

if not args.key:
    raise SystemExit("Provide --key or set LAOZHANG_API_KEY in env")

url = f"{args.base.rstrip('/')}/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {args.key}",
    "Content-Type": "application/json",
}

payload = {
    "model": args.model,
    "messages": [
        {"role": "user", "content": "write a haiku about ai"}
    ]
}

with httpx.Client(timeout=30, trust_env=False) as client:
    r = client.post(url, headers=headers, json=payload)
    print("status:", r.status_code)
    print("raw:", r.text[:800])
    try:
        data = r.json()
        c0 = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        if c0:
            print("message:", c0)
    except Exception:
        pass

