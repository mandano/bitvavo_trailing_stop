from models.clients.Cryptowatch import CryptowatchClient

import datetime
from decimal import Decimal
from faker import Faker

from models.Alert import Alert
from models.clients.Bitvavo import BitvavoClient


def get_alert(**kwargs):
    status = kwargs.get("status")
    client_response_ticker_price_scenario = kwargs.get("client_response_ticker_price_scenario")
    client_response_ticker_price = None
    market = kwargs.get('market', 'ETH-EUR')

    fake = Faker()

    trailing_price = fake.pydecimal(min_value=100)
    trailing_percentage = Decimal('0.' + str(fake.pyint(min_value=70, max_value=97)))
    init_price = trailing_price / trailing_percentage + fake.pydecimal(min_value=100, max_value=200)

    if status == Alert.STATUS_ACTIVE:
        price = trailing_price / trailing_percentage + fake.pydecimal(min_value=100, max_value=200)
    elif status == Alert.STATUS_HIT:
        price = trailing_price / trailing_percentage
    else:
        return None

    if client_response_ticker_price_scenario is not None:
        if client_response_ticker_price_scenario == 'hit':
            client_response_ticker_price = trailing_price - fake.pydecimal(min_value=30, max_value=80)
        elif client_response_ticker_price_scenario == 'increased':
            client_response_ticker_price = price + fake.pydecimal(min_value=30, max_value=80)
        elif client_response_ticker_price_scenario == 'decreased':
            client_response_ticker_price = fake.pydecimal(min_value=int(trailing_price + 1), max_value=int(price - 1))

    dt = fake.date_time() + datetime.timedelta(microseconds=1)

    return Alert(
        amount=None,
        actions=[],
        dt=dt,
        init_dt=dt,
        init_price=init_price,
        market=market,
        price=price,
        status=status,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price,
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": client_response_ticker_price
            }
        )
    )


def test_is_ticker_price_diverted_true():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('1500.0')
    ticker_price = '1000.0'
    trailing_percentage = Decimal('0.9')

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_NOT_INIT,
        trailing_percentage=trailing_percentage,
        trailing_price=None,
        _client_backup=CryptowatchClient(
            _response_ticker_price={
                'result': {
                    'price': ticker_price
                }
            }
        ),
        _price_diversion_threshold=Decimal('0.01')
    )

    assert alert.is_ticker_price_diverted() is True


def test_is_ticker_price_diverted_false():
    actions = []
    market = 'ETH-EUR'
    init_price = Decimal('1000')
    price = Decimal('1500.0')
    ticker_price = '1499.0'
    trailing_percentage = Decimal('0.9')

    alert = Alert(
        actions=actions,
        dt=datetime.datetime.now(),
        init_price=init_price,
        market=market,
        price=price,
        status=Alert.STATUS_NOT_INIT,
        trailing_percentage=trailing_percentage,
        trailing_price=None,
        _client_backup=CryptowatchClient(
            _response_ticker_price={
                'result': {
                    'price': ticker_price
                }
            }
        ),
        _price_diversion_threshold=Decimal('0.01')
    )

    assert alert.is_ticker_price_diverted() is False


def test_get_symbol():
    market = 'ETH-EUR'

    alert = Alert(
        market=market,
    )

    assert alert.get_symbol() == 'ETH'


def test_attributes():
    amount = Decimal('1.20')
    actions = ['send_email']
    dt = datetime.datetime.now()
    init_price = Decimal('1000')
    market = 'ADA-EUR'
    price = Decimal('1300.3')
    status = Alert.STATUS_ACTIVE
    trailing_percentage = Decimal('0.9')
    trailing_price = Decimal('23.9')

    alert = Alert(
        amount=amount,
        actions=actions,
        dt=dt,
        init_dt=dt,
        init_price=init_price,
        market=market,
        price=price,
        status=status,
        trailing_percentage=trailing_percentage,
        trailing_price=trailing_price
    )

    alert_dict = {
        'amount': amount,
        'actions': actions,
        'dt': dt,
        'init_dt': dt,
        'init_price': init_price,
        'market': market,
        'price': price,
        'status': status,
        'trailing_percentage': trailing_percentage,
        'trailing_price': trailing_price
    }

    assert alert.attributes() == alert_dict


def test_update_by_client_already_hit():
    alert = get_alert(status=Alert.STATUS_HIT, client_response_ticker_price_scenario='hit')

    updated = alert.update_by_client()

    assert updated == False


def test_update_by_client_no_market():
    alert = get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='increased')
    alert.market = None

    updated = alert.update_by_client()

    assert updated == False


def test_update_by_client_price_hit():
    alert = get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='hit')

    updated = alert.update_by_client()

    assert updated == True
    assert alert.changedAttributes == ['price', 'dt', 'status']
    assert Alert.STATUS_HIT == alert.status


def test_update_by_client_price_increased():
    alert = get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='increased')

    updated = alert.update_by_client()

    assert updated == True
    assert alert.changedAttributes == ['trailing_price', 'price', 'dt']
    assert Alert.STATUS_ACTIVE == alert.status


def test_update_by_client_price_decreased():
    alert = get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='decreased')

    updated = alert.update_by_client()

    assert updated == True
    assert alert.changedAttributes == ['price', 'dt']
    assert Alert.STATUS_ACTIVE == alert.status

