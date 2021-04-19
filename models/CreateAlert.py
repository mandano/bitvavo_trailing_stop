import sys
import simplejson as json
import os
from decimal import Decimal
from models.Alert import Alert
from models.clients.Bitvavo import BitvavoClient


class CreateAlert(object):
    _client: BitvavoClient = None
    file_name: str = 'new_alert.json'
    alerts_file_path: str = None

    alert = None

    actions: list = None
    alert_init_price = None
    alert_trailing_percentage = None
    market = None

    actions_selection = None
    init_price_type = None
    market_selection_type = None

    def __init__(self, **kwargs):
        self.actions = []
        self.alerts_file_path = os.environ.get('ALERTS_FILE_PATH')

        if 'test_create_alert_logic' not in sys.argv[1]:
            if len(sys.argv) > 1:
                self.alert_trailing_percentage = Decimal(sys.argv[1])

            if len(sys.argv) > 2:
                self.market_selection_type = sys.argv[2]

            if len(sys.argv) > 3:
                self.market = sys.argv[3]

            if len(sys.argv) > 4:
                self.actions_selection = sys.argv[4]

            if len(sys.argv) > 5:
                self.init_price_type = Decimal(sys.argv[5])

            if len(sys.argv) > 6:
                self.alert_init_price = Decimal(sys.argv[6])

        self.alerts_file_path = os.environ.get('ALERTS_FILE_PATH')

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def save_alert(self):
        with open(self.alerts_file_path + self.file_name, 'w') as fp:
            json.dump(self.alert.attributes(), fp, indent=4, sort_keys=True, default=str)

    def add_by_console(self):
        if os.path.isfile(self.file_name):
            print("Pending new alert, try again please (Updating process probably didn't yet pick up new alert).")

            exit(1)

        print('Input new alert data:')
        print('---------------------')

        if self.market is None:
            self.choose_market()

        print('Add new init price:')
        print(' [1] Use manual value')
        print(' [2] Set by market')

        if self.init_price_type is None:
            self.init_price_type = input()

        if self.init_price_type == '1' and self.alert_init_price is None:
            print('Type in your value for init price as string like "2345.43"')
            self.alert_init_price = Decimal(input())

        if self.alert_trailing_percentage is None:
            print('Insert trail in percentage like ["0.9", "0.45"]')
            self.alert_trailing_percentage = Decimal(input())

        if self.actions_selection is None:
            print('Which actions should be activated?')
            print('[1] Send e-mail')
            print('[2] Sell')
            print('[3] Send e-mail and sell')

            self.actions_selection = input()

        if self.actions_selection == '1':
            self.actions.append(Alert.ACTION_SEND_EMAIL)
        if self.actions_selection == '2':
            self.actions.append(Alert.ACTION_SELL_ASSET)
        elif self.actions_selection == '3':
            self.actions.extend([
                Alert.ACTION_SEND_EMAIL,
                Alert.ACTION_SELL_ASSET
            ])

        self.alert = Alert(
            actions=self.actions,
            init_price=self.alert_init_price,
            trailing_percentage=self.alert_trailing_percentage,
            market=self.market,
            _client=self._client
        )

        self.alert.update_by_client()
        self.save_alert()

        print('New alert created.')
        print(self.alert.attributes())

    def choose_market(self):
        print('Choose market, like "ETH-EUR"')
        print(' [1] Type in your market string')
        print(' [2] List supported markets')

        self.market_selection_type = input()

        if self.market_selection_type == '1':
            print('Type in your market string')
            self.market = input()
        elif self.market_selection_type == '2':
            markets = self._client.get_markets()

            print('Supported markets:')
            print(json.dumps(markets, indent=4, sort_keys=True))

            self.market = self.choose_market()
        else:
            print('Input not recognized.')
            exit(1)

        if not self.is_market_supported(self.market):
            print('Market string not supported.')
            exit(1)

        return self.market

    def is_market_supported(self, market):
        remote_market = self._client.get_markets(market)

        if \
                'market' in remote_market and \
                market == remote_market['market'] and \
                'trading' == remote_market['status']:
            return True

        return False
