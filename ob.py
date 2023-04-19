#pip install websocket
#pip install websocket-client

import websocket
import numpy as np
import json
import matplotlib.pyplot as plt
import threading
import time

url = 'wss://ws-feed.exchange.coinbase.com'

class Data:

    bids = {}
    asks = {}

    sync = False
    no = 0

    def summation(self, depth=5):
        res = {}
        for tick in self.tickers:
            if tick in self.bids.keys() and tick in self.asks.keys():
                bids = self.bids[tick]
                asks = self.asks[tick]
                bids = list(sorted(bids.items(), reverse=True))[:depth]
                asks = list(sorted(asks.items()))[:depth]
                
                
                bp, bv = np.array(bids).T.tolist()
                ap, av = np.array(asks).T.tolist()
                sum_bv = [float(np.sum(bv[:i])) for i in range(depth)]
                sum_av = [float(np.sum(av[:i])) for i in range(depth)]
                res[tick] = {'bid_x': bp[::-1], 'bid_y': sum_bv[::-1],
                            'ask_x': ap, 'ask_y':sum_av}
        return res
        

    def parseBook(self, resp):
        if 'type' in resp.keys():
            if resp['type'] == 'snapshot':
                ticker = resp['product_id']
                self.bids[ticker] = {float(price):float(volume) for (price, volume) in resp['bids']}
                self.asks[ticker] = {float(price):float(volume) for (price, volume) in resp['asks']}
                self.no += 1
                if self.no == len(self.tickers):
                    self.sync = True
            if resp['type'] == 'l2update':
                ticker = resp['product_id']
                for (side, price, volume) in resp['changes']:
                    price, volume = float(price), float(volume)
                    if side == 'buy':
                        if volume == 0:
                            del self.bids[ticker][price]
                        else:
                            self.bids[ticker][price] = volume
                    if side == 'sell':
                        if volume == 0:
                            del self.asks[ticker][price]
                        else:
                            self.asks[ticker][price] = volume


        

class OBook(threading.Thread, Data):

    def __init__(self, tickers=['BTC-USD','ETH-USD']):
        threading.Thread.__init__(self)
        self.tickers = tickers

    def run(self):
        conn = websocket.create_connection(url)

        msg = {'type':'subscribe',
               'product_ids': self.tickers,
               'channels': ['level2']}

        conn.send(json.dumps(msg))

        while True:
            response = json.loads(conn.recv())
            self.parseBook(response)
            self.summation()


fig = plt.figure(figsize=(10, 5))
btc = fig.add_subplot(121)
eth = fig.add_subplot(122)

cbook = OBook()
cbook.start()

while True:
    if cbook.sync == True:
        items = cbook.summation(depth=30)
        btc.cla()
        btc.set_title("Bitcon Orderbook")
        btc.plot(items['BTC-USD']['bid_x'], items['BTC-USD']['bid_y'], color='red')
        btc.plot(items['BTC-USD']['ask_x'], items['BTC-USD']['ask_y'], color='limegreen')

        eth.cla()
        eth.set_title("Ethereum Orderbook")
        eth.plot(items['ETH-USD']['bid_x'], items['ETH-USD']['bid_y'], color='red')
        eth.plot(items['ETH-USD']['ask_x'], items['ETH-USD']['ask_y'], color='limegreen')
        
        plt.pause(0.0001)



plt.show()