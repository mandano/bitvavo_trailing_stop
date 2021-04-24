from decimal import Decimal

from models.clients.Bitvavo import BitvavoClient


def test_get_ticker_price_no_market():
    b_client = BitvavoClient(
        _response_ticker_price={
            "market": "BTC-EUR",
            "price": "5003.2"
        }
    )

    assert b_client.get_ticker_price() == None


def test_get_ticker_price():
    b_client = BitvavoClient(
        _response_ticker_price={
            "market": "BTC-EUR",
            "price": "5003.2"
        }
    )

    assert b_client.get_ticker_price() == Decimal("5003.2")
