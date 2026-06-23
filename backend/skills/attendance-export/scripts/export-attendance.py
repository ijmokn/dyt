"""AdacoWeb 考勤表 PDF 导出脚本.

通过 Playwright 自动化浏览器，登录 AdacoWeb 并导出考勤 PDF.

用法：
    python export-attendance.py [output_dir]

参数：
    output_dir: 可选，PDF 输出目录（默认从配置文件或 D:\\report 读取）
"""

import asyncio
import os
import sys
from pathlib import Path

# 强制 UTF-8 编码，避免 Windows GBK 终端下的 UnicodeEncodeError
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Skill 以独立脚本方式运行时，需要把 JMate 项目根目录加入导入路径。
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.async_api import async_playwright

from backend.services.attendance_config import default_output_dir, load_config

# 配置缺失时使用当前用户的文档目录，不再硬编码 D 盘路径。
DEFAULT_OUTPUT_DIR = default_output_dir()


def load_user_config() -> dict | None:
    """通过 JMate 配置服务读取配置，并取得已经解密的运行时密码。"""
    try:
        result = load_config()
        if result.error:
            print(f"[WARN] 读取 JMate 配置失败: {result.error}")
            return None
        print(f"[OK] 已从 JMate 配置文件加载: {result.path}")
        return result.config
    except Exception as exc:
        print(f"[WARN] 读取 JMate 配置失败: {exc}")
        return None


def normalize_output_dir(raw_output_dir: str | None) -> str:
    """规范化输出目录路径."""
    if not raw_output_dir:
        return DEFAULT_OUTPUT_DIR
    return raw_output_dir.replace("报表", "report").replace("鎶ヨ〃", "report")


# 加载配置
user_config = load_user_config()

CONFIG = {
    "url": (
        (user_config or {}).get("attendance", {}).get("url")
        or os.environ.get("ATTENDANCE_URL")
        or "http://adacodalian.ajis-group.com.cn/AdacoWeb/login"
    ),
    "username": (
        (user_config or {}).get("attendance", {}).get("username")
        or os.environ.get("ATTENDANCE_USERNAME")
        or ""
    ),
    "password": (
        (user_config or {}).get("attendance", {}).get("password")
        or os.environ.get("ATTENDANCE_PASSWORD")
        or ""
    ),
    "output_dir": normalize_output_dir(
        (user_config or {}).get("common", {}).get("outputDir")
        or os.environ.get("ATTENDANCE_OUTPUT_DIR")
        or (sys.argv[1] if len(sys.argv) > 1 else None)
    ),
    "wait_ms": (
        (user_config or {}).get("common", {}).get("waitMs")
        or int(os.environ.get("ATTENDANCE_WAIT_MS", "0"))
        or 7000
    ),
}


async def sleep(page):
    """等待配置的毫秒数."""
    await page.wait_for_timeout(CONFIG["wait_ms"])


def get_scopes(page):
    """获取页面及其所有 iframe 的作用域列表."""
    return [page, *page.frames]


def build_text_variants(text: str) -> list[str]:
    """构建文本的多种变体，用于匹配不同格式."""
    return [text, f"<{text}>", f"＜{text}＞", f"【{text}】"]


async def click_by_text(page, text: str, preferred_role: str | None = None):
    """通过文本内容查找并点击元素."""
    variants = build_text_variants(text)
    for scope in get_scopes(page):
        candidates = []
        for current_text in variants:
            if not preferred_role or preferred_role == "link":
                candidates.append(scope.get_by_role("link", name=current_text, exact=True).first)
                candidates.append(scope.get_by_role("link", name=current_text).first)
                candidates.append(scope.locator(f'a:has-text("{current_text}")').first)
            if not preferred_role or preferred_role == "button":
                candidates.append(scope.get_by_role("button", name=current_text, exact=True).first)
                candidates.append(scope.get_by_role("button", name=current_text).first)
                candidates.append(
                    scope.locator(
                        f'input[type="submit"][value="{current_text}"], '
                        f'input[type="button"][value="{current_text}"]'
                    ).first
                )
            candidates.append(scope.get_by_text(current_text, exact=True).first)
            candidates.append(scope.get_by_text(current_text).first)

        for locator in candidates:
            try:
                if await locator.count():
                    target = locator.first
                    visible = await target.is_visible()
                    if not visible:
                        continue
                    await target.click(timeout=1500)
                    return
            except Exception:
                continue

    raise Exception(f"未找到可点击元素: {text}")


async def click_by_any_text(page, texts: list[str], preferred_role: str | None = None) -> str:
    """尝试多个文本变体来点击元素."""
    for text in texts:
        try:
            await click_by_text(page, text, preferred_role)
            return text
        except Exception:
            continue
    raise Exception(f"未找到可点击元素（候选）: {' | '.join(texts)}")


