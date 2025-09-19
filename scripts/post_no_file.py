import httpx
with httpx.Client(trust_env=False) as client:
    r = client.post('http://127.0.0.1:8000/api/jobs', data={'type':'enhance','params':'{}'})
    print('status', r.status_code)
print(r.text[:500])

