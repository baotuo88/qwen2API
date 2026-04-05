import asyncio
import logging
from backend.core.account_pool import AccountPool, Account
from backend.core.browser_engine import _new_browser

log = logging.getLogger("qwen2api.auth")

class AuthResolver:
    """自动登录并提取 Token，在检测到 401 时自动自愈凭证"""
    def __init__(self, pool: AccountPool):
        self.pool = pool

    async def refresh_token(self, acc: Account) -> bool:
        if not acc.email or not acc.password:
            log.warning(f"[Auth] 账号 {acc.email} 缺少密码，无法自愈。")
            return False
            
        log.info(f"[Auth] 正在启动独立浏览器为 {acc.email} 自动刷新 Token...")
        try:
            async with _new_browser() as browser:
                page = await browser.new_page()
                await page.goto("https://chat.qwen.ai/auth", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # 填写邮箱密码
                li_email = await page.query_selector('input[placeholder*="Email"]')
                if li_email: await li_email.fill(acc.email)
                li_pwd = await page.query_selector('input[type="password"]')
                if li_pwd: await li_pwd.fill(acc.password)
                
                # 提交
                li_btn = (await page.query_selector('button:has-text("Log in")') or
                          await page.query_selector('button[type="submit"]'))
                if li_btn: await li_btn.click()
                
                await asyncio.sleep(8)
                
                # 提取 LocalStorage Token
                new_token = await page.evaluate("localStorage.getItem('token')")
                if new_token and new_token != acc.token:
                    acc.token = new_token
                    acc.valid = True
                    await self.pool.save()
                    log.info(f"[Auth] 自愈成功，{acc.email} 获得全新 Token。")
                    return True
                elif new_token == acc.token:
                    acc.valid = True
                    log.info(f"[Auth] {acc.email} 重新校验成功。")
                    return True
                else:
                    log.error(f"[Auth] {acc.email} 登录失败或遭遇滑块验证拦截。")
                    return False
        except Exception as e:
            log.error(f"[Auth] 自愈流程异常: {e}")
            return False
