"""公众号写作工作台 — Streamlit 主入口

结构化写作流程：
  选题 → 大纲 → 写作 → 质检
"""

import os
import datetime
import json
import streamlit as st
from pathlib import Path

from core.config import load as load_config
from core.memory import (
    ensure_dirs, build_system_prompt,
    read_long_term, write_long_term,
    append_short_term, append_rule,
    read_rules,
)
from core.thoughts import (
    append_thought, read_current_month, list_months,
    save_image_from_bytes,
)
from workflow.topic import generate_angles, analyze_hot_topic
from workflow.outline import generate_outline
from workflow.writing import write_article
from workflow.quality import review_article, de_ai_taste, generate_article_images, has_image_markers
from tools.formatter import to_wechat_html
from tools.web_fetcher import fetch_text

# ── 初始化 ──
cfg = load_config()
ensure_dirs()

st.set_page_config(page_title="公众号写作工作台", page_icon="📝", layout="wide")

# ── Session 状态 ──
if "phase" not in st.session_state:
    st.session_state.phase = "topic"       # topic → outline → writing → review
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "outline" not in st.session_state:
    st.session_state.outline = ""
if "article" not in st.session_state:
    st.session_state.article = ""
if "material" not in st.session_state:
    st.session_state.material = ""
if "soul_name" not in st.session_state:
    st.session_state.soul_name = "default"
if "history" not in st.session_state:
    st.session_state.history = []           # 多版本存档
if "current_soul_text" not in st.session_state:
    st.session_state.current_soul_text = ""
if "angles_result" not in st.session_state:
    st.session_state.angles_result = ""     # 选题角度（与大纲分开存储）
if "images" not in st.session_state:
    st.session_state.images = []            # 生成的配图 [{url, description, status}, ...]


# ── 灵魂/人设 ──
SOUL_DIR = Path(cfg["ROOT_DIR"]) / "souls"

def list_souls():
    return sorted(f.stem for f in SOUL_DIR.glob("*.md"))

def load_soul(name: str) -> str:
    fpath = SOUL_DIR / f"{name}.md"
    return fpath.read_text(encoding="utf-8") if fpath.exists() else ""


def refresh_soul():
    st.session_state.current_soul_text = load_soul(st.session_state.soul_name)


# ── 存档 ──
ARCHIVE_DIR = Path(cfg["ROOT_DIR"]) / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)


def save_archive(phase: str, content: str):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in st.session_state.topic[:30])
    fpath = ARCHIVE_DIR / f"{ts}_{phase}_{safe}.md"
    fpath.write_text(content, encoding="utf-8")
    return str(fpath)


# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.header("⚙️ 控制台")

    # ── 人设切换 ──
    souls = list_souls()
    selected = st.selectbox("🎭 账号人设", souls, index=souls.index(st.session_state.soul_name) if st.session_state.soul_name in souls else 0)
    if selected != st.session_state.soul_name:
        st.session_state.soul_name = selected
        refresh_soul()
        st.rerun()

    if not st.session_state.current_soul_text:
        refresh_soul()

    # ── 记忆管理 ──
    with st.expander("🧠 记忆管理", expanded=False):
        tab1, tab2, tab3 = st.tabs(["长期记忆", "写作规则", "个人想法"])
        with tab1:
            lt = st.text_area("长期风格偏好", value=read_long_term(), height=150, label_visibility="collapsed")
            if st.button("保存长期记忆", use_container_width=True):
                write_long_term(lt)
                st.success("已保存")
        with tab2:
            rules = st.text_area("明确规则", value=read_rules(), height=150, label_visibility="collapsed")
            if st.button("保存规则", use_container_width=True):
                from core.memory import _write as mem_write
                mem_write("rules.md", rules)
                st.success("已保存")
        with tab3:
            st.markdown("**记录你的真实经历/观点**")
            tags = st.text_input("标签（逗号分隔）", placeholder="存钱、消费主义、工作", key="thought_tags")
            thought = st.text_area("内容", height=80, placeholder="上个月我卸载了京东和美团，一个月多存了3000...", label_visibility="collapsed", key="thought_content")
            uploaded_img = st.file_uploader("配图（可选）", type=["png", "jpg", "jpeg", "gif", "webp"], key="thought_img")
            if st.button("📝 保存想法", use_container_width=True):
                if tags.strip() and thought.strip():
                    img_md = ""
                    if uploaded_img is not None:
                        img_md = save_image_from_bytes(uploaded_img.getvalue(), uploaded_img.name) or ""
                    append_thought(tags.strip(), thought.strip(), img_md)
                    st.success("已保存")
                    st.rerun()
                else:
                    st.warning("标签和内容不能为空")
            st.divider()
            st.caption("最近想法")
            months = list_months()
            if months:
                default_month = months[0]
                month_options = {m: m for m in months}
                selected_month = st.selectbox("切换月份", options=list(month_options.keys()), format_func=lambda x: x, index=0, key="thought_month", label_visibility="collapsed")
                from core.thoughts import read_month as _read_month
                year_str, month_str = selected_month.split("-")
                thoughts_text = _read_month(int(year_str), int(month_str))
                if thoughts_text.strip():
                    st.markdown(thoughts_text)
                else:
                    st.caption("该月暂无想法")
            else:
                st.caption("还没有记录，写一条试试")

    # ── 工作流导航 ──
    st.divider()
    st.subheader("📋 写作流程")
    phases = {
        "topic": "1️⃣ 选题角度",
        "outline": "2️⃣ 大纲",
        "writing": "3️⃣ 写作",
        "review": "4️⃣ 质检",
    }
    for key, label in phases.items():
        if st.session_state.phase == key:
            st.markdown(f"**→ {label}**")
        else:
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.phase = key
                st.rerun()

    st.divider()
    if st.button("🔄 重置流程", use_container_width=True, type="primary"):
        for k in ["phase", "topic", "outline", "article", "material", "history", "angles_result", "images"]:
            st.session_state[k] = "" if k != "history" and k != "images" else [] if k in ("history", "images") else ""
        st.session_state.phase = "topic"
        st.rerun()


