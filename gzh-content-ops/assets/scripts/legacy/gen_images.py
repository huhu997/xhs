# -*- coding: utf-8 -*-
"""第七回配图生成 — 即梦 Seedream 5.0 Lite（免费积分档）

背景：即梦新 UI 的提交按钮有两个（隐藏+可见），且默认选中的是「Seedream 5.0 Pro」
（会员模型，点提交会弹会员页）。本脚本：切 Lite → 点可见提交按钮 → 轮询新图 → 存候选。

用法：python gen_images.py [只跑某张的名字]
输出：候选图存 candidates/<名字>-c1..c4.png
"""
import base64, os, sys, time

SKILL = r"F:\桌面\zcode工作区\.zcode\skills\gemini生图"
sys.path.insert(0, SKILL)
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
import generate_image as gi
from generate_backup import open_backup_site, _handle_agreement

BASE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(BASE, "candidates")
os.makedirs(CAND, exist_ok=True)

STYLE = ("暖米色宣纸底，水墨插画质感，朱红与青瓷绿作小面积点缀，"
         "有层次的纸感与柔和阴影，编辑插画风格，安静高级，")
NOTEXT = "画面中不出现任何文字、字母、数字、水印。"

PROMPTS = [
 ("cover", "客栈庭院的夜景，一张木案上摊着两本厚厚的账册，一盏红灯笼在屋檐下，油灯微亮，"
           "窗外远处一半是火光一半是水色，构图居中留白，" + STYLE + NOTEXT),
 ("配图-01-洋面", "隔着一条河望向对岸：对岸一半燃着温暖的火光，一半是沉静的江水色，"
                  "岸边一叶小舟，天上几缕晚霞，" + STYLE + NOTEXT),
 ("配图-02-洋钱袋", "一间老账房里，房梁很高，梁上悬着一杆铜秤和一串钱袋，很高很高，"
                    "下面一个人仰头观望，距离感强烈，" + STYLE + NOTEXT),
 ("配图-03-院里炉", "客栈院子里一只红泥小火炉烧着温火，旁边摆着两只盛满凉水的木瓢，"
                    "远处街市灯火与灯笼，门口挂着客栈布幌，" + STYLE + NOTEXT),
 ("配图-04-磨盘三态", "院子里一盘大石磨，磨盘边三个人：一位老者盘腿静坐在一旁闭目养神，"
                      "一位年轻人快步走过不停留，一位中年人围着磨盘来回踱步挠头，"
                      "三种姿态对比鲜明，" + STYLE + NOTEXT),
 ("配图-05-开市四看", "客栈门口向外的四条小路，每条路口挂一盏灯笼照亮前路，"
                      "天将破晓，店门刚开一条缝，一杆秤立在门边，" + STYLE + NOTEXT),
]


def set_model_lite(page):
    """打开模型下拉并选中 Seedream 5.0 Lite；成功后返回 True"""
    try:
        page.mouse.click(519, 369); time.sleep(2)
        hit = page.evaluate("""(() => {
          const els = Array.from(document.querySelectorAll('div,span,li'));
          for (const e of els) {
            const t = (e.innerText||'').trim();
            if (t === 'Seedream 5.0 Lite') {
              const r = e.getBoundingClientRect();
              if (r.width>100 && r.height>10) return {x:r.x+r.width/2, y:r.y+r.height/2};
            }
          }
          return null; })()""")
        if not hit:
            page.keyboard.press("Escape"); return False
        page.mouse.click(hit["x"], hit["y"]); time.sleep(2)
        cur = page.evaluate("""(() => { const e=document.querySelector('.model-label-wceeNL')||document.querySelector('.lv-select-view-value'); return e?(e.innerText||'').trim():''; })()""")
        return "Lite" in cur
    except Exception as e:
        print("  切模型异常:", str(e)[:120]); return False


def clear_composer(page):
    try:
        page.locator('[contenteditable="true"]').first.click(timeout=6000)
        page.keyboard.press("Control+a"); page.keyboard.press("Delete"); time.sleep(0.5)
    except Exception:
        pass


def submit(page):
    sel = 'button[data-generator-submit-available="true"]'
    for i in range(page.locator(sel).count()):
        el = page.locator(sel).nth(i)
        try:
            if el.is_visible():
                el.click(timeout=8000); return True
        except Exception:
            continue
    return False


def fetch_new_images(page, pre_srcs, want=4):
    """等待并抓取新出现的大图，返回 [bytes,...]"""
    out, seen = [], set(pre_srcs)
    for _ in range(40):          # 最多 ~200s
        time.sleep(5)
        got = page.evaluate("""(pre) => (async () => {
            const res = [];
            for (const img of document.querySelectorAll('img')) {
              const src = img.src || '';
              if (!src || pre.includes(src) || img.naturalWidth < 400) continue;
              try { const r = await fetch(src, {credentials:'include'});
                    const b = await r.blob();
                    const buf = await b.arrayBuffer();
                    let bin=''; const u = new Uint8Array(buf);
                    for (let i=0;i<u.length;i++) bin += String.fromCharCode(u[i]);
                    res.push({src, data: btoa(bin), w: img.naturalWidth});
              } catch(e) {}
            }
            return res; })()""", list(seen))
        for g in got:
            if g["src"] in seen:
                continue
            seen.add(g["src"])
            out.append(g)
        if len(out) >= want:
            break
    return out


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    with sync_playwright() as p:
        ctx, page = gi.launch_browser(p, False)
        if not open_backup_site(page, "jimeng"):
            raise SystemExit("❌ 即梦打开失败")
        _handle_agreement(page); time.sleep(2)

        for name, prompt in PROMPTS:
            if only and name != only:
                continue
            print(f"\n=== [{name}] 开始 ===")
            clear_composer(page)
            try:
                ce = page.locator('[contenteditable="true"]').first
                ce.click(timeout=6000); time.sleep(0.6)
                page.keyboard.type(prompt, delay=4); time.sleep(1.5)
            except Exception as e:
                print("  输入失败:", str(e)[:120]); continue
            if not set_model_lite(page):
                print("  ⚠️ 模型切换未确认，尝试继续")
            pre = page.evaluate("Array.from(document.querySelectorAll('img')).map(i=>i.src)") or []
            if not submit(page):
                print("  ❌ 未找到可见提交按钮"); continue
            imgs = fetch_new_images(page, pre)
            print(f"  出图 {len(imgs)} 张")
            for k, g in enumerate(imgs, 1):
                fn = os.path.join(CAND, f"{name}-c{k}.png")
                with open(fn, "wb") as f:
                    f.write(base64.b64decode(g["data"]))
                print(f"  ✅ {os.path.basename(fn)} ({g['w']}px)")
        ctx.close()
    print("\n全部完成")

if __name__ == "__main__":
    main()
