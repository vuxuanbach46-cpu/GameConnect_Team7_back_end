"""SMTP email delivery helpers, intended for FastAPI BackgroundTasks."""

import html
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email(recipient: str, subject: str, text_body: str, html_body: str) -> None:
    smtp_user = settings.SMTP_USER.strip()
    app_password = settings.SMTP_APP_PASSWORD.replace(" ", "")
    from_email = settings.SMTP_FROM_EMAIL.strip() or smtp_user
    if not smtp_user or not app_password or not from_email:
        logger.error("Email delivery skipped: SMTP_USER/SMTP_APP_PASSWORD is not configured")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.SMTP_FROM_NAME, from_email))
    message["To"] = recipient
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                context=ssl.create_default_context(),
                timeout=20,
            ) as server:
                server.login(smtp_user, app_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                server.ehlo()
                if settings.SMTP_STARTTLS:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(smtp_user, app_password)
                server.send_message(message)
        logger.info("Email sent: %s", subject)
    except Exception:
        # SMTP failure happens after the API response and must not undo account/token work.
        logger.exception("SMTP delivery failed for email type: %s", subject)


def send_registration_email(recipient: str, username: str) -> None:
    safe_name = html.escape(username or "game thủ")
    text_body = (
        f"Chào {username or 'game thủ'},\n\n"
        "Tài khoản GameConnect của bạn đã được tạo thành công. "
        "Bạn có thể đăng nhập và bắt đầu kết nối với đồng đội.\n\n"
        "Nếu bạn không thực hiện đăng ký này, vui lòng liên hệ quản trị viên.\n"
    )
    html_body = f"""<!doctype html><html lang="vi"><body style="font-family:Arial,sans-serif;color:#172033">
      <h2>Chào {safe_name}!</h2>
      <p>Tài khoản <strong>GameConnect</strong> của bạn đã được tạo thành công.</p>
      <p>Bạn có thể đăng nhập và bắt đầu kết nối với đồng đội.</p>
      <p style="color:#64748b;font-size:13px">Nếu bạn không thực hiện đăng ký này, vui lòng liên hệ quản trị viên.</p>
    </body></html>"""
    _send_email(recipient, "Chào mừng bạn đến với GameConnect", text_body, html_body)


def send_password_reset_email(recipient: str, code: str) -> None:
    safe_code = html.escape(code)
    text_body = (
        f"Mã đặt lại mật khẩu GameConnect của bạn là: {code}\n\n"
        "Mã có hiệu lực trong 15 phút. Nếu bạn không yêu cầu đặt lại mật khẩu, "
        "hãy bỏ qua email này."
    )
    html_body = f"""<!doctype html><html lang="vi"><body style="font-family:Arial,sans-serif;color:#172033">
      <h2>Đặt lại mật khẩu GameConnect</h2>
      <p>Nhập mã xác nhận sau để tiếp tục:</p>
      <p style="font-size:28px;font-weight:700;letter-spacing:8px;color:#e85002">{safe_code}</p>
      <p>Mã có hiệu lực trong <strong>15 phút</strong>.</p>
      <p style="color:#64748b;font-size:13px">Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.</p>
    </body></html>"""
    _send_email(recipient, "Mã đặt lại mật khẩu GameConnect", text_body, html_body)
