import datetime
import smtplib
import ssl
import logging
import simplejson as json
import os
from decimal import Decimal

from python_bitvavo_api.bitvavo import Bitvavo

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '/.env')
load_dotenv('.env')
alerts_file_name='alerts.json'

cached_ticker_prices = list()
logging.basicConfig(level=os.environ.get("LOGGING_LEVEL"))


def get_decimal(s):
    return Decimal(s)


def get_cached_ticker_prices(market: str):
    for cached_ticker_price in cached_ticker_prices:
        if cached_ticker_price['market'] == market:
            return cached_ticker_price

    return None


def send_email(message: str):
    smtp_server = os.environ.get('SMTP_SERVER_URI')
    port = os.environ.get('SMTP_SERVER_PORT')
    email_user = os.environ.get('EMAIL_USER')
    email_user_pw = os.environ.get('EMAIL_USER_PW')

    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(email_user, email_user_pw)

        server.sendmail(
            os.environ.get('SENDER_EMAIL'),
            os.environ.get('RECEIVER_EMAIL'),
            message
        )
    except Exception as e:
        logging.error(e)
    finally:
        server.quit()


def process_alert(idx: int, alert: dict):
    ticker_price = get_cached_ticker_prices(alert['market'])

    if ticker_price is None:
        ticker_price = bitvavo.tickerPrice({'market': alert['market']})
        cached_ticker_prices.append(ticker_price)

    if 'price' not in ticker_price:
        return

    price = Decimal(ticker_price['price'])

    if alert['status'] == "hit":
        return

    # first time
    if alert['status'] is None:
        alerts[idx]['init_price'] = price
        alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alerts[idx]['status'] = 'active'

        return

    # trailing price hit
    if price <= alert['trailing_price']:
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        send_email(json.dumps(alert, indent=4, sort_keys=True))

    # price increased
    if price > alert['price']:
        alerts[idx]['trailing_price'] = price * Decimal(alert['trailing_percentage'])
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return

    # price decreased
    if price <= alert['price']:
        alerts[idx]['price'] = price
        alerts[idx]['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return


bitvavo = Bitvavo({
    'APIKEY': os.environ.get('APIKEY'),
    'APISECRET': os.environ.get('APISECRET')
})

with open(alerts_file_name, 'r') as fp:
    alerts = json.load(fp, parse_float=get_decimal)

if not alerts:
    exit(0)

for idx, alert in enumerate(alerts):
    process_alert(idx, alert)

with open(alerts_file_name, 'w') as fp:
    json.dump(alerts, fp, indent=4, sort_keys=True)
