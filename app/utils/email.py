from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic_settings import BaseSettings

class EmailSettings(BaseSettings):
    MAIL_USERNAME: str = "your_email@gmail.com"
    MAIL_PASSWORD: str = "your_password"
    MAIL_FROM: str = "your_email@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Online Cinema"

conf = ConnectionConfig(
    MAIL_USERNAME=EmailSettings().MAIL_USERNAME,
    MAIL_PASSWORD=EmailSettings().MAIL_PASSWORD,
    MAIL_FROM=EmailSettings().MAIL_FROM,
    MAIL_PORT=EmailSettings().MAIL_PORT,
    MAIL_SERVER=EmailSettings().MAIL_SERVER,
    MAIL_FROM_NAME=EmailSettings().MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_email(subject: str, recipients: list, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
