import json
from decimal import Decimal

from handle_alerts import CreateAlert, BitvavoClient


def get_decimal(s):
    return Decimal(s)


def test_create_alert_by_params(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()

    file_name = 'new_alert.json'
    market = 'ADA-EUR'
    alert_trailing_percentage = Decimal('0.9')
    market_selection_type = '2'
    actions_selection = '1'
    init_price_type = '2'
    price = Decimal('1.004')

    ca = CreateAlert(
        alert_trailing_percentage=alert_trailing_percentage,
        market_selection_type=market_selection_type,
        market=market,
        actions_selection=actions_selection,
        init_price_type=init_price_type,
        file_name=file_name,
        alerts_file_path=str(d) + '/',
        _client=BitvavoClient(
            market=market,
            _response_ticker_price={
                "market": market,
                "price": price
            }
        )
    )
    ca.add_by_console()

    with open(d / file_name, 'r') as fp:
        alerts = json.load(fp, parse_float=get_decimal, parse_int=get_decimal)

    assert alerts['market'] == market
    assert alerts['price'] == price
    assert alerts['trailing_percentage'] == alert_trailing_percentage
