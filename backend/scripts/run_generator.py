import urllib.request, json
BASE = 'http://127.0.0.1:8000/api/v1'

def call(method, url, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token: headers['Authorization'] = 'Bearer ' + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=180)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, 'binary'

s, res = call('POST', BASE + '/auth/login', {'email':'admin@aviu.ac.ug','password':'admin123'})
print('LOGIN:', s)
if s != 200:
    print(res)
    raise SystemExit(1)
t = res['access_token']

s, acts = call('GET', BASE + '/activities', token=t)
print('Activities:', s, '| count:', len(acts) if isinstance(acts, list) else acts)

print()
print('Calling POST /generation/generate ...')
body = {
    'intake': 'Aug',
    'academic_year': '2026/2027',
    'semester': 1,
    'run_type': 'teaching',
}
s, run = call('POST', BASE + '/generation/generate', body, token=t)
print('Status:', s)
print('Response:', json.dumps(run, indent=2)[:800])

s, runs = call('GET', BASE + '/generation/runs', token=t)
print()
print('Runs after generation:', s, '| count:', len(runs) if isinstance(runs, list) else runs)
if isinstance(runs, list) and runs:
    for r in runs[:3]:
        print('  run', r.get('id'), '| status =', r.get('status'), '| msg =', (r.get('message') or '')[:80])