import asyncio
from base import Exchange, addCallbacks, RobotBase

exchange = Exchange()

class Market(RobotBase):

    async def show(self, result):
        self.logger.info(result)
        return result

def next(rbt, name):
    async def awf(result):
        rbt.logger.info(result)
        rbt.addSend(exchange.sayHello(f'{name}[{rbt.loopCount}]'), next(rbt, name), next(rbt, name))
    return awf

mk = Market(rateLimit=100, interval=1, timeunit=60, debug=True)

mk.addSend(mk.idle(), next(mk, 'Nouzan'), next(mk, 'Nouzan'))
mk.addSend(mk.idle(), next(mk, 'Koala'), next(mk, 'Koala'))

URI = ""
DATA = {}
mk.addKeep(exchange.keepWaitting(mk.show))
# mk.addKeep(exchange.testEx(URI, DATA, mk.show))
mk.run()