import asyncio
from base import Exchange, addCallbacks, RobotBase

exchange = Exchange()

class Market(RobotBase):

    def show(self, result):
        self.logger.info(result)
        return result

    def loop(self):
        self.addSend(exchange.sayHello(f'Nouzan[{self.loopCount}]'), self.show, self.show)
        self.addSend(exchange.sayHello(f'Koala[{self.loopCount}]'), self.show, self.show)
        self.logger.info(
            f'[LOOP {self.loopCount}][RUNTIME {round(self.loopCount * self.interval, 2)}][KEEP {len(self.keepList)}][SEND {len(self.sendList)}][RATECOUNT {self.rateCount}/{self.rateLimit}]'
        )

mk = Market(rateLimit=100, interval=1, timeunit=60)
mk.addKeep(exchange.keepWaitting(mk.show))
URI = ""
DATA = {}
# mk.addKeep(exchange.testEx(URI, DATA, mk.show))
mk.run()