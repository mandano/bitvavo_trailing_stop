from decimal import Decimal

import simplejson as json
import copy

from handle_alerts import AlertHandler

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


def test_populate_new_alert(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    market = 'ETH-EUR'

    alert = copy.deepcopy(alert_template)
    alert['market'] = market
    alert['init_price'] = Decimal('1000')
    alert['trailing_percentage'] = Decimal('0.9')

    file_content = json.dumps([alert], indent=4, sort_keys=True)

    p.write_text(file_content)

    ticker_prices = [
        {
            'market': market,
            'price': '1511.7'
        }
    ]

    ah = AlertHandler(ticker_prices=ticker_prices, alerts_file_name=p)
    ah.process_alerts()
    ah.save_alerts()
    ah.load_alerts()

    assert ah.alerts[0]['actions'] == ["send_email", "sell"]
    assert ah.alerts[0]['init_price'] == Decimal('1511.7')
    assert ah.alerts[0]['market'] == 'ETH-EUR'
    assert ah.alerts[0]['price'] == Decimal('1511.7')
    assert ah.alerts[0]['status'] == 'active'
    assert ah.alerts[0]['trailing_percentage'] == Decimal('0.9')
    assert ah.alerts[0]['trailing_price'] == Decimal('0.9') * Decimal('1511.7')


def test_trailing_price_hit():
    assert True


def test_price_increase():
    assert True


def test_price_decreased():
    assert True