async def fill_login(page):
    """填充登录表单."""
    # 填写用户名
    user_filled = False
    for scope in get_scopes(page):
        user_candidates = [
            scope.get_by_label(r"ユーザー|ユーザ|ID|User|Username|用户名|账号").first,
            scope.locator(
                'input[name*="user" i],input[id*="user" i],'
                'input[name*="id" i],input[id*="id" i],'
                'input[name*="login" i]'
            ).first,
            scope.locator('input[type="text"]').first,
        ]
        for locator in user_candidates:
            try:
                if await locator.count():
                    await locator.fill(CONFIG["username"])
                    user_filled = True
                    break
            except Exception:
                continue
        if user_filled:
            break
    if not user_filled:
        raise Exception("未找到用户名输入框")

    # 填写密码
    pass_filled = False
    for scope in get_scopes(page):
        pass_candidates = [
            scope.get_by_label(r"パスワード|Password|密码").first,
            scope.locator(
                'input[name*="pass" i],input[id*="pass" i],input[type="password"]'
            ).first,
            scope.locator('input[type="password"]').first,
        ]
        for locator in pass_candidates:
            try:
                if await locator.count():
                    await locator.fill(CONFIG["password"])
                    pass_filled = True
                    break
            except Exception:
                continue
        if pass_filled:
            break
    if not pass_filled:
        raise Exception("未找到密码输入框")


async def submit_login(page):
    """提交登录表单."""
    login_texts = ["ログイン", "login", "LOGIN", "登录", "登録", "サインイン", "sign in"]
    try:
        await click_by_any_text(page, login_texts, "button")
        return
    except Exception:
        pass

    # 尝试 submit/button 元素
    for scope in get_scopes(page):
        submit = scope.locator('input[type="submit"],button[type="submit"]').first
        try:
            if await submit.count():
                await submit.click()
                return
        except Exception:
            continue

    # 尝试在密码框按 Enter
    for scope in get_scopes(page):
        pass_input = scope.locator('input[type="password"]').first
        try:
            if await pass_input.count():
                await pass_input.press("Enter")
                return
        except Exception:
            continue

    raise Exception("未找到可用的登录提交方式")


async def main_async():
    """主函数."""
    # 检查配置
    if not CONFIG["username"] or not CONFIG["password"]:
        print("[ERR] 错误：未配置用户名或密码")
        print()
        print("请创建配置文件: %USERPROFILE%\\.attendance-config.json")
        print()
        print("示例配置：")
        print("{")
        print('  "version": "1.0",')
        print('  "attendance": {')
        print('    "username": "你的用户名",')
        print('    "password": "你的密码",')
        print('    "url": "http://adacodalian.ajis-group.com.cn/AdacoWeb/login"')
        print("  },")
        print('  "common": {')
        print('    "outputDir": "D:\\\\xxx\\\\ss",')
        print('    "waitMs": 7000')
        print("  }")
        print("}")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            # Step 1: 打开登录页面
            print("[1/6] 打开 AdacoWeb 登录页面")
            await page.goto(CONFIG["url"], wait_until="domcontentloaded")
            await sleep(page)

            # Step 2: 输入登录凭据
            print("[2/6] 输入用户名和密码")
            await fill_login(page)
            await sleep(page)

            # Step 3: 点击登录
            print("[3/6] 点击登录按钮")
            await submit_login(page)
            await sleep(page)

            # Step 4: 点击考勤管理
            print("[4/6] 点击考勤管理")
            try:
                await click_by_any_text(page, ["考勤管理", "勤怠管理"], "link")
            except Exception:
                await click_by_text(page, "考勤")
            await sleep(page)

            # Step 5: 点击检索两次
            print("[5/6] 点击检索按钮（第1次）")
            await click_by_any_text(page, ["検索", "检索"], "button")
            await sleep(page)

            print("[5/6] 点击检索按钮（第2次）")
            await click_by_any_text(page, ["検索", "检索"], "button")
            await sleep(page)

            # Step 6: 点击打印报表并等待 PDF 下载
            print("[6/6] 点击打印报表并等待 PDF 下载")
            async with page.expect_download(timeout=120000) as download_info:
                await click_by_any_text(
                    page, ["打印报表", "印刷", "プリント", "PDF出力", "PDF"], "button"
                )
            download = await download_info.value

            # 保存 PDF
            suggested_filename = download.suggested_filename
            output_dir = Path(CONFIG["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            save_path = output_dir / suggested_filename

            await download.save_as(str(save_path))
            print(f"导出完成: {save_path}")

        finally:
            await context.close()
            await browser.close()


def main():
    """入口函数."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
