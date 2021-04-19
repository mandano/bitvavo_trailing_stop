import datetime
from decimal import Decimal

from models.Alert import Alert
from models.clients.Bitvavo import BitvavoClient

file_name = "alerts.json"

alert_template = {
    "actions": [
        "send_email",
        "sell"
    ],
    "datetime": None,
    "init_price": None,
    "market": None,
    "price": None,
    "status": None,
    "trailing_percentage": None,
    "trailing_price": None
}


def test_populate_new_alert_init_price_set():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    ticker_price = Decimal('1511.7')
    trailing_percentage = Decimal('0.9')

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=init_price,
        status=Alert.STATUS_NOT_INIT,
        trailing_percentage=trailing_percentage,
        trailing_price=None,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_percentage * ticker_price


def test_populate_new_alert_init_price_not_set():
    actions = []
    market = 'ETH-EUR'
    init_price = None
    ticker_price = Decimal('1511.7')
    trailing_percentage = Decimal('0.9')

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=init_price,
        status=Alert.STATUS_NOT_INIT,
        trailing_percentage=trailing_percentage,
        trailing_price=None,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == ticker_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_percentage * ticker_price


def test_trailing_price_hit():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('950')
    ticker_price = Decimal('800')
    trailing_percentage = Decimal('0.9')
    trailing_price = init_price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_HIT
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_price


def test_price_increase_below_init_price():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('900')
    ticker_price = Decimal('950')
    trailing_percentage = Decimal('0.7')
    trailing_price = init_price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == ticker_price * trailing_percentage


def test_price_increase_above_init_price():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('1100')
    ticker_price = Decimal('1200')
    trailing_percentage = Decimal('0.9')
    trailing_price = price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_percentage * ticker_price


def test_price_decreased_above_init_price(tmp_path):
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('1300')
    ticker_price = Decimal('1200')
    trailing_percentage = Decimal('0.9')
    trailing_price = price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_price


def test_price_decreased_below_init_price(tmp_path):
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('900')
    ticker_price = Decimal('850')
    trailing_percentage = Decimal('0.8')
    trailing_price = price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_price


def test_price_decreased_hitting_init_price(tmp_path):
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('1100')
    ticker_price = Decimal('850')
    trailing_percentage = Decimal('0.7')
    trailing_price = price * trailing_percentage

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_ACTIVE,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": ticker_price

            }
        )
    )

    alert.update_by_client()

    assert alert.actions == actions
    assert alert.init_price == init_price
    assert alert.market == market
    assert alert.price == ticker_price
    assert alert.status == Alert.STATUS_ACTIVE
    assert alert.trailing_percentage == trailing_percentage
    assert alert.trailing_price == trailing_price
