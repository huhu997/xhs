"""测试公众号写作工作台核心功能"""
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"

def main():
    issues = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # 1. 页面加载
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        title = page.title()
        print(f"页面标题: {title}")
        assert "公众号写作工作台" in title or "写作" in title, f"标题不对: {title}"
        print("✅ 页面加载正常")

        # 2. 检查阶段1（选题）的元素
        heading = page.locator("h1, h2, h3").filter(has_text="选题").first
        assert heading.is_visible(), "选题标题不可见"
        print("✅ 选题阶段标题可见")

        # 检查输入框
        topic_input = page.locator("input[placeholder*='散户']")
        assert topic_input.count() > 0, "话题输入框不存在"
        print("✅ 话题输入框存在")

        # 检查按钮
        angle_btn = page.locator("button").filter(has_text="生成切入角度")
        assert angle_btn.count() > 0, "生成角度按钮不存在"
        print("✅ 生成角度按钮存在")

        # 3. 检查侧边栏导航（当前阶段=选题，所以大纲/写作/质检显示为按钮）
        sidebar = page.locator("section[data-testid='stSidebar']")
        visible_btns = sidebar.locator("button:visible")
        assert visible_btns.count() >= 3, f"侧边栏按钮不足: {visible_btns.count()}"
        # 确认有"大纲""写作""质检"按钮
        outline_btn = sidebar.locator("button:visible").filter(has_text="大纲")
        assert outline_btn.count() > 0, "大纲按钮不存在"
        print("✅ 侧边栏导航存在")

        # 检查当前阶段指示文字
        current_phase = sidebar.locator("strong").filter(has_text="选题角度")
        assert current_phase.count() > 0, "当前阶段指示不存在"
        print("✅ 当前阶段指示正确")

        # 4. 检查人设切换
        selectbox = page.locator("section[data-testid='stSidebar'] .stSelectbox").first
        assert selectbox.is_visible(), "人设切换下拉不可见"
        print("✅ 人设切换存在")

        # 5. 测试输入话题
        topic_input.first.fill("散户为什么总是亏钱")
        page.wait_for_timeout(300)

        # 6. 测试"分析热点文章"输入框
        url_input = page.locator("input[placeholder*='https']")
        assert url_input.count() > 0, "文章链接输入框不存在"
        print("✅ 文章链接输入框存在")

        # 7. 截图留念
        page.screenshot(path="/tmp/wechat_writer_test.png", full_page=True)
        print("✅ 截图已保存")

        browser.close()

    if issues:
        print(f"\n❌ 发现 {len(issues)} 个问题:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("\n✅ 全部测试通过")

if __name__ == "__main__":
    main()
