import asyncio
import websockets
import random

async def hello(websocket, path):
    name = await websocket.recv()
    if name == 'KEEP':
        while True:
            await asyncio.sleep(random.randint(5, 10))
            for i in range(10):
                await asyncio.sleep(0.5)
                await websocket.send('KEEP')
            print(f'> KEEP')
    print(f'< {name}')

    greeting = f'Hello {name}!'

    await websocket.send(greeting)
    print(f"> {greeting}")


startServer = websockets.serve(hello, 'localhost', 8123)

asyncio.get_event_loop().run_until_complete(startServer)
asyncio.get_event_loop().run_forever()