# ==========================================
# 主区域 — 按阶段渲染
# ==========================================
st.title("📝 公众号写作工作台")

# ── 阶段 1: 选题 ──
if st.session_state.phase == "topic":
    st.markdown("### 1️⃣ 选题与角度")
    st.caption("先确定写什么，再想怎么写。选题对了文章就成功了一半。")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic_input = st.text_input("你想写什么话题", value=st.session_state.topic, placeholder="例：散户为什么总是亏钱")
    with col2:
        url_input = st.text_input("或粘贴热点文章链接", placeholder="https://...")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🎯 生成切入角度", use_container_width=True):
            if not topic_input:
                st.warning("请输入话题")
            else:
                st.session_state.topic = topic_input
                with st.spinner("生成角度中..."):
                    result = generate_angles(topic_input)
                st.session_state.angles_result = result  # 存角度，不占 outline
                st.markdown(result)
                append_short_term(f"选题角度生成：{topic_input}")
    with col_b:
        if st.button("🔍 分析热点文章", use_container_width=True):
            if not url_input:
                st.warning("请输入链接")
            else:
                with st.spinner("分析中..."):
                    result = analyze_hot_topic(url_input)
                st.markdown(result)

    if st.session_state.get("angles_result", ""):
        if st.button("✅ 确定选题，进入大纲阶段 →", use_container_width=True, type="primary"):
            st.session_state.phase = "outline"
            st.rerun()

# ── 阶段 2: 大纲 ──
elif st.session_state.phase == "outline":
    st.markdown("### 2️⃣ 大纲设计")
    st.caption("好的结构 = 读者愿意读完。确认大纲后再写作。")

    if not st.session_state.topic:
        st.warning("请先完成选题阶段")
    else:
        st.text(f"主题：{st.session_state.topic}")

        # 素材池
        material = st.text_area(
            "📦 素材池（把你的观点、案例、金句丢进来，AI 必须围绕这些写）",
            value=st.session_state.material,
            height=150,
            placeholder="例：\n- 核心观点：散户亏钱不是因为技术差\n- 亲身案例：上周朋友追涨停板当天亏 8 万\n- 金句：市场不缺机会，缺的是你还活着",
        )
        st.session_state.material = material

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📋 生成大纲", use_container_width=True):
                with st.spinner("生成大纲中..."):
                    result = list(generate_outline(
                        st.session_state.topic,
                        st.session_state.material,
                        st.session_state.current_soul_text,
                    ))
                    full = "".join(result)
                st.session_state.outline = full
                st.rerun()

        with col2:
            if st.button("💾 保存大纲", use_container_width=True):
                if st.session_state.outline:
                    path = save_archive("outline", st.session_state.outline)
                    st.success(f"已保存至 {path}")

        # 显示当前大纲
        if st.session_state.outline:
            st.divider()
            st.markdown("#### 当前大纲")
            with st.expander("查看/编辑大纲", expanded=True):
                edited = st.text_area("可手动编辑调整", value=st.session_state.outline, height=400, label_visibility="collapsed")
                st.session_state.outline = edited

            if st.button("✅ 大纲确认，进入写作 →", use_container_width=True, type="primary"):
                if st.session_state.outline.strip():
                    st.session_state.phase = "writing"
                    st.rerun()

