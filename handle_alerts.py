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
    dt: str = None
    init_price: Decimal = None
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


class CreateAlert(object):
    _client: BitvavoClient = None

    market = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def add_by_console(self):
        print('Input new alert data:')
        print('---------------------')

        market =  self.choose_market()

        alert = Alert(_client=BitvavoClient(market=market))
        alert.market = market

        print('Add new init price:')
        print(' [1] Use manual value')
        print(' [2] Set by market')

        init_price_type = input()

        if init_price_type == '1':
            print('Type in your value for init price as string like "2345.43"')
            alert.init_price = Decimal(input())

        print('Insert trail in percentage like ["0.9", "0.45"]')
        alert.trailing_percentage = Decimal(input())

        print('Which actions should be activated?')
        print('[1] Send e-mail')
        print('[2] Sell')
        print('[3] Send e-mail and sell')

        actions_selection = input()

        if actions_selection == '1':
            alert.actions.append(Alert.ACTION_SEND_EMAIL)
        if actions_selection == '2':
            alert.actions.append(Alert.ACTION_SELL_ASSET)
        elif actions_selection == '3':
            alert.actions.extend([
                Alert.ACTION_SEND_EMAIL,
                Alert.ACTION_SELL_ASSET
            ])

        alert.update_by_client()

        ah = AlertHandler()
        ah.load_alerts()
        ah.alerts.append(alert.attributes())
        ah.save_alerts()

        print('New alert created.')

    def choose_market(self):
        print('Choose market, like "ETH-EUR"')
        print(' [1] Type in your market string')
        print(' [2] List supported markets')

        market_selection_type = input()

        if market_selection_type == '1':
            print('Type in your market string')
            market = input()
        elif market_selection_type == '2':
            markets = self._client.get_markets()

            print('Supported markets:')
            print(json.dumps(markets, indent=4, sort_keys=True))

            market = self.choose_market()
        else:
            print('Input not recognized.')
            exit(1)

        if not self.is_market_supported(market):
            print('Market string not supported.')
            exit(1)

        return market

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
    alerts = list()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        if not self.alerts:
            self.load_alerts()

    def load_alerts(self):
        try:
            with open(self.alerts_file_name, 'r') as fp:
                self.alerts = json.load(fp, parse_float=self.get_decimal)
        except FileNotFoundError:
            logging.info('No alert file.')

        if not self.alerts:
            logging.warning("No alerts set.")

    def save_alerts(self):
        with open(self.alerts_file_name, 'w') as fp:
            json.dump(self.alerts, fp, indent=4, sort_keys=True)

    @classmethod
    def get_decimal(cls, s):
        return Decimal(s)

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

            if not alert.changedAttributes:
                continue

            self.alerts[idx] = alert.attributes()

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
