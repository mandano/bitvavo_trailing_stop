import os
from decimal import Decimal

from python_bitvavo_api.bitvavo import Bitvavo

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '/.env')
load_dotenv('.env')

bitvavo = Bitvavo({
    'APIKEY': os.environ.get('APIKEY'),
    'APISECRET': os.environ.get('APISECRET')
})

response = bitvavo.trades('ETH-EUR', {})

amount = Decimal()

for item in reversed(response):
    if item['side'] == 'buy':
        amount += Decimal(item['amount'])

    if item['side'] == 'sell':
        amount -= Decimal(item['amount'])

    pass

logging_level = os.environ.get("LOGGING_LEVEL")
