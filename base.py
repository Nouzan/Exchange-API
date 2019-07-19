import asyncio
import websockets
import aiohttp
import random
import logging

# 为异步任务添加回调
# addCallbacks :: Awaitable a -> (a -> b) -> (Error -> b) -> Awaitable b
async def addCallbacks(aw, callback=None, errback=None):
    try:
        result = await aw
    except Exception as err:
        if errback is not None:
            return errback(err)
        else:
            return err
    else:
        if callback is not None:
            return callback(result)
        else:
            return result

class Exchange(object):
    def sayHello(self, name):
        async def awf():
            uri = "ws://localhost:8123"
            async with websockets.connect(uri) as ws:
                await ws.send(name)
                return await ws.recv()
        return awf

    def keepWaitting(self, comsumer):
        async def awf():
            uri = "ws://localhost:8123"
            async with websockets.connect(uri) as ws:
                await ws.send('KEEP')
                async for message in ws:
                    comsumer(message)
        return awf


class RobotBase(object):
    interval = None
    loopCount = None
    keepList = []

    def loop(self):
        print(f"Looping {self.loopCount}")

    def addKeep(self, awf):
        self.keepList.append(awf)

    async def _startKeep(self, awf):
        try:
            await awf()
        except:
            print("ERROR retry in 1s")
            await asyncio.sleep(1)
        finally:
            await self._startKeep(awf)
    
    async def _loop(self, interval=1):
        self.interval = interval
        self.loopCount = 0
        while True:
            self.loop()
            await asyncio.sleep(self.interval)
            self.loopCount += 1

    async def _keep(self):
        await asyncio.gather(
            *[self._startKeep(awf) for awf in self.keepList]
        )

    async def run(self, interval=1):
        await asyncio.gather(
            self._loop(interval),
            self._keep()
        )

