import datetime
import smtplib
import logging
import sys
from email.mime.text import MIMEText
from pathlib import Path

import simplejson
import simplejson as json
import os
from decimal import Decimal

from python_bitvavo_api.bitvavo import Bitvavo

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(level=os.environ.get("LOGGING_LEVEL"))


class BitvavoClient(Bitvavo):
    SIDE_BUY = 'buy'
    SIDE_SELL = 'sell'
    ORDER_TYPE = 'market'

    _response_order = None
    _response_balance = None
    _response_ticker_price = None
    _response_markets = None

    market: str = None

    def __init__(self, **kwargs):
        super().__init__({
            'APIKEY': os.environ.get('APIKEY'),
            'APISECRET': os.environ.get('APISECRET')
        })

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def get_balance(self, symbol):
        if self._response_balance is None:
            self._response_balance = self.balance({'symbol': symbol})[0]

            if 'symbol' not in self._response_balance or 'available' not in self._response_balance:
                logging.error('bitvavo:get_balance: No symbol set.')

                return None

            return Decimal(self._response_balance['available'])

        return None

    def get_ticker_price(self):
        if self.market is None:
            logging.error('bitvavo: Market attribute not set.')

            exit(1)

        if self._response_ticker_price is None:
            self._response_ticker_price = self.tickerPrice({'market': self.market})

            if 'price' not in self._response_ticker_price or 'market' not in self._response_ticker_price:
                logging.error('bitvavo:get_ticker_price: No price or market in response.')

                return None

            if self.market != self._response_ticker_price['market']:
                logging.error('bitvavo:get_ticker_price: Market in response not equal class attribute.')

                return None

            return Decimal(self._response_ticker_price['price'])

        return self._response_ticker_price['price']

    def place_order(self, side: str, order_type: str, amount: str):
        self._response_order = self.placeOrder(
            self.market,
            side,
            order_type,
            {
                'amount': amount,
            }
        )

        return self._response_order

    def get_markets(self, market: str = None):
        if market is not None:
            self._response_markets = self.markets({'market': market})
        else:
            self._response_markets = self.markets({})

        return self._response_markets


