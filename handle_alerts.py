import datetime
import smtplib
import ssl
import logging
import simplejson as json
import os
from decimal import Decimal

from python_bitvavo_api.bitvavo import Bitvavo

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '/.env')
load_dotenv('.env')

logging.basicConfig(level=os.environ.get("LOGGING_LEVEL"))


class AlertHandler(object):
    ticker_prices = list()
    alerts_file_name = 'alerts.json'
    client = Bitvavo({
        'APIKEY': os.environ.get('APIKEY'),
        'APISECRET': os.environ.get('APISECRET')
    })
    alerts = list()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        self.load_alerts()

    def load_alerts(self):
        try:
            with open(self.alerts_file_name, 'r') as fp:
                self.alerts = json.load(fp, parse_float=self.get_decimal)
        except FileNotFoundError:
            logging.error('No alert file.')

            exit(0)

        if not self.alerts:
            logging.warning("No alerts set.")

            exit(0)

    def save_alerts(self):
        with open(self.alerts_file_name, 'w') as fp:
            json.dump(self.alerts, fp, indent=4, sort_keys=True)

    @classmethod
    def get_decimal(cls, s):
        return Decimal(s)

    def get_fetched_ticker_price(self, market: str):
        for ticker_price in self.ticker_prices:
            if ticker_price['market'] == market:
                return ticker_price

        return None

    @classmethod
    def send_email(cls, message: str):
        smtp_server = os.environ.get('SMTP_SERVER_URI')
        port = os.environ.get('SMTP_SERVER_PORT')
        email_user = os.environ.get('EMAIL_USER')
        email_user_pw = os.environ.get('EMAIL_USER_PW')

        context = ssl.create_default_context()

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(email_user, email_user_pw)

            server.sendmail(
                os.environ.get('SENDER_EMAIL'),
                os.environ.get('RECEIVER_EMAIL'),
                message
            )
        except Exception as e:
            logging.error(e)
        finally:
            server.quit()

    def process_alerts(self):
        for idx, alert in enumerate(self.alerts):
            self.process_alert(idx, alert)

    def process_alert(self, idx: int, alert: dict):
        ticker_price = self.get_fetched_ticker_price(alert['market'])

        if ticker_price is None:
            ticker_price = self.client.tickerPrice({'market': alert['market']})

            if 'price' not in ticker_price or 'market' not in ticker_price:
                return

            if alert['market'] != ticker_price['market']:
                return

            ticker_price['price'] = Decimal(ticker_price['price'])

            self.ticker_prices.append(ticker_price)

        price = Decimal(ticker_price['price'])

        if alert['status'] == "hit":
            return

        # first time
        if alert['status'] is None:
            self.alerts[idx]['init_price'] = price
            self.alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
            self.alerts[idx]['price'] = price
            self.alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.alerts[idx]['status'] = 'active'

            return

        # trailing price hit
        if price <= alert['trailing_price']:
            self.alerts[idx]['price'] = price
            self.alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.alerts[idx]['status'] = 'hit'

            if 'send_email' in alert['actions']:
                self.send_email(json.dumps(alert, indent=4, sort_keys=True))

        # price increased and above init price
        if price > alert['price'] and price > alert['init_price']:
            self.alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
            self.alerts[idx]['price'] = price
            self.alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return

        # price increased but below init price
        if price > alert['price']:
            self.alerts[idx]['price'] = price
            self.alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return

        # price decreased
        if price <= alert['price']:
            self.alerts[idx]['price'] = price
            self.alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return


if __name__ == '__main__':
    ah = AlertHandler()
    ah.process_alerts()
    ah.save_alerts()
