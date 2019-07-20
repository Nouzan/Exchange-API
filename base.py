import asyncio
import websockets
import aiohttp
import random
import logging

# 为异步任务添加回调
# addCallbacks :: awf a -> (a -> aw b) -> (Error -> aw b) -> awf b
def addCallbacks(awf, callback=None, errback=None):
    async def _awf():
        try:
            result = await awf()
        except Exception as err:
            if errback is not None:
                return await errback(err)
            else:
                return err
        else:
            if callback is not None:
                return await callback(result)
            else:
                return result
    return _awf

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
                    await comsumer(message)
        return awf

    def testEx(self, uri, data, comsumer):
        import json
        async def awf():
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps(data))
                async for message in ws:
                    await comsumer(message)
        return awf


class RobotBase(object):
    timeunit = 60    # :: int    定时任务频率限制计时周期单位(s)
    interval = 1.0   # :: float  定时周期(s)
    loopCount = 0    # :: int    已执行的定时周期数
    rateLimit = 30   # :: int    短请求频率限制(每个计时周期内允许的短请求次数)
    rateCount = 0    # :: int    计时周期内的已短请求次数
    keepList = []    # :: [awf]  长连接请求列表
    sendList = []    # :: [awf]  短请求列表
    waitList = []    # :: [awf]  推迟短请求列表
    logger = None    # :: Logger 日志对象
    debug = False    # :: bool   是否启动调试

    def __init__(self, rateLimit=60, interval=1.0, timeunit=60, debug=False):
        self.timeunit = timeunit
        self.interval = interval
        self.rateLimit = rateLimit
        self.loopCount = 0
        self.rateCount = 0
        self.keepList = []
        self.sendList = []
        self.waitList = []
        self.logger = logging.getLogger('asyncio')

        self.loggingConfig()

    # logging模块配置: 格式及日志级别
    def loggingConfig(self):
        FORMAT = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=FORMAT)
        self.logger.setLevel(logging.DEBUG)

    def idle(self):
        async def awf():
            return "[IDLE]"
        return awf

    # ----------------- 定时及短连接支持 -----------------

    # 首次任务
    async def init(self):
        self.logger.info(
            f'[INIT]'
        )

    # 定时任务(必须是非阻塞的，才能保证定时任务确实是定时执行的)
    def loop(self):
        self.logger.info(
            f'[LOOP {self.loopCount}][RUNTIME {round(self.loopCount * self.interval, 2)}][KEEP {len(self.keepList)}][SEND {len(self.sendList)}][WAIT {len(self.waitList)}][RATECOUNT {self.rateCount}/{self.rateLimit}]'
        )

    # 短连接请求协程
    def _send(self):
        asyncio.gather(
            *[awf() for awf in self.sendList]
        )
        self.sendList = []

        # 到下一周期时清零rateCount，并将waitList中的任务转移到sendList
        if (self.loopCount * self.interval) % self.timeunit < 1:
            self.rateCount = 0
            if len(self.waitList) <= self.rateLimit:
                self.sendList += self.waitList
                self.waitList = []
                self.rateCount = len(self.sendList)
            else:
                self.sendList = self.waitList[:self.rateLimit]
                self.waitList = self.waitList[self.rateLimit:]
                self.rateCount = len(self.sendList)

    # 定时任务协程
    async def _loop(self):
        self.loopCount = 0
        await self.init()
        while True:
            self.loop()
            self._send()
            await asyncio.sleep(self.interval)
            self.loopCount += 1

    # 添加一次短连接定时请求(awf :: () -> aw)
    def addSend(self, awf, callback, errback):
        # 未达到上限时添加一次定时请求，否则添加到推迟列表
        if self.rateCount < self.rateLimit:
            self.rateCount += 1
            self.sendList.append(addCallbacks(awf, callback, errback))
        else:
            self.waitList.append(addCallbacks(awf, callback, errback))
    # --------------------------------------------------

    # -------------------- 长连接支持 --------------------

    # 添加一个长连接请求(awf :: () -> aw)
    def addKeep(self, awf):
        self.keepList.append(awf)

    # 长连接请求协程
    async def _startKeep(self, awf):
        async def errback(error):
            print("ERROR! Retry in 1s")
            await asyncio.sleep(1)
            return error
        await addCallbacks(awf, errback=errback)()

    # 长连接守护协程
    async def _startKeepForever(self, awf):
        while True:
            await self._startKeep(awf)

    # 运行全部长连接请求的协程
    async def _keep(self):
        await asyncio.gather(
            *[self._startKeepForever(awf) for awf in self.keepList]
        )

    # --------------------------------------------------

    # 启动定时及长连接的协程
    async def _run(self):
        await asyncio.gather(
            self._loop(),
            self._keep()
        )

    # 启动
    def run(self):
        asyncio.run(self._run(), debug=self.debug)

