import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SENDER_EMAIL, SENDER_PASSWORD

def send_reminder_email(body, receiver_email):
    sender_email = SENDER_EMAIL
    sender_password = SENDER_PASSWORD

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'НАПОМИНАНИЕ!'

    message.attach(MIMEText(body, 'plain'))

    smtp_server = "smtp.mail.ru"
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Сообщение отправлено успешно!")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")


