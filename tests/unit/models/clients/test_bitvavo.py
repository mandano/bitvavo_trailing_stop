from decimal import Decimal

from models.clients.Bitvavo import BitvavoClient


def test_get_ticker_price_no_market(bitvavo_credentials):
    market = "BTC-EUR"

    b_client = BitvavoClient(
        api_key=bitvavo_credentials['bitvavo_access_key'],
        api_secret=bitvavo_credentials['bitvavo-access-signature'],
        _response_ticker_price={
            "market": market,
            "price": "5003.2"
        }
    )

    assert b_client.get_ticker_price() is None


def test_get_ticker_price(bitvavo_credentials):
    market = "BTC-EUR"

    b_client = BitvavoClient(
        api_key=bitvavo_credentials['bitvavo_access_key'],
        api_secret=bitvavo_credentials['bitvavo-access-signature'],
        market=market,
        _response_ticker_price={
            "market": market,
            "price": "5003.2"
        }
    )

    assert b_client.get_ticker_price() == Decimal("5003.2")
