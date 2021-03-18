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
    ticker_price = Decimal('1511.7')

    alert = copy.deepcopy(alert_template)
    alert['market'] = market
    alert['init_price'] = Decimal('1000')
    alert['trailing_percentage'] = Decimal('0.9')

    file_content = json.dumps([alert], indent=4, sort_keys=True)

    p.write_text(file_content)

    ticker_prices = [
        {
            'market': market,
            'price': ticker_price
        }
    ]

    ah = AlertHandler(ticker_prices=ticker_prices, alerts_file_name=p)
    ah.process_alerts()
    ah.save_alerts()
    ah.load_alerts()

    assert ah.alerts[0]['actions'] == ["send_email", "sell"]
    assert ah.alerts[0]['init_price'] == ticker_price
    assert ah.alerts[0]['market'] == market
    assert ah.alerts[0]['price'] == ticker_price
    assert ah.alerts[0]['status'] == 'active'
    assert ah.alerts[0]['trailing_percentage'] == alert['trailing_percentage']
    assert ah.alerts[0]['trailing_price'] == alert['trailing_percentage'] * ticker_price


def test_trailing_price_hit(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    market = 'ETH-EUR'
    ticker_price = Decimal('800')

    alert = copy.deepcopy(alert_template)
    alert['actions'] = []
    alert['market'] = market
    alert['init_price'] = Decimal('1000')
    alert['trailing_percentage'] = Decimal('0.9')
    alert['status'] = 'active'
    alert['price'] = Decimal('950')
    alert['trailing_price'] = alert['trailing_percentage'] * alert['init_price']

    file_content = json.dumps([alert], indent=4, sort_keys=True)

    p.write_text(file_content)

    ticker_prices = [
        {
            'market': market,
            'price': '800'
        }
    ]

    ah = AlertHandler(ticker_prices=ticker_prices, alerts_file_name=p)
    ah.process_alerts()
    ah.save_alerts()
    ah.load_alerts()

    assert ah.alerts[0]['actions'] == []
    assert ah.alerts[0]['init_price'] == alert['init_price']
    assert ah.alerts[0]['market'] == market
    assert ah.alerts[0]['price'] == ticker_price
    assert ah.alerts[0]['status'] == 'hit'
    assert ah.alerts[0]['trailing_percentage'] == alert['trailing_percentage']
    assert ah.alerts[0]['trailing_price'] == alert['trailing_price']


def test_price_increase_below_init_price(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    market = 'ETH-EUR'
    ticker_price = Decimal('950')

    alert = copy.deepcopy(alert_template)
    alert['actions'] = []
    alert['market'] = market
    alert['init_price'] = Decimal('1000')
    alert['trailing_percentage'] = Decimal('0.7')
    alert['status'] = 'active'
    alert['price'] = Decimal('900')
    alert['trailing_price'] = alert['trailing_percentage'] * alert['init_price']

    file_content = json.dumps([alert], indent=4, sort_keys=True)

    p.write_text(file_content)

    ticker_prices = [
        {
            'market': market,
            'price': ticker_price
        }
    ]

    ah = AlertHandler(ticker_prices=ticker_prices, alerts_file_name=p)
    ah.process_alerts()
    ah.save_alerts()
    ah.load_alerts()

    assert ah.alerts[0]['actions'] == []
    assert ah.alerts[0]['init_price'] == alert['init_price']
    assert ah.alerts[0]['market'] == market
    assert ah.alerts[0]['price'] == ticker_price
    assert ah.alerts[0]['status'] == 'active'
    assert ah.alerts[0]['trailing_percentage'] == alert['trailing_percentage']
    assert ah.alerts[0]['trailing_price'] == alert['trailing_price']


def test_price_increase_above_init_price(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / file_name

    market = 'ETH-EUR'
    ticker_price = Decimal('1200')

    alert = copy.deepcopy(alert_template)
    alert['actions'] = []
    alert['market'] = market
    alert['init_price'] = Decimal('1000')
    alert['trailing_percentage'] = Decimal('0.9')
    alert['status'] = 'active'
    alert['price'] = Decimal('1100')
    alert['trailing_price'] = alert['trailing_percentage'] * alert['price']

    file_content = json.dumps([alert], indent=4, sort_keys=True)

    p.write_text(file_content)

    ticker_prices = [
        {
            'market': market,
            'price': ticker_price
        }
    ]

    ah = AlertHandler(ticker_prices=ticker_prices, alerts_file_name=p)
    ah.process_alerts()
    ah.save_alerts()
    ah.load_alerts()

    assert ah.alerts[0]['actions'] == []
    assert ah.alerts[0]['init_price'] == alert['init_price']
    assert ah.alerts[0]['market'] == market
    assert ah.alerts[0]['price'] == ticker_price
    assert ah.alerts[0]['status'] == 'active'
    assert ah.alerts[0]['trailing_percentage'] == alert['trailing_percentage']
    assert ah.alerts[0]['trailing_price'] == alert['trailing_percentage'] * ticker_price


def test_price_decreased():
    assert True