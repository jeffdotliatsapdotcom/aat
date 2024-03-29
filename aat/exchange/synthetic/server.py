import asyncio
import os
import ujson  # type: ignore
import uvloop  # type: ignore
from websockets import serve  # type: ignore
from aat.exchange.synthetic import SyntheticExchange
from aat.core import Order
from aat.config import TradingType


def _main(port: int = 5000):  # type: ignore
    async def handle(websocket, *args, **kwargs):  # type: ignore
        exchange = SyntheticExchange(trading_type=TradingType.SIMULATION)
        await exchange.connect()
        await exchange.instruments()

        while True:
            for item in exchange.snapshot():
                print("sending snapshot: {}".format(item))
                await websocket.send(ujson.dumps(item.json()))

            async for item in exchange.tick(snapshot=True):
                print("sending {}".format(item))
                await websocket.send(ujson.dumps(item.json()))
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    order = Order.from_json(ujson.loads(data))
                    print("received order: {}".format(order))
                    ret = await exchange.newOrder(order)
                    await websocket.send(ujson.dumps(ret.json()))
                except asyncio.TimeoutError:
                    pass

    start_server = serve(handle, "0.0.0.0", port)
    print("listening on %d" % port)
    return start_server


def main() -> None:
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.get_event_loop().run_until_complete(
            _main(int(os.environ.get("PORT", "5000")))
        )
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("terminating...")
