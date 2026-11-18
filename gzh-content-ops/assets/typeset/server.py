#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归藏排版工具 — 公众号排版器
双击启动 → 浏览器打开 → 左边写文章 → 右边预览 → 点复制 → 去公众号 Ctrl+V
"""

import os, sys, json, threading, webbrowser, http.server, socketserver, subprocess, time, socket, re
from urllib.parse import urlparse
import ctypes, ctypes.wintypes

# ═══════════════════════════════════════════
# Win32 Clipboard API
# ═══════════════════════════════════════════
HGLOBAL, UINT, SIZE_T, LPVOID, HANDLE, HWND, BOOL, DWORD = \
    ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_ulong
k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32

k32.GlobalAlloc.argtypes, k32.GlobalAlloc.restype = [UINT, SIZE_T], HGLOBAL
k32.GlobalLock.argtypes, k32.GlobalLock.restype = [HGLOBAL], LPVOID
k32.GlobalUnlock.argtypes, k32.GlobalUnlock.restype = [HGLOBAL], BOOL
k32.GlobalFree.argtypes, k32.GlobalFree.restype = [HGLOBAL], HGLOBAL
u32.RegisterClipboardFormatW.argtypes, u32.RegisterClipboardFormatW.restype = [ctypes.wintypes.LPCWSTR], UINT
u32.OpenClipboard.argtypes, u32.OpenClipboard.restype = [HWND], BOOL
u32.EmptyClipboard.argtypes, u32.EmptyClipboard.restype = [], BOOL
u32.SetClipboardData.argtypes, u32.SetClipboardData.restype = [UINT, HANDLE], HANDLE
u32.CloseClipboard.argtypes, u32.CloseClipboard.restype = [], BOOL
k32.GetLastError.argtypes, k32.GetLastError.restype = [], DWORD

def win32e(msg): return OSError(f'{msg} (错误码: {k32.GetLastError()})')

def copy_html(html: str):
    """写 CF_HTML 到剪贴板，公众号后台 Ctrl+V 保留样式"""
    fmt = u32.RegisterClipboardFormatW("HTML Format")
    if not fmt: raise win32e("注册剪贴板格式失败")

    prefix = b'<!DOCTYPE html><html><body><!--StartFragment-->'
    suffix = b'<!--EndFragment--></body></html>'
    body = html.encode('utf-8')
    html_part = prefix + body + suffix

    hdr = 'Version:1.0\r\nStartHTML:0000000000\r\nEndHTML:0000000000\r\nStartFragment:0000000000\r\nEndFragment:0000000000\r\n'
    hdr_size = len(hdr.encode('utf-8'))
    hdr2 = f'Version:1.0\r\nStartHTML:{hdr_size:010d}\r\nEndHTML:{hdr_size+len(html_part):010d}\r\nStartFragment:{hdr_size+len(prefix):010d}\r\nEndFragment:{hdr_size+len(prefix)+len(body):010d}\r\n'
    data = hdr2.encode('utf-8') + html_part

    GMEM = 0x0002 | 0x0040
    hmem = k32.GlobalAlloc(GMEM, len(data) + 2)
    if not hmem: raise win32e("GlobalAlloc 失败")
    try:
        ptr = k32.GlobalLock(hmem)
        if not ptr: raise win32e("GlobalLock 失败")
        try: ctypes.memmove(ptr, data, len(data))
        finally: k32.GlobalUnlock(hmem)
        if not u32.OpenClipboard(None): raise win32e("OpenClipboard 失败")
        try:
            u32.EmptyClipboard()
            if not u32.SetClipboardData(fmt, hmem): raise win32e("SetClipboardData 失败")
            hmem = None
        finally: u32.CloseClipboard()
    finally:
        if hmem: k32.GlobalFree(hmem)

# ═══════════════════════════════════════════
# Markdown → 公众号 HTML
# ═══════════════════════════════════════════
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def inline(s):
    r = esc(s)
    r = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#fff;font-weight:700;">\1</strong>', r)
    r = re.sub(r'\{红(.+?)\}', r'<span style="color:#E53935;font-weight:600;">\1</span>', r)
    r = re.sub(r'\{绿(.+?)\}', r'<span style="color:#43A047;font-weight:600;">\1</span>', r)
    r = re.sub(r'`([^`]+)`', r'<code style="font-family:Courier New,monospace;font-size:13px;padding:1px 5px;background:#222228;border-radius:3px;color:#43A047;">\1</code>', r)
    return r

def convert(text):
    if not text.strip(): return ''
    lines = text.split('\n')
    parts, i, n = [], 0, len(lines)
    while i < n:
        t = lines[i].strip()
        if not t: i+=1; continue
        if re.match(r'^---+$', t):
            parts.append('<p style="margin:1.4em 0;text-align:center;color:#8888A0;letter-spacing:6px;font-size:14px;opacity:.3;">◆ ◆ ◆</p>')
            i+=1; continue
        m = re.match(r'^#\s+(.+)', t)
        if m: parts.append(f'<h2 style="font-size:18px;font-weight:700;color:#fff;margin:1.4em 0 .5em;padding-left:12px;border-left:3px solid #E53935;line-height:1.4;">{inline(m.group(1))}</h2>'); i+=1; continue
        m = re.match(r'^##\s+(.+)', t)
        if m: parts.append(f'<h3 style="font-size:16px;font-weight:700;color:#fff;margin:1.2em 0 .4em;">{inline(m.group(1))}</h3>'); i+=1; continue
        if t.startswith('> '):
            q=[]
            while i<n and lines[i].strip().startswith('> '): q.append(lines[i].strip()[2:]); i+=1
            parts.append(f'<blockquote style="margin:1em 0;padding:14px 16px;background:#1A1A1E;border-left:3px solid #7C4DFF;border-radius:0 8px 8px 0;font-size:14px;line-height:1.7;color:#8888A0;">{inline("\n".join(q))}</blockquote>')
            continue
        if t.startswith('```'):
            i+=1; c=[]
            while i<n and not lines[i].strip().startswith('```'): c.append(lines[i]); i+=1
            i+=1
            parts.append(f'<pre style="margin:1em 0;padding:14px 16px;background:#222228;border-radius:8px;border:1px solid rgba(255,255,255,.06);font-family:Courier New,monospace;font-size:13px;line-height:1.6;color:#b0b0c0;white-space:pre-wrap;overflow-x:auto;">{esc("\n".join(c).rstrip())}</pre>')
            continue
        para=[]
        while i<n:
            x=lines[i].strip()
            if not x or x.startswith('#') or x.startswith('> ') or x.startswith('```') or re.match(r'^---+$',x): break
            para.append(lines[i]); i+=1
        p='\n'.join(para).strip()
        if not p: continue
        if re.match(r'^[-*]\s', p):
            items=re.findall(r'^[-*]\s+(.+)$', p, re.MULTILINE)
            lis='\n'.join(f'<li style="margin-bottom:.3em;">{inline(it)}</li>' for it in items)
            parts.append(f'<ul style="margin:.6em 0;padding-left:1.5em;font-size:15px;line-height:1.75;color:#d0d0d8;">{lis}</ul>')
        else:
            parts.append(f'<p style="font-size:15px;line-height:1.75;color:#d0d0d8;margin-bottom:1em;text-align:justify;">{inline(p)}</p>')
    inner='\n'.join(parts)
    return f'<section style="padding:0 8px;max-width:100%;background:#0a0a0e;color:#d0d0d8;font-size:15px;line-height:1.75;letter-spacing:.5px;">\n{inner}\n</section>'

# ═══════════════════════════════════════════
# 前端 HTML（内嵌）
# ═══════════════════════════════════════════
INDEX_HTML = r'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>归藏排版工具</title>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0D0D0F;--surface:#141418;--card:#1A1A1E;--border:rgba(255,255,255,.08);--text:#E8E8EA;--dim:#8888A0;--red:#E53935;--green:#43A047;--purple:#7C4DFF}
body{background:var(--bg);color:var(--text);font-family:'Microsoft YaHei UI','PingFang SC',sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.topbar{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;flex-wrap:wrap;gap:8px}
.logo{font-size:18px;font-weight:900}.logo span{color:var(--red)}
.actions{display:flex;gap:6px}
.actions button{padding:6px 14px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:13px;cursor:pointer;font-family:inherit}
.actions button:hover{background:#2a2a30}
.actions .copy-btn{background:var(--red);border-color:var(--red);color:#fff;min-width:120px}
.main{flex:1;display:flex;min-height:0}
.left{width:50%;display:flex;flex-direction:column;border-right:1px solid var(--border)}
.left textarea{flex:1;border:none;outline:none;background:var(--bg);color:var(--text);font-size:14px;line-height:1.9;padding:18px;font-family:'Microsoft YaHei UI','PingFang SC',sans-serif;resize:none}
.right{width:50%;display:flex;flex-direction:column;background:var(--surface)}
.preview{flex:1;overflow-y:auto;padding:20px 24px;background:#0a0a0e}
.preview::-webkit-scrollbar{width:4px}
.preview::-webkit-scrollbar-thumb{background:#222;border-radius:2px}
.phdr{padding:6px 16px;font-size:11px;color:var(--dim);background:var(--surface);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;flex-shrink:0}
.r-h2{font-size:18px;font-weight:700;color:#fff;margin:1.2em 0 .4em;padding-left:12px;border-left:3px solid var(--red);line-height:1.4}
.r-h3{font-size:16px;font-weight:700;color:#fff;margin:1em 0 .3em}
.r-text{font-size:15px;line-height:1.75;color:#d0d0d8;margin-bottom:1em;text-align:justify}
.r-bold{font-weight:700;color:#fff}
.r-red{color:var(--red);font-weight:600}
.r-green{color:var(--green);font-weight:600}
.r-quote{margin:1em 0;padding:12px 16px;background:var(--card);border-left:3px solid var(--purple);border-radius:0 6px 6px 0;font-size:14px;color:var(--dim)}
.r-code{margin:1em 0;padding:12px 16px;background:#222228;border-radius:6px;border:1px solid var(--border);font-family:'Courier New',monospace;font-size:13px;color:#b0b0c0;white-space:pre-wrap}
.r-icode{font-family:'Courier New',monospace;font-size:13px;padding:1px 5px;background:#222228;border-radius:3px;color:var(--green)}
.r-div{margin:1.2em 0;text-align:center;color:var(--dim);opacity:.3;letter-spacing:6px}
.r-list{margin:.6em 0;padding-left:1.5em;font-size:15px;line-height:1.75;color:#d0d0d8}
.r-list li{margin-bottom:.3em}.r-list li::marker{color:var(--green)}
.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#444;font-size:14px;gap:4px;cursor:pointer;user-select:none}
.empty .icon{font-size:32px;opacity:.4}.hd{display:none!important}
.status{background:var(--surface);border-top:1px solid var(--border);padding:5px 20px;font-size:12px;color:var(--dim);display:flex;justify-content:space-between;flex-shrink:0}
.toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:var(--card);color:var(--text);padding:10px 22px;border-radius:8px;font-size:14px;border:1px solid var(--border);opacity:0;transition:opacity .3s;pointer-events:none;z-index:100;white-space:nowrap}
.toast.show{opacity:1}
@media(max-width:700px){.main{flex-direction:column}.left,.right{width:100%;border:none}.left{height:40vh}.right{height:60vh}}
</style>
</head>
<body>
<div class="topbar">
<div class="logo">归藏<span>排版</span>工具</div>
<div class="actions">
<button onclick="loadDemo()">📄 示例</button>
<button class="copy-btn" id="copyBtn" onclick="doCopy()">📋 复制</button>
</div>
</div>
<div class="main">
<div class="left">
<div class="phdr">✏️ 文章 <span id="wordCount">0 字</span></div>
<textarea id="input" placeholder="在这里写文章...&#10;&#10;# 大标题&#10;## 小标题&#10;> 引用&#10;&#96;&#96;&#96;代码&#96;&#96;&#96;&#10;**加粗**&#10;{红红色}  {绿绿色}&#10;---"></textarea>
</div>
<div class="right">
<div class="phdr">👁️ 预览</div>
<div class="preview" id="scrollArea">
<div class="empty" id="emptyState"><div class="icon">✍️</div><div>左边写文章</div><div style="font-size:12px;color:#555">点我加载示例</div></div>
<div class="r-hd" id="renderArea"></div>
</div>
</div>
</div>
<div class="status"><span>语法: # ## > &#96;&#96;&#96; ** {红} {绿} ---</span><span id="copyStatus"></span></div>
<div class="toast" id="toast"></div>
<script>
const input=document.getElementById('input'),renderArea=document.getElementById('renderArea'),empty=document.getElementById('emptyState'),wc=document.getElementById('wordCount'),btn=document.getElementById('copyBtn'),cs=document.getElementById('copyStatus');
let loaded=false;
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function inl(s){
  let r=esc(s);
  r=r.replace(/\*{2}(.+?)\*{2}/g,'<strong class="r-bold">$1</strong>');
  r=r.replace(/\{红(.+?)\}/g,'<span class="r-red">$1</span>');
  r=r.replace(/\{绿(.+?)\}/g,'<span class="r-green">$1</span>');
  r=r.replace(/`([^`]+)`/g,'<code class="r-icode">$1</code>');
  return r;
}
function parse(t){
  if(!t.trim())return '';
  const L=t.split('\n');let h='',i=0,n=L.length;
  while(i<n){
    const x=L[i].trim();
    if(!x){i++;continue}
    if(/^---+$/.test(x)){h+='<div class="r-div">◆ ◆ ◆</div>';i++;continue}
    let m=x.match(/^#\s+(.+)/);if(m){h+='<div class="r-h2">'+inl(m[1])+'</div>';i++;continue}
    m=x.match(/^##\s+(.+)/);if(m){h+='<div class="r-h3">'+inl(m[1])+'</div>';i++;continue}
    if(x.startsWith('> ')){let q=[];while(i<n&&L[i].trim().startsWith('> ')){q.push(L[i].trim().slice(2));i++}h+='<div class="r-quote">'+inl(q.join('\n'))+'</div>';continue}
    if(x.startsWith('\`\`\`')){i++;let c=[];while(i<n&&!L[i].trim().startsWith('\`\`\`')){c.push(L[i]);i++}i++;h+='<div class="r-code">'+esc(c.join('\n').trimEnd())+'</div>';continue}
    let p=[],s=i;
    while(i<n){const y=L[i].trim();if(!y||y.startsWith('#')||y.startsWith('> ')||y.startsWith('\`\`\`')||/^---+$/.test(y))break;p.push(L[i]);i++}
    p=p.join('\n').trim();if(!p)continue;
    if(/^[-*]\s/.test(p)){const its=p.split('\n').filter(l=>/^[-*]\s/.test(l.trim()));h+='<ul class="r-list">';its.forEach(it=>{h+='<li>'+inl(it.trim().replace(/^[-*]\s+/,''))+'</li>'});h+='</ul>'}else{h+='<div class="r-text">'+inl(p)+'</div>'}
  }
  return h;
}
function render(){
  const t=input.value,h=parse(t);
  if(h){renderArea.innerHTML=h;renderArea.classList.remove('hd');empty.classList.add('hd')}
  else{renderArea.classList.add('hd');empty.classList.remove('hd')}
  wc.textContent=t.replace(/\s/g,'').length+' 字';
}
async function doCopy(){
  if(!input.value.trim()){toast('⚠️ 先写文章');return}
  btn.textContent='⏳ ...';btn.style.opacity='.6';
  try{
    const r=await fetch('/copy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:input.value})});
    const d=await r.json();
    if(d.ok){toast('✅ 已复制！去公众号 Ctrl+V');cs.textContent='✅ 已复制';btn.textContent='✅ 已复制';setTimeout(()=>{btn.textContent='📋 复制';btn.style.opacity='1'},2000)}
    else{toast('❌ '+d.error);btn.textContent='📋 复制';btn.style.opacity='1'}
  }catch(e){toast('❌ 连接失败: '+e.message);btn.textContent='📋 复制';btn.style.opacity='1'}
}
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');clearTimeout(t._timer);t._timer=setTimeout(()=>t.classList.remove('show'),2500)}
function loadDemo(){input.value='用 AI 做量化交易，这一年我踩过的坑\n\n从回测过拟合到实盘翻车，6 个用真金白银换来的教训\n\n# 一、回测曲线越漂亮，越要警惕\n\n第一个策略回测年化 180%，最大回撤不到 5%。结果实盘第一天就亏了 3%。\n\n> **教训：** 回测永远比实盘好看。用 \`walk_forward\` 做样本外测试，能让幻觉缩小 60%。\n\n# 二、因子不是越多越好\n\n我一度堆了 47 个因子，后来用 Shapley 值筛选，砍到只剩 8 个。\n\n\`\`\`\nimport shap\nexplainer = shap.TreeExplainer(model)\nshap_values = explainer.shap_values(X_test)\n\`\`\`\n\n# 三、仓位管理 > 策略胜率\n\n之前专注在提高胜率，忽略了 {红回撤控制} 比 {绿策略胜率} 重要得多。\n\n---\n\n关注 **归藏AI**，每周分享量化实战干货。';render();loaded=true;toast('📝 已加载示例')}
input.addEventListener('input',render);
input.addEventListener('focus',function(){if(!loaded&&!input.value.trim())loadDemo()});
empty.addEventListener('click',function(){if(!input.value.trim())loadDemo()});
document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();doCopy()}});
render();
</script>
</body>
</html>'''

# ═══════════════════════════════════════════
# HTTP Server
# ═══════════════════════════════════════════
PORT = 18989

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode('utf-8'))
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if urlparse(self.path).path == '/copy':
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            # Try UTF-8 first, fallback to GBK
            try: data = json.loads(raw.decode('utf-8'))
            except UnicodeDecodeError:
                try: data = json.loads(raw.decode('gbk'))
                except: self._json(400, {'ok':False,'error':'编码错误'}); return
            except json.JSONDecodeError as e: self._json(400, {'ok':False,'error':str(e)}); return
            text = data.get('text','')
            if not text.strip(): self._json(400, {'ok':False,'error':'内容为空'}); return
            try:
                html = convert(text)
                copy_html(html)
                self._json(200, {'ok':True})
            except Exception as e: self._json(500, {'ok':False,'error':str(e)})
        else: self._json(404, {'ok':False,'error':'Not Found'})
    def _json(self, code, obj):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode('utf-8'))
    def log_message(self, *a): pass

def port_used(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port(port):
    try:
        r = subprocess.run(f'netstat -ano | findstr :{port}', shell=True, capture_output=True, text=True, timeout=3)
        for line in r.stdout.split('\n'):
            p = line.strip().split()
            if len(p)>=5 and 'LISTENING' in line:
                pid = p[-1]
                if pid and pid!='0':
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True, timeout=3)
                    time.sleep(0.3); return True
    except: pass
    return False

# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════
def main():
    if port_used(PORT):
        kill_port(PORT)
        time.sleep(0.3)

    socketserver.TCPServer.allow_reuse_address = True
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()

    try:
        with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
            httpd.serve_forever()
    except: pass

if __name__ == '__main__':
    main()
