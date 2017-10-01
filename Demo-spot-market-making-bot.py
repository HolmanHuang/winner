import hmac
import hashlib
import json
import uuid
import random
import time
import requests # pip install requests
import logging

def get_logger():
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = get_logger()

class CoinutAPI():
    def __init__(self, user = None, api_key = None):
        self.user = user
        self.api_key = api_key

    def request(self, api, content = {}):
        url = 'https://api.coinut.com'
        headers = {}
        content["request"] = api
        content["nonce"] = random.randint(1, 1000000000)
        content = json.dumps(content)
        logger.debug(content.strip())

        if self.api_key is not None and self.user is not None:
            key_bytes = bytes(self.api_key,'latin-1')
            data_bytes = bytes(content,'latin-1')
            sig = hmac.new(key_bytes, data_bytes,
                           digestmod=hashlib.sha256).hexdigest()
            headers = {'X-USER': self.user, "X-SIGNATURE": sig}

        response = requests.post(url, headers=headers, data=content)
        logger.debug(response.text.strip())
        return response.json()

    def get_spot_instruments(self, pair = None):
        result = self.request("inst_list", {'sec_type': 'SPOT'})
        if pair != None:
            return result['SPOT'][pair][0]
        else:
            return result['SPOT']

    def get_existing_orders(self, inst_id):
        return self.request("user_open_orders", {"inst_id": inst_id})['orders']

    def cancel_orders(self, inst_id, ids):
        ords = [{'inst_id': inst_id, 'order_id': x} for x in ids]
        return self.request("cancel_orders", {'entries': ords})

    def submit_new_orders(self, ords):
        return self.request("new_orders", {"orders": ords})

    def submit_new_order(self, inst_id, side, qty, price):
        return self.request("new_order", self.new_order(inst_id, side, qty, price))

    def new_order(self, inst_id, side, qty, price = None):
        order = {
            'inst_id': inst_id,
            "side": side,
            'qty': "%.8f" % qty,
            'price': "%.8f" % price,
            'client_ord_id': random.randint(1, 4294967290)
        }

        return order

    def cancel_all_orders(self, inst_id):
        ords = api.get_existing_orders(inst_id)
        self.cancel_orders(inst_id, [x['order_id'] for x in ords])

    def balance(self):
        return self.request("user_balance")

# can not use anymore
def get_btce_ltcusd():
    try:
        res = requests.get("https://btc-e.com/api/3/ticker/ltc_btc", timeout=5)
        return res.json()["ltc_btc"]["last"]
    except:
        return 0.0


def get_bitfinex_ltcusd():
    try:
        # help information:
        # Get API from https://www.bitfinex.com/api
        res = requests.get("https://api.bitfinex.com/v2/tickers?symbols=tLTCBTC", timeout=5)
        return res.json()[0][7]
    except:
        return 0.0

def get_bitstamp_ltcusd():
    try:
        res = requests.get("https://btc-e.com/api/3/ticker/ltc_btc", timeout=5) #TODO:
        return res.json()["ltc_btc"]["last"]
    except:
        return 0.0

def get_kraken_ltcusd():
    try:
        res = requests.get("https://btc-e.com/api/3/ticker/ltc_btc", timeout=5) #TODO:
        return res.json()["ltc_btc"]["last"]
    except:
        return 0.0

def get_poloniex_ltcusd():
    try:
        res = requests.get("https://btc-e.com/api/3/ticker/ltc_btc", timeout=5) #TODO:
        return res.json()["ltc_btc"]["last"]
    except:
        return 0.0

api = CoinutAPI("xxxx", "xxx") # in the profile
bal = api.balance()
logger.info("Balance: LTC=%s, BTC=%s" % (bal['LTC'], bal['BTC']))

LTCBTC_ID = api.get_spot_instruments('LTCBTC')['inst_id']
logger.info("LTCBTC instrument id: %d" % LTCBTC_ID)

mid_price = 0
while True:
    bitfinex_last_price = get_bitfinex_ltcusd()
    if bitfinex_last_price == 0.0:
        logger.error("bitfinex price error")
        continue
    else:
        logger.info("bitfinex price %f", bitfinex_last_price)

    # if the price on bitfinex did not change much, we don't move either;
    # otherwise, we cancel existing orders and place new orders

    if abs(mid_price - bitfinex_last_price) < 0.00001:
        continue

    # cancel all existing orders
    logger.info("cancel all orders")
    api.cancel_all_orders(LTCBTC_ID)

    mid_price = bitfinex_last_price
    spread = mid_price * 0.002 # to improve this factor to be the total balance

    # place a blanket of orders around the mid_price
    ords = []
    for i in range(1, 10):
        bid = mid_price - i * spread / 2
        ask = mid_price + i * spread / 2
        qty = 0.0001

        logger.info("BUY  %f @ %s" % (qty, bid))
        buy_order = api.new_order(LTCBTC_ID, 'BUY', qty, bid)  # the quantity is all for LTC when BUY & SELL?
        ords.append(buy_order)

        logger.info("SELL %f @ %s" % (qty, ask))
        sell_order = api.new_order(LTCBTC_ID, 'SELL', qty, ask)
        ords.append(sell_order)

    # submit the orders in batch mode
    api.submit_new_orders(ords)

    time.sleep(1) #bitfinex API requires no larger than 90 times query per minute
    bal = api.balance()
    logger.info("Balance: LTC=%s, BTC=%s, Equal LTC=%s" % (bal['LTC'], bal['BTC'], float(bal['LTC'])+ float(bal['BTC']) / bitfinex_last_price))
