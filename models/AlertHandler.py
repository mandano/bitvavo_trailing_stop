import datetime
import logging
from pathlib import Path
import simplejson
import simplejson as json
import os
from decimal import Decimal
from models.Alert import Alert
from models.Messages import Messages
from models.Trade import Trade
from models.clients.Bitvavo import BitvavoClient


class AlertHandler(object):
    alerts_file_name: str = None
    new_alert_file_name: str = None
    alerts_file_path: str = None
    alerts = list()
    _ticker_prices = {}

    def __init__(self, **kwargs):
        self.alerts_file_name = os.environ.get('ALERTS_FILE_NAME')
        self.alerts_file_path = os.environ.get('ALERTS_FILE_PATH')
        self.new_alert_file_name = os.environ.get('NEW_ALERTS_FILE_NAME')

        for k, v in kwargs.items():
            self.__setattr__(k, v)

        if not self.alerts:
            self.load_alerts()

    def load_alerts(self):
        alerts = list()

        try:
            with open(self.alerts_file_path + self.alerts_file_name, 'r') as fp:
                alerts = json.load(fp, parse_float=self.get_decimal, parse_int=self.get_decimal)
        except FileNotFoundError:
            logging.info('No alert file.')
            Path(self.alerts_file_path + self.alerts_file_name).touch()
            logging.info('Created alert file.')

            return
        except simplejson.errors.JSONDecodeError as e:
            logging.info(e)

        if not alerts:
            logging.warning("No alerts set.")

        for idx, alert in enumerate(alerts):
            alert = Alert(
                actions=alert['actions'],
                amount=alert['amount'],
                dt=datetime.datetime.strptime(alert['dt'], "%Y-%m-%d %H:%M:%S.%f"),
                init_dt=datetime.datetime.strptime(alert['init_dt'], "%Y-%m-%d %H:%M:%S.%f"),
                init_price=alert['init_price'],
                market=alert['market'],
                price=alert['price'],
                status=alert['status'],
                trailing_percentage=alert['trailing_percentage'],
                trailing_price=alert['trailing_price'],
                _client=BitvavoClient(
                    market=alert['market']
                )
            )

            self.alerts.append(alert)

    def save_alerts(self):
        alerts = list()

        for idx, alert in enumerate(self.alerts):
            alerts.append(alert.attributes())

        with open(self.alerts_file_path + self.alerts_file_name, 'w') as fp:
            json.dump(alerts, fp, indent=4, sort_keys=True, default=str)

    @classmethod
    def get_decimal(cls, s):
        return Decimal(s)

    def update_alerts(self):
        for idx, alert in enumerate(self.alerts):
            """if alert.market in self._ticker_prices:
                self.alerts[idx]._client._response_ticker_price = {
                    'price': self._ticker_prices[alert.market],
                    'market': alert.market
                }"""

            updated = self.alerts[idx].update_by_client()

            if updated is False:
                continue

            if self.alerts[idx].status != self.alerts[idx].STATUS_HIT:
                continue

            if self.alerts[idx].is_ticker_price_diverted():
                Messages.send_email(
                    json.dumps(
                        {
                            "alert_price": self.alerts[idx].price,
                            "backup_price": self.alerts[idx].backup_price
                        },
                        indent=4,
                        sort_keys=True,
                        default=str
                    ),
                    'Ticker price diversion'
                )

                continue

            if Alert.ACTION_SELL_ASSET in self.alerts[idx].actions:
                trade = Trade(
                    _client=BitvavoClient(market=self.alerts[idx].market),
                    _alert=self.alerts[idx]
                )
                trade.sell()

            if Alert.ACTION_SEND_EMAIL in self.alerts[idx].actions:
                Messages.send_email(json.dumps(self.alerts[idx].attributes(), indent=4, sort_keys=True, default=str))
