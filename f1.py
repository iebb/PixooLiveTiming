import asyncio
import collections
import logging
import time

import mergedeep
from signalr_async.net import Hub
from signalr_async.net.client import SignalRClient

from scoreboard import Scoreboard
from mergedeep import merge

logging.basicConfig(level=logging.DEBUG)
s = Scoreboard()


class F1SignalRClient(SignalRClient):
    driver_list = collections.defaultdict(dict)
    driver_timing = collections.defaultdict(dict)

    def LapCount(self, lc):
        pass

    def SessionData(self, sd):
        pass

    def DriverList(self, drivers):
        for driver_number in drivers:
            if isinstance(drivers[driver_number], dict):
                mergedeep.merge(self.driver_list[driver_number], drivers[driver_number])

    def TimingData(self, timing):
        for driver_number in timing["Lines"]:
            driver = self.driver_list[driver_number]
            driver_timing = mergedeep.merge(self.driver_timing[driver_number], timing["Lines"][driver_number])
            gap = ''
            color = driver['TeamColour']
            if not color:
                color = 'ffffff'
            if 'TimeDiffToFastest' in driver_timing:
                gap = driver_timing['TimeDiffToFastest']
            if 'GapToLeader' in driver_timing:
                gap = driver_timing['GapToLeader']
            if not gap:
                if 'BestLapTime' in driver_timing:
                    gap = driver_timing['BestLapTime']['Value']
            s.scoreboard[driver_number] = {
                "Pos": driver_timing['Position'],
                "TLA": driver['Tla'],
                "Gap": gap,
                "Color": (int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)),
            }

    async def _process_message(self, message):
        if hasattr(message, "result"):
            print(message)
            for k in message.result:
                print(k)
                if hasattr(self, k):
                    getattr(self, k)(message.result[k])
                else:
                    print(k, message.result[k])
        elif hasattr(message, "arguments"):
            k, v, t = message.arguments
            if hasattr(self, k):
                getattr(self, k)(v)
            else:
                print(k, v)


_connection_url = 'https://livetiming.formula1.com/signalr'
hub = Hub("streaming")


async def run_client():
    async with F1SignalRClient(
        _connection_url,
        [hub],
        keepalive_interval=5,
    ) as client:
        await hub.invoke("Subscribe", [
            "DriverList",
            "TimingData",
            "SessionData",
            "LapCount",
            "ExtrapolatedClock",
        ])
        await client.wait(timeout=5)


async def main():
    await asyncio.gather(
        run_client(),
        s.heartbeat()
    )

if __name__ == "__main__":
    asyncio.run(main())
