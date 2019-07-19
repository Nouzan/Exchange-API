import asyncio
import logging
from base import Exchange, addCallbacks, RobotBase

TIMEUNIT = 60
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

logging.getLogger('asyncio').setLevel(logging.DEBUG)
exchange = Exchange()

def show(result):
    logging.getLogger('asyncio').info(result)
    return result

class Market(RobotBase):
    def __init__(self, rateLimit):
        self.rateLimit = rateLimit # 每{TIMEUNIT}秒可进行的请求数
        self.rateCount = 0         # 记录请求数
        self.sendList = []         # 本轮发送的请求列表

    def addSend(self, awf, cb, eb):
        if self.rateCount < self.rateLimit:
            self.rateCount += 1
            self.sendList.append(addCallbacks(awf(), cb, eb))

    def send(self):
        aw = asyncio.gather(*self.sendList)
        self.sendList = []
        if (self.loopCount * self.interval) % TIMEUNIT < 1:
            self.rateCount = 0
        return aw

    def loop(self):
        self.addSend(exchange.sayHello(f'Nouzan[{self.loopCount}]'), show, show)
        self.addSend(exchange.sayHello(f'Koala[{self.loopCount}]'), show, show)
        logging.getLogger('asyncio').info(
            f'[LOOP {self.loopCount}][RUNTIME {round(self.loopCount * self.interval, 2)}][LEN {len(self.sendList)}][RATECOUNT {self.rateCount}/{self.rateLimit}]'
        )
        self.send()

mk = Market(100)
mk.addKeep(exchange.keepWaitting(show))
print(mk.keepList)
asyncio.run(mk.run(1), debug=False)