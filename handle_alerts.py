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


class BitvavoClient(Bitvavo):
    SIDE_BUY = 'buy'
    SIDE_SELL = 'sell'
    ORDER_TYPE = 'market'

    _response_order = None
    _response_balance = None
    _response_ticker_price = None

    market: str = None

    def __init__(self, **kwargs):
        super().__init__({
            'APIKEY': os.environ.get('APIKEY'),
            'APISECRET': os.environ.get('APISECRET')
        })

        for k, v in kwargs.items():
            self.__setattr__(k, v)

        if self.market is None:
            exit(1)

    def get_balance(self, symbol):
        if self._response_balance is None:
            self._response_balance = self.balance({'symbol': symbol})

            if symbol not in self._response_balance or 'available' not in self._response_balance:
                return None

            return Decimal(self._response_balance['available'])

        return None

    def get_ticker_price(self):
        if self._response_ticker_price is None:
            self._response_ticker_price = self.tickerPrice({'market': self.market})

            if 'price' not in self._response_ticker_price or 'market' not in self._response_ticker_price:
                return None

            if self.market != self._response_ticker_price['market']:
                return None

            return Decimal(self._response_ticker_price['price'])

        return self._response_ticker_price['price']

    def place_order(self, side: str, order_type, amount: str):
        self._response_order = self.placeOrder(
            self.market,
            side,
            order_type,
            {
                'amount': amount,
            }
        )

        return self._response_order


class Alert(object):
    STATUS_HIT = 'hit'
    STATUS_ACTIVE = 'active'
    STATUS_NOT_INIT = None

    ACTION_SEND_EMAIL = 'send_email'
    ACTION_SELL_ASSET = 'sell_asset'

    _client: BitvavoClient = None

    changedAttributes = []

    actions = []
    dt: str = None
    init_price: Decimal = None
    market: str = None
    price: Decimal = None
    status: str = None
    trailing_percentage: Decimal = None
    trailing_price: Decimal = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def attributes(self):
        return {
            'actions': self.actions,
            'dt': self.dt,
            'init_price': self.init_price,
            'market': self.market,
            'price': self.price,
            'status': self.status,
            'trailing_percentage':self.trailing_percentage,
            'trailing_price':self.trailing_price
        }

    def update_by_client(self):
        self.changedAttributes = []

        if self.status == self.STATUS_HIT:
            return None

        if self.market is None:
            return False

        price = Decimal(self._client.get_ticker_price())

        # first time
        if self.status is None:
            if self.init_price is None:
                self.init_price = price
                self.changedAttributes.append('init_price')

            self.trailing_price = price * Decimal(self.trailing_percentage)
            self.price = price
            self.dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.status = self.STATUS_ACTIVE

            self.changedAttributes.extend([
                'trailing_price',
                'price',
                'dt',
                'status'
            ])

            return True

        # trailing price hit
        if price <= self.trailing_price:
            self.price = price
            self.dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.status = self.STATUS_HIT

            self.changedAttributes = [
                'price',
                'dt',
                'status'
            ]

            return True

        # price increased and above init price
        if price > self.price and price > self.init_price:
            self.trailing_price = price * Decimal(self.trailing_percentage)
            self.price = price
            self.dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.changedAttributes = [
                'trailing_price'
                'price',
                'dt',
            ]

            return True

        # price increased but below init price
        if price > self.price:
            self.price = price
            self.dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.changedAttributes = [
                'price',
                'dt',
            ]

            return True

        # price decreased
        if price <= self.price:
            self.price = price
            self.dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.changedAttributes = [
                'price',
                'dt',
            ]

            return True


class AlertHandler(object):
    alerts_file_name = 'alerts.json'
    alerts = list()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        if self.alerts is None:
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

    def sell_asset(self):
        pass

    def update_alerts(self):
        for idx, alert in enumerate(self.alerts):
            alert = Alert(
                actions=alert['actions'],
                dt=alert['dt'],
                init_price=alert['init_price'],
                market=alert['market'],
                price=alert['price'],
                status=alert['status'],
                trailing_percentage=alert['trailing_percentage'],
                trailing_price=alert['trailing_price'],
                _client=BitvavoClient(
                    market=alert['market']
                )
            )

            alert.update_by_client()

            if alert.changedAttributes is not None:
                self.alerts[idx] = alert.attributes()

            if Alert.STATUS_HIT in alert.changedAttributes and Alert.ACTION_SEND_EMAIL in alert.actions:
                self.send_email(json.dumps(alert, indent=4, sort_keys=True))

            if Alert.STATUS_HIT in alert.changedAttributes and Alert.ACTION_SELL_ASSET in alert.actions:
                self.sell_asset()


if __name__ == '__main__':
    ah = AlertHandler()
    ah.update_alerts()
    ah.save_alerts()
