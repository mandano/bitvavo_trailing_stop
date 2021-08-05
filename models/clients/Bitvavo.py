import logging
import os
from decimal import Decimal
from python_bitvavo_api.bitvavo import Bitvavo


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
            'APIKEY': kwargs.get('api_key') if 'api_key' in kwargs else os.environ.get('APIKEY'),
            'APISECRET': kwargs.get('api_secret') if 'api_secret' in kwargs else os.environ.get('APISECRET')
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

            return None

        if self._response_ticker_price is None:
            self._response_ticker_price = self.tickerPrice({'market': self.market})

            if 'price' not in self._response_ticker_price or 'market' not in self._response_ticker_price:
                logging.error('bitvavo:get_ticker_price: No price or market in response.')

                return None

            if self.market != self._response_ticker_price['market']:
                logging.error('bitvavo:get_ticker_price: Market in response not equal class attribute.')

                return None

            return Decimal(self._response_ticker_price['price'])

        return Decimal(self._response_ticker_price['price'])

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
