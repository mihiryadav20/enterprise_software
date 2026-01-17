import httpx
import os
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


async def send_magic_link_email(to_email: str, token: str) -> bool:
    """
    Send a magic link email using Resend API.

    Args:
        to_email: The recipient's email address
        token: The magic link token

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY is not configured")

    magic_link = f"{FRONTEND_URL}/dashboard?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sign in to your account</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px;">Sign in to your account</h1>
        </div>
        <div style="background: #ffffff; padding: 40px 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
            <p style="font-size: 16px; margin-bottom: 30px;">
                Click the button below to securely sign in to your account. This link will expire in 15 minutes.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_link}"
                   style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          padding: 15px 40px;
                          text-decoration: none;
                          border-radius: 8px;
                          font-size: 16px;
                          font-weight: 600;
                          display: inline-block;
                          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                    Sign in
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 30px;">
                If you didn't request this email, you can safely ignore it.
            </p>
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
            <p style="font-size: 12px; color: #999;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{magic_link}" style="color: #667eea; word-break: break-all;">{magic_link}</a>
            </p>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Sign in to your account

Click the link below to securely sign in to your account. This link will expire in 15 minutes.

{magic_link}

If you didn't request this email, you can safely ignore it.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": "Sign in to your account",
                "html": html_content,
                "text": text_content
            }
        )

        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send email: {response.status_code} - {response.text}")
            return False
