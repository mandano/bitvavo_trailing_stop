import smtplib
import logging
from email.mime.text import MIMEText
import os


class Messages(object):
    E_MAIL_SUBJECT: str = 'Trailing stop hit.'
    FROM: str = 'Bitvavo Trailing Alert'

    @classmethod
    def send_email(cls, message: str, subject: str = None):
        smtp_server = os.environ.get('SMTP_SERVER_URI')
        port = os.environ.get('SMTP_SERVER_PORT')
        email_user = os.environ.get('EMAIL_USER')
        email_user_pw = os.environ.get('EMAIL_USER_PW')

        msg = MIMEText(message, 'text')
        msg['Subject'] = subject or cls.E_MAIL_SUBJECT
        msg['From'] = cls.FROM
        msg['To'] = os.environ.get('RECEIVER_EMAIL')

        try:
            server = smtplib.SMTP_SSL(smtp_server, port)
            logging.info('Created smtp socket.')
            server.ehlo()
            server.login(email_user, email_user_pw)
            logging.info('Logged into smtp server.')
            server.send_message(
                msg,
                from_addr=os.environ.get('SENDER_EMAIL'),
                to_addrs=os.environ.get('RECEIVER_EMAIL'),
            )
            logging.info('E-mail sent.')
            server.quit()
        except Exception as e:
            logging.error(e)
