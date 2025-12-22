import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class EmailSettings(BaseSettings):
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "urbanastronaut88@gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "Online Cinema Portfolio Project")

conf = ConnectionConfig(
    MAIL_USERNAME=EmailSettings().MAIL_USERNAME,
    MAIL_PASSWORD=EmailSettings().MAIL_PASSWORD,
    MAIL_FROM=EmailSettings().MAIL_FROM,
    MAIL_PORT=EmailSettings().MAIL_PORT,
    MAIL_SERVER=EmailSettings().MAIL_SERVER,
    MAIL_FROM_NAME=EmailSettings().MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
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
