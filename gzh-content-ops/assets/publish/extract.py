import re, html, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def extract(path):
    data = open(path, encoding='utf-8', errors='ignore').read()
    out = {}
    m = re.search(r'<title[^>]*>(.*?)</title>', data, re.S)
    out['title'] = html.unescape(m.group(1)).strip() if m else ''
    nick = ''
    m = re.search(r'var\s+nickname\s*=\s*(?:htmlDecode\()?["\']([^"\']*)["\']', data)
    if m:
        nick = m.group(1)
    else:
        m = re.search(r'id="js_name"[^>]*>(.*?)</a>', data, re.S)
        if m:
            nick = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    out['nickname'] = nick
    m = re.search(r'var\s+user_name\s*=\s*["\']([^"\']*)["\']', data)
    out['account'] = m.group(1) if m else ''
    m = re.search(r'var\s+createTime\s*=\s*["\']?(\d+)', data)
    out['createTime'] = m.group(1) if m else ''
    out['original'] = ('原创' in data)
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*)', data, re.S)
    body = m.group(1) if m else ''
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    body = re.sub(r'<[^>]+>', '\n', body)
    body = html.unescape(body)
    body = re.sub(r'[ \t]+', ' ', body)
    body = re.sub(r'\n\s*\n+', '\n', body)
    out['body'] = body.strip()
    return out

for p in sys.argv[1:]:
    r = extract(p)
    print('=' * 70)
    print('FILE:', p)
    print('NICKNAME:', r['nickname'], '| ACCOUNT:', r['account'])
    print('TITLE:', r['title'])
    print('ORIGINAL(原创):', r['original'])
    print('-' * 70)
    print(r['body'][:4000])
    print()
