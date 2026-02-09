from dotenv import load_dotenv
import os

load_dotenv()

class Config:

    # ✅ MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DB = os.getenv("MYSQL_DB")
    

    SECRET_KEY = os.getenv("SECRET_KEY")

    # ✅ Flask Mail (Gmail SMTP)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # VERY IMPORTANT
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")
