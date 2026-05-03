import os

from nature_daily_email import main


def configure_recipients():
    sender_account = os.environ["SMTP_USERNAME"]
    xu_xu_email = os.getenv("XU_XU_EMAIL", "xu.xu02@xjtlu.edu.cn")
    os.environ["EMAIL_TO"] = f"{sender_account},{xu_xu_email}"
    os.environ["EMAIL_CC"] = ""
    os.environ["EMAIL_BCC"] = ""


if __name__ == "__main__":
    configure_recipients()
    main()
