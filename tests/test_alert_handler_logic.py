from decimal import Decimal
import simplejson as json
from faker import Faker
from handle_alerts import AlertHandler, Alert

file_name = "alerts.json"


def test_load_alerts_from_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    fake = Faker()

    market = 'ETH-EUR'

    alert_0 = {
        "actions": [
            "send_email",
            "sell_asset"
        ],
        "datetime": fake.date_time_this_month().strftime("%Y-%m-%d %H:%M:%S"),
        "init_price": fake.pydecimal(min_value=200),
        "market": market,
        "price": fake.pydecimal(min_value=0),
        "status": Alert.STATUS_ACTIVE,
        "trailing_percentage": fake.pydecimal(min_value=0, max_value=1),
        "trailing_price": fake.pydecimal(min_value=0)
    }

    alert_1 = {
        "actions": [
            "send_email",
            "sell_asset"
        ],
        "datetime": fake.date_time_this_month().strftime("%Y-%m-%d %H:%M:%S"),
        "init_price": fake.pydecimal(min_value=200),
        "market": market,
        "price": fake.pydecimal(min_value=0),
        "status": Alert.STATUS_ACTIVE,
        "trailing_percentage": fake.pydecimal(min_value=0, max_value=1),
        "trailing_price": fake.pydecimal(min_value=0)
    }

    with open(p, 'w') as fp:
        json.dump([alert_0, alert_1], fp, indent=4, sort_keys=True)

    ah = AlertHandler(alerts_file_name=p)

    assert ah.alerts[0]['actions'] == alert_0['actions']
    assert ah.alerts[0]['init_price'] == alert_0['init_price']
    assert ah.alerts[0]['market'] == market
    assert ah.alerts[0]['price'] == alert_0['price']
    assert ah.alerts[0]['status'] == alert_0['status']
    assert ah.alerts[0]['trailing_percentage'] == alert_0['trailing_percentage']
    assert ah.alerts[0]['trailing_price'] == alert_0['trailing_price']

    assert ah.alerts[1]['actions'] == alert_1['actions']
    assert ah.alerts[1]['init_price'] == alert_1['init_price']
    assert ah.alerts[1]['market'] == market
    assert ah.alerts[1]['price'] == alert_1['price']
    assert ah.alerts[1]['status'] == alert_1['status']
    assert ah.alerts[1]['trailing_percentage'] == alert_1['trailing_percentage']
    assert ah.alerts[1]['trailing_price'] == alert_1['trailing_price']


def test_save_alerts_from_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    fake = Faker()

    market = 'ETH-EUR'

    alert_0 = {
        "actions": [
            "send_email",
            "sell_asset"
        ],
        "datetime": fake.date_time_this_month().strftime("%Y-%m-%d %H:%M:%S"),
        "init_price": fake.pydecimal(min_value=200),
        "market": market,
        "price": fake.pydecimal(min_value=0),
        "status": Alert.STATUS_ACTIVE,
        "trailing_percentage": fake.pydecimal(min_value=0, max_value=1),
        "trailing_price": fake.pydecimal(min_value=0)
    }

    alert_1 = {
        "actions": [
            "send_email",
            "sell_asset"
        ],
        "datetime": fake.date_time_this_month().strftime("%Y-%m-%d %H:%M:%S"),
        "init_price": fake.pydecimal(min_value=200),
        "market": market,
        "price": fake.pydecimal(min_value=0),
        "status": Alert.STATUS_ACTIVE,
        "trailing_percentage": fake.pydecimal(min_value=0, max_value=1),
        "trailing_price": fake.pydecimal(min_value=0)
    }

    ah = AlertHandler(alerts_file_name=p, alerts=[
        alert_0,
        alert_1
    ])

    ah.save_alerts()

    with open(p, 'r') as fp:
        alerts = json.load(fp, parse_float=AlertHandler.get_decimal)

    assert alerts[0]['actions'] == alert_0['actions']
    assert alerts[0]['init_price'] == alert_0['init_price']
    assert alerts[0]['market'] == market
    assert alerts[0]['price'] == alert_0['price']
    assert alerts[0]['status'] == alert_0['status']
    assert alerts[0]['trailing_percentage'] == alert_0['trailing_percentage']
    assert alerts[0]['trailing_price'] == alert_0['trailing_price']

    assert alerts[1]['actions'] == alert_1['actions']
    assert alerts[1]['init_price'] == alert_1['init_price']
    assert alerts[1]['market'] == market
    assert alerts[1]['price'] == alert_1['price']
    assert alerts[1]['status'] == alert_1['status']
    assert alerts[1]['trailing_percentage'] == alert_1['trailing_percentage']
    assert alerts[1]['trailing_price'] == alert_1['trailing_price']



