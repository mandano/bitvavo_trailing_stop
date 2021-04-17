from decimal import Decimal

import requests


class CryptowatchClient(object):
    _response_ticker_price = None
    _response_markets = None

    _currency = 'eur'
    _market = 'kraken'
    _coin = 'eth'

    def __init__(self, **kwargs):
        super().__init__()

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def get_ticker_price(self):
        r = requests.get(
            'https://api.cryptowat.ch/markets/' +
            self._market +
            '/' +
            self._coin +
            self._currency +
            '/price'
        )

        ticker_price_response = r.json()

        if 'result' not in ticker_price_response and 'price' not in ticker_price_response['result']:
            return None

        return Decimal(ticker_price_response['result']['price'])