class Alert(object):
    STATUS_HIT = 'hit'
    STATUS_ACTIVE = 'active'
    STATUS_NOT_INIT = None

    ACTION_SEND_EMAIL = 'send_email'
    ACTION_SELL_ASSET = 'sell_asset'

    _client: BitvavoClient = None

    changedAttributes = []

    actions = []
    dt: datetime = None
    init_price: Decimal = None
    init_dt: datetime = None
    market: str = None
    price: Decimal = None
    status: str = None
    trailing_percentage: Decimal = None
    trailing_price: Decimal = None
    amount: Decimal = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def get_symbol(self):
        if self.market is None:
            return None

        return self.market.split('-', 2)[0]

    def attributes(self):
        return {
            'amount': self.amount,
            'actions': self.actions,
            'dt': self.dt,
            'init_dt': self.init_dt,
            'init_price': self.init_price,
            'market': self.market,
            'price': self.price,
            'status': self.status,
            'trailing_percentage': self.trailing_percentage,
            'trailing_price': self.trailing_price
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

            dt = datetime.datetime.now()

            self.trailing_price = price * Decimal(self.trailing_percentage)
            self.price = price
            self.init_dt = dt
            self.dt = dt
            self.status = self.STATUS_ACTIVE

            self.changedAttributes.extend([
                'trailing_price',
                'price',
                'dt',
                'init_dt',
                'status'
            ])

            return True

        # trailing price hit
        if price <= self.trailing_price:
            self.price = price
            self.dt = datetime.datetime.now()
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
            self.dt = datetime.datetime.now()

            self.changedAttributes = [
                'trailing_price'
                'price',
                'dt',
            ]

            return True

        # price increased but below init price
        if price > self.price:
            self.price = price
            self.dt = datetime.datetime.now()

            self.changedAttributes = [
                'price',
                'dt',
            ]

            return True

        # price decreased
        if price <= self.price:
            self.price = price
            self.dt = datetime.datetime.now()

            self.changedAttributes = [
                'price',
                'dt',
            ]

            return True


class CreateAlert(object):
    _client: BitvavoClient = None
    file_name = 'new_alert.json'
    alerts_file_path = os.environ.get('ALERTS_FILE_PATH')

    alert = None

    actions = list()
    alert_init_price = None
    alert_trailing_percentage = None
    market = None

    actions_selection = None
    init_price_type = None
    market_selection_type = None

    def __init__(self, **kwargs):
        if sys.argv[1] != 'test_create_alert_logic.py::test_create_alert_by_params':
            if len(sys.argv) > 1:
                self.alert_trailing_percentage = Decimal(sys.argv[1])

            if len(sys.argv) > 2:
                self.market_selection_type = sys.argv[2]

            if len(sys.argv) > 3:
                self.market = sys.argv[3]

            if len(sys.argv) > 4:
                self.actions_selection = sys.argv[4]

            if len(sys.argv) > 5:
                self.init_price_type = Decimal(sys.argv[5])

            if len(sys.argv) > 6:
                self.alert_init_price = Decimal(sys.argv[6])

        self.alerts_file_path = os.environ.get('ALERTS_FILE_PATH')

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def save_alert(self):
        with open(self.alerts_file_path + self.file_name, 'w') as fp:
            json.dump(self.alert.attributes(), fp, indent=4, sort_keys=True, default=str)

    def add_by_console(self):
        if os.path.isfile(self.file_name):
            print("Pending new alert, try again please (Updating process probably didn't yet pick up new alert).")

            exit(1)

        print('Input new alert data:')
        print('---------------------')

        if self.market is None:
            self.choose_market()

        print('Add new init price:')
        print(' [1] Use manual value')
        print(' [2] Set by market')

        if self.init_price_type is None:
            self.init_price_type = input()

        if self.init_price_type == '1' and self.alert_init_price is None:
            print('Type in your value for init price as string like "2345.43"')
            self.alert_init_price = Decimal(input())

        if self.alert_trailing_percentage is None:
            print('Insert trail in percentage like ["0.9", "0.45"]')
            self.alert_trailing_percentage = Decimal(input())

        if self.actions_selection is None:
            print('Which actions should be activated?')
            print('[1] Send e-mail')
            print('[2] Sell')
            print('[3] Send e-mail and sell')

            self.actions_selection = input()

        if self.actions_selection == '1':
            self.actions.append(Alert.ACTION_SEND_EMAIL)
        if self.actions_selection == '2':
            self.actions.append(Alert.ACTION_SELL_ASSET)
        elif self.actions_selection == '3':
            self.actions.extend([
                Alert.ACTION_SEND_EMAIL,
                Alert.ACTION_SELL_ASSET
            ])

        self.alert = Alert(
            actions=self.actions,
            init_price=self.alert_init_price,
            trailing_percentage=self.alert_trailing_percentage,
            market=self.market,
            _client=self._client
        )

        self.alert.update_by_client()
        self.save_alert()

        print('New alert created.')
        print(self.alert.attributes())

    def choose_market(self):
        print('Choose market, like "ETH-EUR"')
        print(' [1] Type in your market string')
        print(' [2] List supported markets')

        self.market_selection_type = input()

        if self.market_selection_type == '1':
            print('Type in your market string')
            self.market = input()
        elif self.market_selection_type == '2':
            markets = self._client.get_markets()

            print('Supported markets:')
            print(json.dumps(markets, indent=4, sort_keys=True))

            self.market = self.choose_market()
        else:
            print('Input not recognized.')
            exit(1)

        if not self.is_market_supported(self.market):
            print('Market string not supported.')
            exit(1)

        return self.market

    def is_market_supported(self, market):
        remote_market = self._client.get_markets(market)

        if \
                'market' in remote_market and \
                market == remote_market['market'] and \
                'trading' == remote_market['status']:
            return True

        return False


class AlertHandler(object):
    alerts_file_name = 'alerts.json'
    new_alert_file_name = 'new_alert.json'
    alerts_file_path = os.environ.get('ALERTS_FILE_PATH')
    alerts = list()
    _ticker_prices = {}

    def __init__(self, **kwargs):
        self.alerts_file_path = os.environ.get('ALERTS_FILE_PATH')

        for k, v in kwargs.items():
            self.__setattr__(k, v)

        if not self.alerts:
            self.load_alerts()

    def load_alerts(self):
        alerts = list()

        try:
            if not os.path.isfile(self.alerts_file_path + self.alerts_file_name):
                Path(self.alerts_file_name).touch()

            with open(self.alerts_file_path + self.alerts_file_name, 'r') as fp:
                alerts = json.load(fp, parse_float=self.get_decimal, parse_int=self.get_decimal)
        except FileNotFoundError:
            logging.info('No alert file.')
        except simplejson.errors.JSONDecodeError as e:
            logging.info(e)

        if os.path.isfile(self.alerts_file_path + self.new_alert_file_name):
            try:
                with open(self.alerts_file_path + self.new_alert_file_name, 'r') as fp:
                    alerts.append(json.load(fp, parse_float=self.get_decimal, parse_int=self.get_decimal))

                os.remove(self.alerts_file_path + self.new_alert_file_name)
            except simplejson.errors.JSONDecodeError as e:
                logging.info(e)

        if not alerts:
            logging.warning("No alerts set.")

        for idx, alert in enumerate(alerts):
            alert = Alert(
                actions=alert['actions'],
                dt=datetime.datetime.strptime(alert['dt'], "%Y-%m-%d %H:%M:%S.%f"),
                init_dt=datetime.datetime.strptime(alert['init_dt'], "%Y-%m-%d %H:%M:%S.%f"),
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

            self.alerts.append(alert)

    def save_alerts(self):
        alerts = list()

        for idx, alert in enumerate(self.alerts):
            alerts.append(alert.attributes())

        with open(self.alerts_file_path + self.alerts_file_name, 'w') as fp:
            json.dump(alerts, fp, indent=4, sort_keys=True, default=str)

    @classmethod
    def get_decimal(cls, s):
        return Decimal(s)

    def update_alerts(self):
        for idx, alert in enumerate(self.alerts):
            """if alert.market in self._ticker_prices:
                self.alerts[idx]._client._response_ticker_price = {
                    'price': self._ticker_prices[alert.market],
                    'market': alert.market
                }"""

            alert.update_by_client()
            #self._ticker_prices[alert.market] = alert.price

            if not alert.changedAttributes:
                continue

            if alert.STATUS_HIT != alert.status:
                continue

            if Alert.ACTION_SELL_ASSET in alert.actions:
                trade = Trade(
                    _client=BitvavoClient(market=alert.market),
                    _alert=alert
                )
                trade.sell()

            if Alert.ACTION_SEND_EMAIL in alert.actions:
                Messages.send_email(json.dumps(alert.attributes(), indent=4, sort_keys=True))


class Messages(object):
    E_MAIL_SUBJECT: str = 'Trailing stop hit.'
    FROM: str = 'Bitvavo Trailing Alert'

    @classmethod
    def send_email(cls, message: str):
        smtp_server = os.environ.get('SMTP_SERVER_URI')
        port = os.environ.get('SMTP_SERVER_PORT')
        email_user = os.environ.get('EMAIL_USER')
        email_user_pw = os.environ.get('EMAIL_USER_PW')

        msg = MIMEText(message, 'text')
        msg['Subject'] = cls.E_MAIL_SUBJECT
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


class Trade(object):
    _client: BitvavoClient = None
    _alert: Alert = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def sell(self):
        symbol = self._alert.get_symbol()

        if symbol is None:
            return False

        if self._alert.amount is None:
            amount = self._client.get_balance(symbol)
        else:
            amount = self._alert.amount

        try:
            amount
        except NameError:
            return False

        response = self._client.place_order(
            BitvavoClient.SIDE_SELL,
            BitvavoClient.ORDER_TYPE,
            str(amount)
        )

        Messages.send_email(json.dumps(response, indent=4, sort_keys=True))

        if 'orderId' in response:
            return True

        return False


if __name__ == '__main__':
    ah = AlertHandler()
    ah.update_alerts()
    ah.save_alerts()
