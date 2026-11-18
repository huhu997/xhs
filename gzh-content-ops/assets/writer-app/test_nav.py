"""测试阶段导航功能"""
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 1. 检查初始阶段 = 选题
        heading = page.locator("h1, h2, h3").filter(has_text="选题").first
        assert heading.is_visible(), "选题标题不可见"
        print("✅ 阶段1: 选题")

        # 2. 点击侧边栏"大纲"按钮 → 跳转到大纲
        page.locator("section[data-testid='stSidebar'] button:visible").filter(has_text="大纲").click()
        page.wait_for_timeout(500)
        outline_heading = page.locator("h1, h2, h3").filter(has_text="大纲").first
        assert outline_heading.is_visible(), "跳转到大纲失败"
        # 此时应提示"请先完成选题阶段"
        warning = page.locator("text=请先完成选题阶段")
        assert warning.is_visible(), "未提示先完成选题"
        print("✅ 阶段2: 大纲（有前置条件提示）")

        # 3. 跳转到写作阶段
        page.locator("section[data-testid='stSidebar'] button:visible").filter(has_text="写作").click()
        page.wait_for_timeout(500)
        write_heading = page.locator("h1, h2, h3").filter(has_text="写作").first
        assert write_heading.is_visible(), "跳转到写作失败"
        outline_warning = page.locator("text=请先完成大纲阶段")
        assert outline_warning.is_visible(), "未提示先完成大纲"
        print("✅ 阶段3: 写作（有前置条件提示）")

        # 4. 跳转到质检阶段
        page.locator("section[data-testid='stSidebar'] button:visible").filter(has_text="质检").click()
        page.wait_for_timeout(500)
        review_heading = page.locator("h1, h2, h3").filter(has_text="质量检查").first
        assert review_heading.is_visible(), "跳转到质检失败"
        print("✅ 阶段4: 质检")

        # 5. 测试重置
        page.locator("section[data-testid='stSidebar'] button:visible").filter(has_text="重置").click()
        page.wait_for_timeout(500)
        topic_heading = page.locator("h1, h2, h3").filter(has_text="选题").first
        assert topic_heading.is_visible(), "重置后未回到选题"
        print("✅ 重置功能正常")

        browser.close()
        print("\n✅ 所有阶段导航测试通过")

if __name__ == "__main__":
    main()
