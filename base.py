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
    timeunit = 60    # :: int    定时任务频率限制计时周期单位(s)
    interval = 1.0   # :: float  定时周期(s)
    loopCount = 0    # :: int    已执行的定时周期数
    rateLimit = 30   # :: int    短请求频率限制(每个计时周期内允许的短请求次数)
    rateCount = 0    # :: int    计时周期内的已短请求次数
    keepList = []    # :: [awf]  长连接请求列表
    sendList = []    # :: [aw]   短请求列表
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
        self.logger = logging.getLogger('asyncio')

        self.loggingConfig()

    # logging模块配置: 格式及日志级别
    def loggingConfig(self):
        FORMAT = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=FORMAT)
        self.logger.setLevel(logging.DEBUG)

    # ----------------- 定时及短连接支持 -----------------

    # 定时任务
    def loop(self):
        self.logger.info(
            f'[LOOP {self.loopCount}][RUNTIME {round(self.loopCount * self.interval, 2)}][KEEP {len(self.keepList)}][SEND {len(self.sendList)}][RATECOUNT {self.rateCount}/{self.rateLimit}]'
        )

    # 定时任务协程
    async def _loop(self):
        self.loopCount = 0
        while True:
            self.loop()
            self._send()
            await asyncio.sleep(self.interval)
            self.loopCount += 1

    # 短连接请求协程
    def _send(self):
        asyncio.gather(*self.sendList)
        self.sendList = []

        # 到下一周期时清零rateCount
        if (self.loopCount * self.interval) % self.timeunit < 1:
            self.rateCount = 0

    # 添加一次短连接定时请求(awf :: () -> aw)
    def addSend(self, awf, cb, eb):
        # 未达到上限时添加一次定时请求，否则丢弃定时请求
        if self.rateCount < self.rateLimit:
            self.rateCount += 1
            self.sendList.append(addCallbacks(awf(), cb, eb))
    # --------------------------------------------------

    # -------------------- 长连接支持 --------------------

    # 添加一个长连接请求(awf :: () -> aw)
    def addKeep(self, awf):
        self.keepList.append(awf)

    # 长连接请求协程
    async def _startKeep(self, awf):
        try:
            await awf()
        except:
            print("ERROR retry in 1s")
            await asyncio.sleep(1)

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

