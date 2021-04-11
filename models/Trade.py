import simplejson as json
from models.Alert import Alert
from models.Messages import Messages
from models.clients.Bitvavo import BitvavoClient


class Trade(object):
    _client: BitvavoClient = None
    _alert: Alert = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def sell(self):
        symbol = self._alert.get_symbol()

        if symbol is None:
            return False

        if self._alert.amount is None:
            amount = self._client.get_balance(symbol)
        else:
            amount = self._alert.amount

        response = self._client.place_order(
            BitvavoClient.SIDE_SELL,
            BitvavoClient.ORDER_TYPE,
            str(amount)
        )

        Messages.send_email(json.dumps(response, indent=4, sort_keys=True), "Sell request result.")

        if 'orderId' in response:
            return True

        return False
