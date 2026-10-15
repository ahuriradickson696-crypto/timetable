import urllib.request, urllib.error, json
BASE = 'http://127.0.0.1:8000/api/v1'

def call(method, url, body=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token: headers['Authorization'] = 'Bearer ' + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except: return e.code, 'binary'
    except Exception as e: return 0, str(e)

# Login as the demo lecturer
s, res = call('POST', BASE + '/auth/login', {'email':'lecturer1@aviu.ac.ug','password':'lecturer123'})
print('LOGIN:', s)
if s != 200:
    print(res); raise SystemExit(1)
t = res['access_token']
print()

# What can a lecturer see?
tests = [
    ('GET', '/auth/me'),
    ('GET', '/portal/me'),
    ('GET', '/portal/my-timetable'),
    ('GET', '/portal/my-next-class'),
    ('GET', '/portal/my-today'),
    ('GET', '/portal/my-exams'),
    ('GET', '/notifications/me'),
    ('GET', '/account/me'),
]
print('{:6} {:30} {:6} {}'.format('METHOD', 'ENDPOINT', 'STATUS', 'PREVIEW'))
print('-' * 100)
for method, path in tests:
    s, r = call(method, BASE + path, token=t)
    if isinstance(r, list): preview = 'list len=' + str(len(r))
    elif isinstance(r, dict): preview = json.dumps(r)[:70]
    else: preview = str(r)[:70]
    marker = ' <-- FIX' if s != 200 else ''
    print('{:6} {:30} {:6} {}{}'.format(method, path, s, preview, marker))

# Full /portal/me to check lecturer_id is linked
print()
print('=== Full /portal/me ===')
s, r = call('GET', BASE + '/portal/me', token=t)
print(json.dumps(r, indent=2))