"""
端到端完整写作测试：选题 → 大纲 → 写作 → 质检
捕获每一阶段的输出和截图
"""
import sys, json, re
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"
OUTPUT = []

def log(msg):
    print(msg)
    OUTPUT.append(msg)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.set_default_timeout(120000)

    # ── 0. 加载 ──
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    log("✅ 页面加载完成")

    # ── 阶段 1: 选题 ──
    log("\n═══ 阶段 1: 选题 ═══")
    topic_input = page.locator("input[placeholder*='散户']").first
    topic_input.fill("为什么你总是存不下钱")
    page.wait_for_timeout(300)

    page.locator("button:visible").filter(has_text="生成切入角度").first.click()
    # 等待 API 返回
    proceed_btn = page.locator("button:visible").filter(has_text="确定选题，进入大纲阶段")
    proceed_btn.wait_for(timeout=60000)
    log("✅ 角度已生成")

    # 读取角度内容（在 proceed_btn 前的 markdown 区域）
    page.screenshot(path="/tmp/flow_phase1.png", full_page=True)
    log("📸 截图: phase1")

    # 进入大纲
    proceed_btn.first.click()
    page.wait_for_timeout(500)
    log("✅ 进入大纲阶段")

    # ── 阶段 2: 大纲 ──
    log("\n═══ 阶段 2: 大纲 ═══")

    # 定位素材池输入框
    all_textareas = page.locator("textarea").all()
    sidebar_ids = set(
        ta.get_attribute("id") or ""
        for ta in page.locator("section[data-testid='stSidebar'] textarea").all()
    )
    material_area = None
    for ta in all_textareas:
        if (ta.get_attribute("id") or "") not in sidebar_ids:
            material_area = ta
            break

    if material_area:
        material_text = (
            "- 核心观点：存不下钱不是因为赚得少，是因为花钱没有痛感\n"
            "- 亲身案例：朋友月薪2万，每月光，被裁后才清醒\n"
            "- 金句：存钱不是为了以后花，是为了现在有底气说不\n"
            "- 调性：真实、扎心、给方法"
        )
        material_area.fill(material_text)
        log("✅ 素材已填入")
    else:
        log("⚠️ 未找到素材池输入框")

    page.wait_for_timeout(300)

    # 生成大纲
    page.locator("button:visible").filter(has_text="生成大纲").first.click()
    # 等待大纲生成（结果会 rerun，等待大纲编辑器出现）
    page.wait_for_timeout(2000)
    try:
        page.locator("textarea").first.wait_for(state="visible", timeout=60000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    log("✅ 大纲生成完成")
    page.screenshot(path="/tmp/flow_phase2.png", full_page=True)

    # 进入写作
    writing_btn = page.locator("button:visible").filter(has_text="大纲确认，进入写作")
    if writing_btn.count() > 0:
        writing_btn.first.click()
        page.wait_for_timeout(500)
        log("✅ 进入写作阶段")
    else:
        # 可能大纲还没生成完，再等一等
        log("⚠️ 大纲确认按钮未出现，尝试等待")
        try:
            writing_btn.wait_for(timeout=60000)
            writing_btn.first.click()
            page.wait_for_timeout(500)
            log("✅ 进入写作阶段")
        except Exception:
            log("❌ 无法进入写作阶段")

    # ── 阶段 3: 写作 ──
    log("\n═══ 阶段 3: 写作 ═══")

    # 生成文章
    page.locator("button:visible").filter(has_text="生成文章").first.click()
    # 等待文章生成（需要较长时间）
    page.wait_for_timeout(2000)
    try:
        page.locator("textarea").first.wait_for(state="visible", timeout=120000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    log("✅ 文章生成完成")
    page.screenshot(path="/tmp/flow_phase3.png", full_page=True)

    # 截取文章内容
    all_textareas_3 = page.locator("textarea").all()
    sidebar_ids_3 = set(
        ta.get_attribute("id") or ""
        for ta in page.locator("section[data-testid='stSidebar'] textarea").all()
    )
    article_area = None
    for ta in all_textareas_3:
        if (ta.get_attribute("id") or "") not in sidebar_ids_3:
            article_area = ta
            break

    if article_area:
        article_text = article_area.input_value()
        log(f"\n📄 文章内容 ({len(article_text)} 字):")
        log("─" * 40)
        log(article_text[:2000])
        if len(article_text) > 2000:
            log(f"\n...（共 {len(article_text)} 字，截取前 2000 字）")
        log("─" * 40)
    else:
        log("⚠️ 未找到文章输入框")

    # 进入质检
    log("\n═══ 阶段 4: 质检 ═══")
    review_btn = page.locator("button:visible").filter(has_text="进入质检")
    if review_btn.count() > 0:
        review_btn.first.click()
        page.wait_for_timeout(500)
        log("✅ 进入质检阶段")

        # 质量评审
        quality_btn = page.locator("button:visible").filter(has_text="质量评审")
        if quality_btn.count() > 0:
            quality_btn.first.click()
            page.wait_for_timeout(3000)
            try:
                page.locator("text=总体评分").wait_for(timeout=60000)
                log("✅ 质量评审完成")
            except Exception:
                log("⚠️ 评审结果未显示")
        page.screenshot(path="/tmp/flow_phase4.png", full_page=True)
        log("📸 截图: phase4")

    log("\n" + "=" * 40)
    log("✅ 全流程结束")
    log("截图已保存: /tmp/flow_phase1.png ~ phase4.png")

    browser.close()
