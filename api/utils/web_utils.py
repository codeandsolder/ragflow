#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import ipaddress
import json
import re
import socket
from urllib.parse import urlparse
import aiosmtplib
from email.mime.text import MIMEText
from email.header import Header
from common import settings
from quart import render_template_string
from api.utils.email_templates import EMAIL_TEMPLATES
from playwright.sync_api import sync_playwright


OTP_LENGTH = 4
OTP_TTL_SECONDS = 5 * 60  # valid for 5 minutes
ATTEMPT_LIMIT = 5  # maximum attempts
ATTEMPT_LOCK_SECONDS = 30 * 60  # lock for 30 minutes
RESEND_COOLDOWN_SECONDS = 60  # cooldown for 1 minute


CONTENT_TYPE_MAP = {
    # Office
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "pdf": "application/pdf",
    "csv": "text/csv",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # Text/code
    "txt": "text/plain",
    "py": "text/plain",
    "js": "text/plain",
    "java": "text/plain",
    "c": "text/plain",
    "cpp": "text/plain",
    "h": "text/plain",
    "php": "text/plain",
    "go": "text/plain",
    "ts": "text/plain",
    "sh": "text/plain",
    "cs": "text/plain",
    "kt": "text/plain",
    "sql": "text/plain",
    # Web
    "md": "text/markdown",
    "markdown": "text/markdown",
    "mdx": "text/markdown",
    "htm": "text/html",
    "html": "text/html",
    "json": "application/json",
    # Image formats
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "ico": "image/x-icon",
    "avif": "image/avif",
    "heic": "image/heic",
    # PPTX
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


FORCE_ATTACHMENT_EXTENSIONS = {
    "htm",
    "html",
    "shtml",
    "xht",
    "xhtml",
    "xml",
    "mhtml",
    "svg",
}


FORCE_ATTACHMENT_CONTENT_TYPES = {
    "text/html",
    "image/svg+xml",
    "application/xhtml+xml",
    "text/xml",
    "application/xml",
    "multipart/related",
}


def should_force_attachment(ext: str | None, content_type: str | None = None) -> bool:
    normalized_ext = (ext or "").lower().strip(".")
    if normalized_ext in FORCE_ATTACHMENT_EXTENSIONS:
        return True
    normalized_type = (content_type or "").lower()
    return normalized_type in FORCE_ATTACHMENT_CONTENT_TYPES


def apply_safe_file_response_headers(response, content_type: str | None, ext: str | None = None):
    if content_type:
        response.headers.set("Content-Type", content_type)
    force_attachment = should_force_attachment(ext, content_type)
    if force_attachment:
        response.headers.set("X-Content-Type-Options", "nosniff")
        response.headers.set("Content-Disposition", "attachment")
    return response


def html2pdf(
    source: str,
    timeout: int = 2,
    install_driver: bool = True,
    print_options: dict = {},
):
    return __get_pdf_from_html(source, timeout, install_driver, print_options)


def __get_pdf_from_html(path: str, timeout: int, install_driver: bool, print_options: dict):
    calculated_print_options = {
        "landscape": False,
        "display_header_footer": False,
        "print_background": True,
        "prefer_css_page_size": True,
    }
    # Keep backward compatibility with old keys.
    if "displayHeaderFooter" in print_options:
        print_options["display_header_footer"] = print_options.pop("displayHeaderFooter")
    if "printBackground" in print_options:
        print_options["print_background"] = print_options.pop("printBackground")
    if "preferCSSPageSize" in print_options:
        print_options["prefer_css_page_size"] = print_options.pop("preferCSSPageSize")
    calculated_print_options.update(print_options)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        context = browser.new_context()
        page = context.new_page()
        page.goto(path, timeout=timeout * 1000, wait_until="networkidle")
        pdf_bytes = page.pdf(**calculated_print_options)
        browser.close()
        return pdf_bytes


def is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(
            [
                ip_obj.is_private,
                ip_obj.is_loopback,
                ip_obj.is_link_local,
                ip_obj.is_multicast,
                ip_obj.is_reserved,
                ip_obj.is_unspecified,
            ]
        )
    except ValueError:
        return False


def is_reserved_ip(ip: str) -> bool:
    """Check if IP is in reserved ranges that should be blocked for SSRF protection."""
    try:
        ip_obj = ipaddress.ip_address(ip)

        # Specific private ranges to block
        private_ranges = [
            ipaddress.IPv4Network("127.0.0.0/8"),  # Loopback
            ipaddress.IPv4Network("10.0.0.0/8"),  # Private
            ipaddress.IPv4Network("172.16.0.0/12"),  # Private
            ipaddress.IPv4Network("192.168.0.0/16"),  # Private
            ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local
            ipaddress.IPv4Network("0.0.0.0/8"),  # Current network
            ipaddress.IPv4Network("::1/128"),  # IPv6 loopback
            ipaddress.IPv4Network("fe80::/10"),  # IPv6 link-local
            ipaddress.IPv4Network("fc00::/7"),  # IPv6 unique local
            ipaddress.IPv4Network("fd00::/8"),  # IPv6 unique local
            ipaddress.IPv4Network("255.255.255.255/32"),  # Broadcast
        ]

        for network in private_ranges:
            if ip_obj in network:
                return True

        return False
    except ValueError:
        return False


def is_valid_url(url: str) -> bool:
    if not re.match(r"(https?)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", url):
        return False
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname

    if not hostname:
        return False

    hostname_lower = hostname.lower()

    if hostname_lower in ("localhost", "0.0.0.0", "::1", "::", "[::1]", "[::]"):
        return False

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".localhost") or hostname_lower.endswith(".internal"):
        return False

    if hostname_lower.startswith(
        (
            "192.168.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "127.",
            "169.254.",
        )
    ):
        return False

    try:
        ip_obj = ipaddress.ip_address(hostname_lower.strip("[]"))
        if is_reserved_ip(str(ip_obj)):
            return False
    except ValueError:
        pass

    try:
        for _, _, _, _, addrinfo in socket.getaddrinfo(hostname, None):
            ip = addrinfo[0]
            if is_reserved_ip(ip):
                return False
            break
    except socket.gaierror:
        return False

    return True


