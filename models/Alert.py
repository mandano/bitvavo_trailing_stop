import datetime
from decimal import Decimal
from models.clients.Bitvavo import BitvavoClient
from models.clients.Cryptowatch import CryptowatchClient


class Alert(object):
    STATUS_HIT = 'hit'
    STATUS_ACTIVE = 'active'
    STATUS_NOT_INIT = None

    ACTION_SEND_EMAIL = 'send_email'
    ACTION_SELL_ASSET = 'sell_asset'

    _client: BitvavoClient = None
    _client_backup: CryptowatchClient = None
    _price_diversion_threshold = None

    changedAttributes: list = None

    actions: list = None
    dt: datetime = None
    init_price: Decimal = None
    init_dt: datetime = None
    market: str = None
    price: Decimal = None
    backup_price: Decimal = None
    status: str = None
    trailing_percentage: Decimal = None
    trailing_price: Decimal = None
    amount: Decimal = None

    def __init__(self, **kwargs):
        self.changedAttributes = []
        self.actions = []

        self._price_diversion_threshold = Decimal('0.01')

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def is_ticker_price_diverted(self):
        """
        Check price against third party ticker price
        :return:
        """

        market_str_spl = self.market.split('-')

        currency = market_str_spl[1].lower()
        coin = market_str_spl[0].lower()

        if self._client_backup is None:
            self._client_backup = CryptowatchClient(
                _currency=currency,
                _coin=coin
            )

        self.backup_price = self._client_backup.get_ticker_price()

        lower_th = self.backup_price * (1 - self._price_diversion_threshold)
        upper_th = self.backup_price * (1 + self._price_diversion_threshold)

        if lower_th < self.price < upper_th:
            return False

        return True

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
            return False

        if self.market is None:
            return False

        price = Decimal(self._client.get_ticker_price())

        """# first time
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

            return True"""

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

        if price <= self.price:
            self.price = price
            self.dt = datetime.datetime.now()

            self.changedAttributes = [
                'price',
                'dt'
            ]

            return True

        if price > self.price:
            self.trailing_price = price * Decimal(self.trailing_percentage)
            self.price = price
            self.dt = datetime.datetime.now()

            self.changedAttributes = [
                'trailing_price',
                'price',
                'dt'
            ]

            return True