# ── 阶段 3: 写作 ──
elif st.session_state.phase == "writing":
    st.markdown("### 3️⃣ 写作")
    st.caption("AI 根据大纲和素材撰写正文，你可以反复修改。")

    if not st.session_state.outline:
        st.warning("请先完成大纲阶段")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✍️ 生成文章", use_container_width=True):
                with st.spinner("写作中..."):
                    result = list(write_article(
                        st.session_state.topic,
                        st.session_state.outline,
                        st.session_state.material,
                        st.session_state.current_soul_text,
                    ))
                    full = "".join(result)
                if st.session_state.article:
                    st.session_state.history.append(st.session_state.article)
                st.session_state.article = full
                save_archive("article", full)
                append_short_term(f"生成文章：{st.session_state.topic}")
                st.rerun()

        with col2:
            if st.button("💾 保存当前版本", use_container_width=True):
                if st.session_state.article:
                    path = save_archive("article", st.session_state.article)
                    st.success(f"已保存至 {path}")

        with col3:
            if st.session_state.history:
                if st.button("⏪ 回退到上一版", use_container_width=True):
                    st.session_state.article = st.session_state.history.pop()
                    st.rerun()

        # 文章编辑器（不用 key，避免 Streamlit 缓存旧值覆盖文章）
        article_text = st.text_area(
            "文章内容（可直接编辑）",
            value=st.session_state.article,
            height=500,
            label_visibility="collapsed",
        )
        st.session_state.article = article_text

        st.caption(f"字数：{len(article_text)}  |  版本历史：{len(st.session_state.history)} 个旧版本")

        if st.session_state.article.strip():
            if st.button("✅ 进入质检 →", use_container_width=True, type="primary"):
                st.session_state.phase = "review"
                st.rerun()

# ── 阶段 4: 质检 ──
elif st.session_state.phase == "review":
    st.markdown("### 4️⃣ 质量检查与发布准备")

    if not st.session_state.article.strip():
        st.warning("还没有文章，请先完成写作阶段")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📊 质量评审", use_container_width=True):
                with st.spinner("评审中..."):
                    result = review_article(st.session_state.article)
                st.session_state.review_result = result
                st.rerun()

        with col2:
            intensity = st.selectbox("去 AI 味力度", ["light", "medium", "heavy"], index=1, label_visibility="collapsed")
            if st.button("🧹 去 AI 味", use_container_width=True):
                with st.spinner("去味中..."):
                    result = list(de_ai_taste(st.session_state.article, intensity))
                    cleaned = "".join(result)
                st.session_state.history.append(st.session_state.article)
                st.session_state.article = cleaned
                st.rerun()

        with col3:
            if st.button("📋 转公众号排版", use_container_width=True):
                html = to_wechat_html(st.session_state.article)
                st.session_state.wechat_html = html
                st.rerun()

        with col4:
            has_markers = has_image_markers(st.session_state.article)
            if has_markers:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    if st.button("🖼️ 生成配图", use_container_width=True):
                        with st.spinner("生成配图中..."):
                            new_article, img_results = generate_article_images(st.session_state.article)
                        st.session_state.article = new_article
                        st.session_state.images = img_results
                        save_archive("article_with_images", new_article)
                        st.rerun()
                with sub_col2:
                    if st.button("🧹 清理标记", use_container_width=True):
                        from tools.image_gen import strip_image_markers
                        st.session_state.article = strip_image_markers(st.session_state.article)
                        st.rerun()
            else:
                st.caption("🖼️ 无配图标记\n重新生成文章可自动插入")

        # 配图标记警告
        if has_image_markers(st.session_state.article):
            st.warning("📷 文章中有未处理的 [配图：...] 标记。点击「生成配图」替换为实际图片，或「清理标记」移除占位符。")

        # 显示评审结果
        if "review_result" in st.session_state and st.session_state.review_result:
            with st.expander("📊 评审结果", expanded=True):
                st.markdown(st.session_state.review_result)

        # 显示公众号 HTML
        if "wechat_html" in st.session_state and st.session_state.wechat_html:
            with st.expander("📋 公众号排版预览", expanded=False):
                st.code(st.session_state.wechat_html, language="html")
                st.download_button(
                    "⬇️ 下载 HTML 文件",
                    data=st.session_state.wechat_html,
                    file_name=f"{st.session_state.topic[:20]}.html",
                    mime="text/html",
                    use_container_width=True,
                )

        # 文章（可直接编辑）
        st.divider()
        st.markdown("#### 当前文章（可直接编辑）")
        article_text = st.text_area(
            "",
            value=st.session_state.article,
            height=400,
            label_visibility="collapsed",
        )
        st.session_state.article = article_text

        st.caption(f"字数：{len(st.session_state.article)}")

        # 显示生成的配图
        if st.session_state.get("images"):
            st.divider()
            st.markdown("#### 🖼️ 配图预览")
            img_cols = st.columns(min(len(st.session_state.images), 3))
            for i, img in enumerate(st.session_state.images):
                col = img_cols[i % 3]
                with col:
                    if img["status"] == "ok" and img.get("url"):
                        st.image(img["url"], caption=img["description"][:60], use_container_width=True)
                    else:
                        st.markdown(f"⚠️ {img['description'][:60]} (生成失败)")

        if st.button("✏️ 回到写作阶段修改", use_container_width=True):
            st.session_state.phase = "writing"
            st.rerun()
