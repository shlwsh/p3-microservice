"""NWU library / CARSI institutional login via Playwright."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
CREDENTIALS_PATH = ROOT / "config" / "library_credentials.json"


@dataclass
class LibraryCredentials:
    university: str
    university_en: str
    username: str
    password: str
    authserver_url: str
    lib_portal: str
    carsi_info: str
    publishers: dict[str, Any]

    @classmethod
    def load(cls, path: Path | None = None) -> LibraryCredentials:
        p = path or CREDENTIALS_PATH
        if not p.is_file():
            raise FileNotFoundError(
                f"未找到 {p}，请复制 config/library_credentials.example.json 并填写账号密码"
            )
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


def _fill_authserver(page, creds: LibraryCredentials) -> bool:
    """Fill NWU unified identity form on authserver.nwu.edu.cn."""
    selectors_user = (
        "#username",
        "input[name='username']",
        "input#un",
        "input[placeholder*='学号']",
        "input[placeholder*='工号']",
    )
    selectors_pass = (
        "#password",
        "input[name='password']",
        "input[type='password']",
    )
    selectors_submit = (
        "#login_submit",
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('登录')",
        "#login",
    )

    filled_user = filled_pass = False
    for sel in selectors_user:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.fill(creds.username)
            filled_user = True
            break
    for sel in selectors_pass:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.fill(creds.password)
            filled_pass = True
            break
    if not (filled_user and filled_pass):
        return False

    for sel in selectors_submit:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            loc.click()
            return True
    page.keyboard.press("Enter")
    return True


def _click_institution(page, creds: LibraryCredentials) -> bool:
    """Try to pick 西北大学 / Northwest University on publisher WAYF page."""
    patterns = (
        creds.university,
        creds.university_en,
        "Northwest University (China)",
        "Northwest University, China",
    )
    for text in patterns:
        link = page.get_by_role("link", name=text)
        if link.count() > 0:
            link.first.click()
            return True
        btn = page.get_by_text(text, exact=False)
        if btn.count() > 0:
            btn.first.click()
            return True
    # IEEE entity search box
    search = page.locator(
        "input[placeholder*='institution'], input[placeholder*='Institution'], "
        "input[name='search'], input#search-main"
    ).first
    if search.count() > 0:
        search.fill(creds.university_en)
        page.wait_for_timeout(1500)
        opt = page.get_by_text(creds.university_en, exact=False)
        if opt.count() > 0:
            opt.first.click()
            return True
    return False


def _on_nwu_auth_page(page) -> bool:
    u = page.url.lower()
    return "authserver.nwu.edu.cn" in u or "idp.nwu.edu.cn" in u


def login_authserver_direct(page, creds: LibraryCredentials, service_url: str) -> bool:
    """Direct NWU portal login with ?service= redirect target."""
    url = f"{creds.authserver_url}?service={quote(service_url, safe='')}"
    print("[进展] 直达西北大学统一身份认证...")
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    if _on_nwu_auth_page(page):
        _fill_authserver(page, creds)
        page.wait_for_timeout(5000)
        return True
    return False


def login_ieee_institutional(page, creds: LibraryCredentials | None = None) -> bool:
    """
    IEEE 机构登录：Institutional Sign In → 西北大学 → 统一身份认证（CARSI 路径）。
    不经过 lib.nwu.edu.cn 超星全局代理。
    """
    creds = creds or LibraryCredentials.load()
    ieee = creds.publishers.get("ieee", {})
    ieee_home = ieee.get("home", "https://ieeexplore.ieee.org")
    signin_url = ieee.get(
        "institutional_sign_in",
        "https://ieeexplore.ieee.org/login/signin?url=https%3A%2F%2Fieeexplore.ieee.org%2F",
    )

    print("[进展] 打开 IEEE 机构登录页...")
    page.goto(signin_url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)

    for label in (
        "Institutional Sign In",
        "Institutional sign in",
        "机构登录",
        "Shibboleth",
        "Access Through Your Institution",
        "Access through your institution",
    ):
        tab = page.locator(f"a:has-text('{label}'), button:has-text('{label}')")
        if tab.count() > 0:
            tab.first.click()
            page.wait_for_timeout(2000)
            break

    if not _click_institution(page, creds):
        # IEEE 2024+ entity picker
        page.locator("input[type='search'], input[placeholder*='Search']").first.fill(
            creds.university_en
        )
        page.wait_for_timeout(1500)
        _click_institution(page, creds)

    page.wait_for_timeout(3000)

    deadline = time.time() + 35
    while time.time() < deadline and not _on_nwu_auth_page(page):
        page.wait_for_timeout(500)

    if _on_nwu_auth_page(page):
        print("[进展] 填写统一身份认证账号...")
        _fill_authserver(page, creds)
        page.wait_for_timeout(6000)
    else:
        login_authserver_direct(page, creds, ieee_home)

    deadline = time.time() + 60
    while time.time() < deadline:
        url = page.url.lower()
        if "ieeexplore.ieee.org" in url and "/login" not in url and "/signin" not in url:
            print("[进展] ✅ IEEE 机构登录成功")
            return True
        if "ieeexplore.ieee.org" in url and "signin" not in url:
            print("[进展] ✅ IEEE 机构登录成功")
            return True
        page.wait_for_timeout(1000)

    print("[进展] ⚠️ 自动登录未完成（可能有验证码），请在浏览器中手动完成")
    return False


def login_springer_carsi(page, creds: LibraryCredentials | None = None) -> bool:
    """Springer CARSI: link.springer.com/login/carsi"""
    creds = creds or LibraryCredentials.load()
    pub = creds.publishers.get("springer", {})
    url = pub.get("home", "https://link.springer.com").rstrip("/") + pub.get(
        "carsi_path", "/login/carsi"
    )
    print(f"[进展] 打开 Springer CARSI: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2000)
    _click_institution(page, creds)
    page.wait_for_timeout(3000)
    if "authserver.nwu.edu.cn" in page.url:
        _fill_authserver(page, creds)
        page.wait_for_timeout(5000)
    return "springer.com" in page.url


def ensure_publisher_login(page, publisher: str = "ieee") -> bool:
    creds = LibraryCredentials.load()
    if publisher == "ieee":
        return login_ieee_institutional(page, creds)
    if publisher == "springer":
        return login_springer_carsi(page, creds)
    return False
