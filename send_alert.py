import datetime
import simplejson as json
import os
from decimal import Decimal

from python_bitvavo_api.bitvavo import Bitvavo

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '/.env')
load_dotenv('.env')
alerts_file_name='alerts.json'
logging_level = os.environ.get("LOGGING_LEVEL")

cached_ticker_prices = list()


def get_cached_ticker_prices(market: str):
    for cached_ticker_price in cached_ticker_prices:
        if cached_ticker_price['market'] == market:
            return cached_ticker_price

    return None


def trigger_action():
    print('Alert!')


bitvavo = Bitvavo({
    'APIKEY': os.environ.get('APIKEY'),
    'APISECRET': os.environ.get('APISECRET')
})

with open(alerts_file_name, 'r') as fp:
    alerts = json.load(fp)

if not alerts:
    exit(0)

for idx, alert in enumerate(alerts):
    ticker_price = get_cached_ticker_prices(alert['market'])

    if ticker_price is None:
        ticker_price = bitvavo.tickerPrice({'market': alert['market']})

    if 'price' not in ticker_price:
        continue

    price = Decimal(ticker_price['price'])

    if alert['status'] == "hit":
        continue

    # first time
    if alert['status'] is None:
        alerts[idx]['init_price'] = price
        alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alerts[idx]['status'] = 'active'

        continue

    # price increased
    if price > alert['price']:
        alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        continue

    # trailing price hit
    if price <= alert['trailing_price']:
        alerts[idx]['trailing_price'] = price * alert['threshold']
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        trigger_action()

with open(alerts_file_name, 'w') as fp:
    json.dump(alerts, fp, indent=4, sort_keys=True)