def safe_json_parse(data: str | dict) -> dict:
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data) if data else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_float(req: dict, key: str, default: float | int = 10.0) -> float:
    try:
        parsed = float(req.get(key, default))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


async def send_email_html(to_email: str, subject: str, template_key: str, **context):
    body = await render_template_string(EMAIL_TEMPLATES.get(template_key), **context)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{settings.MAIL_DEFAULT_SENDER[0]} <{settings.MAIL_DEFAULT_SENDER[1]}>"
    msg["To"] = to_email

    smtp = aiosmtplib.SMTP(
        hostname=settings.MAIL_SERVER,
        port=settings.MAIL_PORT,
        use_tls=True,
        timeout=10,
    )

    await smtp.connect()
    await smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
    await smtp.send_message(msg)
    await smtp.quit()


async def send_invite_email(to_email, invite_url, tenant_id, inviter):
    # Reuse the generic HTML sender with 'invite' template
    await send_email_html(
        to_email=to_email,
        subject="RAGFlow Invitation",
        template_key="invite",
        email=to_email,
        invite_url=invite_url,
        tenant_id=tenant_id,
        inviter=inviter,
    )


def otp_keys(email: str):
    email = (email or "").strip().lower()
    return (
        f"otp:{email}",
        f"otp_attempts:{email}",
        f"otp_last_sent:{email}",
        f"otp_lock:{email}",
    )


def hash_code(code: str, salt: bytes) -> str:
    import hashlib
    import hmac

    return hmac.new(salt, (code or "").encode("utf-8"), hashlib.sha256).hexdigest()


def captcha_key(email: str) -> str:
    return f"captcha:{email}"
