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

        response = requests.post(url, headers=headers, data=content,timeout=15)
        logger.debug(response.text.strip())
        return response.json()

    def get_spot_instruments(self, pair = None):
        result = self.request("inst_list", {'sec_type': 'SPOT'})
        if pair != None:
            return result['SPOT'][pair][0]
        else:
            return result['SPOT']

    #{"request": "inst_tick", "inst_id": 1, "subscribe": true, "nonce": 615146544}
    '''
    {
        "highest_buy": "750.58100000",
        "inst_id": 1,
        "last": "752.00000000",
        "lowest_sell": "752.00000000",
        "open_interest": "0.00000000",
        "reply": "inst_tick",
        "timestamp": 1481355058109705,
        "trans_id": 170064,
        "volume": "0.07650000",
        "volume24": "56.07650000"
    }
    '''

    def get_realtime_ticks(self, inst_id):
        return self.request("inst_tick", {"inst_id": inst_id})

    '''
    {
    "nonce": 237368387,
    "reply": "user_open_orders",
    "status": [
        "OK"
    ],
    "orders": [
        {
            "order_id": 35,
            "open_qty": "0.01000000",
            "price": "750.58200000",
            "inst_id": 1,
            "client_ord_id": 4,
            "timestamp": 1481138766081720,
            "qty": "0.01000000",
            "side": "BUY"
        },
        {
            "order_id": 30,
            "open_qty": "0.01000000",
            "price": "750.58100000",
            "inst_id": 1,
            "client_ord_id": 5,
            "timestamp": 1481137697919617,
            "qty": "0.01000000",
            "side": "BUY"
        }
    ]
    }
    '''
    
    def get_inst_order_book(self,inst_id):
        return self.request("inst_order_book",{"inst_id":inst_id})


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

api = CoinutAPI("xxxxxxxx", "yyyyyyyyy")
bal = api.balance()
logger.info("WINN:Balance: LTC=%s, BTC=%s" % (bal['LTC'], bal['BTC']))

LTCBTC_ID = api.get_spot_instruments('LTCBTC')['inst_id']
logger.info("LTCBTC instrument id: %d" % LTCBTC_ID)

mid_price = 0
last_order_time = time.time() 
while True:
    coinut_realtime_ticks = api.get_realtime_ticks(LTCBTC_ID)
    coinut_last_price = float(coinut_realtime_ticks['last'])
    if coinut_last_price == 0.0:
        logger.error("WINN:coinut last price error")
        time.sleep(1)
        continue
    else:
        #logger.info("WINN:coinut last price %s", coinut_last_price)
        logger.info("WINN:RealTime ticks:{}".format(coinut_realtime_ticks))

    coinut_inst_order_book = api.get_inst_order_book(LTCBTC_ID)
    logger.info("Inst Order buy:{}".format(coinut_inst_order_book["buy"][0])+"Sell:{}".format(coinut_inst_order_book["sell"][0]))
    # the buy side is block and sell side is not block


    my_buy_adjust = 0
    my_sell_adjust = 0
    if float(coinut_inst_order_book["buy"][0]["qty"]) > 100 and float(coinut_inst_order_book["sell"][0]["qty"]) < 10:
        coinut_last_price = float(coinut_inst_order_book["buy"][0]["price"])+0.00001
        my_buy_adjust = 1
        my_sell_adjust = 0

    if float(coinut_inst_order_book["sell"][0]["qty"]) > 100 and float(coinut_inst_order_book["buy"][0]["qty"]) < 10:
       coinut_last_price = float(coinut_inst_order_book["sell"][0]["price"])-0.00001 
       my_sell_adjust =1 
       my_buy_adjust = 0


    # if the price on coinut did not change much, we don't move either;
    # otherwise, we cancel existing orders and place new orders

    # now i don't have any buy and sell order, start
    # long time no trade, restart
    # price change a lot , restart
    
    existing_orders = api.get_existing_orders(LTCBTC_ID)
    logger.info("WINN:Existing Orders:{}".format(existing_orders)+"time@%f,now@%f,mid_price:%f,last_price:%f",last_order_time,time.time(),mid_price,coinut_last_price)
    if (len(existing_orders) > 0) and (abs(mid_price - coinut_last_price) < 0.00005) and (time.time()-last_order_time < 180):
        continue

    mid_price = coinut_last_price # if use this price, the trading will be blocked if SELL/BUY one side is blocked
    spread = 0.00001 # to improve this factor to be the total balance
    
    #cancel all existing orders
    #logger.info("WINN:cancel all orders: ",existing_orders)
    api.cancel_all_orders(LTCBTC_ID)
    existing_orders = api.get_existing_orders(LTCBTC_ID)
    #logger.info("WINN:Exising Orders after cancel: %f", len(existing_orders))	

    # place a blanket of orders around the mid_price
    ords = []
    for i in range(1, 2):

	

        my_buy = mid_price - (i-my_buy_adjust) * spread  
        my_sell = mid_price  + (i-my_sell_adjust) * spread 
        qty = 0.00001


        logger.info("WINN:BUY  %f @ %s" % (qty, my_buy))
        buy_order = api.new_order(LTCBTC_ID, 'BUY', qty, my_buy)  # the quantity is all for LTC when BUY & SELL
        ords.append(buy_order)

        logger.info("WINN:SELL %f @ %s" % (qty, my_sell))
        sell_order = api.new_order(LTCBTC_ID, 'SELL', qty, my_sell)
        ords.append(sell_order)

    # submit the orders in batch mode
    api.submit_new_orders(ords)
    last_order_time = time.time()

    #time.sleep(1) #bitfinex API requires no larger than 90 times query per minute
    bal = api.balance()
    logger.info("WINN:Balance: LTC=%s, BTC=%s, Equal LTC=%s" % (bal['LTC'], bal['BTC'], float(bal['LTC'])+ float(bal['BTC']) / coinut_last_price))
