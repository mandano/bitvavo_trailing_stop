import datetime
from decimal import Decimal

import simplejson as json
from faker import Faker
from handle_alerts import AlertHandler, Alert, BitvavoClient

file_name = "alerts.json"


def test_load_alerts_from_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    alert_0 = get_alert(status=Alert.STATUS_ACTIVE)
    alert_1 = get_alert(status=Alert.STATUS_ACTIVE)

    with open(p, 'w') as fp:
        json.dump([
                alert_0.attributes(),
                alert_1.attributes()
            ],
            fp,
            indent=4,
            sort_keys=True,
            default=str
        )

    ah = AlertHandler(alerts_file_name=p)

    assert ah.alerts[0].attributes() == alert_0.attributes()
    assert ah.alerts[1].attributes() == alert_1.attributes()


def test_save_alerts_from_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    alert_0 = get_alert(status=Alert.STATUS_ACTIVE)
    alert_1 = get_alert(status=Alert.STATUS_ACTIVE)

    ah_save = AlertHandler(alerts_file_name=p, alerts=[
        alert_0,
        alert_1
    ])

    ah_save.save_alerts()

    ah_load = AlertHandler(alerts_file_name=p)

    assert ah_load.alerts[0].attributes() == alert_0.attributes()
    assert ah_load.alerts[1].attributes() == alert_1.attributes()


def get_alert(**kwargs):
    status = kwargs.get("status")
    client_response_ticker_price_scenario = kwargs.get("client_response_ticker_price_scenario")
    client_response_ticker_price = None

    fake = Faker()

    market = 'ETH-EUR'
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
            client_response_ticker_price = fake.pydecimal(min_value=int(trailing_price+1), max_value=int(price-1))

    dt = fake.date_time()

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


def test_update_alerts(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    ah = AlertHandler(
        alerts_file_name=p,
        alerts=[
            get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='hit'),
            get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='increased'),
            get_alert(status=Alert.STATUS_ACTIVE, client_response_ticker_price_scenario='decreased')
        ],

    )

    ah.update_alerts()

    assert ah.alerts[0].status == Alert.STATUS_HIT

    assert ah.alerts[1].status == Alert.STATUS_ACTIVE
    assert ah.alerts[1].price == ah.alerts[1]._client._response_ticker_price['price']

    assert ah.alerts[2].status == Alert.STATUS_ACTIVE
    assert ah.alerts[2].price == ah.alerts[2]._client._response_ticker_price['price']
