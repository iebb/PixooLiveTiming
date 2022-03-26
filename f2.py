import asyncio
import collections
import logging

import mergedeep
from signalr_async.net import Hub
from signalr_async.net.client import SignalRClient

from scoreboard import Scoreboard

logging.basicConfig(level=logging.DEBUG)

s = Scoreboard()


class F2SignalRClient(SignalRClient):
    drivers = collections.defaultdict(dict)
    session = {'Session': 'Race'}

    def send_scoreboard(self):
        for driver_number in self.drivers:
            d = self.drivers[driver_number]

            s.scoreboard[driver_number] = {
                "Pos": d['Number'],
                "TLA": d['driver']['TLA'],
            }

            if self.session['Session'] == 'Race':
                s.scoreboard[driver_number]["Gap"] = d['gap']['Value'] if d['gap']['Value'] \
                    else "LAP " + d['laps']['Value']
            else:
                s.scoreboard[driver_number]["Gap"] = d['gapP']['Value'] if d['gapP']['Value'] \
                    else d['best']['Value']

            if d['status']['Stopped']:
                s.scoreboard[driver_number]['Color'] = (255, 0, 0)
                s.scoreboard[driver_number]['Gap'] = 'STOP'


    def on_data(self, t, a, drivers):
        if isinstance(a, dict):
            self.session = a
        for driver_number in drivers:
            if isinstance(drivers[driver_number], dict):
                self.drivers[driver_number] = drivers[driver_number]
        self.send_scoreboard()

    def on_datafeed(self, t, a, lines):
        if isinstance(a, dict):
            self.session = a
        for line in lines['lines']:
            driver_number = line['driver']['RacingNumber']
            mergedeep.merge(self.drivers[driver_number], line)
        self.send_scoreboard()

    def on_statsfeed(self, *args):
        # print("on_statsfeed", v)
        pass

    def on_timefeed(self, *args):
        # print("timefeed", v)
        pass

    def on_racedetailsfeed(self, *args):
        pass

    def on_commentaryfeed(self, *args):
        pass

    def on_sessionfeed(self, *args):
        pass

    async def _process_message(self, message):
        print(message)
        if hasattr(message, "target"):
            if hasattr(self, "on_" + message.target):
                getattr(self, "on_" + message.target)(*message.arguments)
        elif hasattr(message, "result"):
            if message.result:
                for k in message.result:
                    if hasattr(self, "on_" + k):
                        getattr(self, "on_" + k)(*message.result[k])
        return None


_connection_url = 'https://ltss.fiaformula2.com/streaming'
hub = Hub("streaming")


async def run_client():
    async with F2SignalRClient(
        _connection_url,
        [hub],
        keepalive_interval=3,
    ) as client:
        await asyncio.gather(hub.invoke("GetData2", "F2", [
            "data",
            # "statsfeed",
            # "weatherfeed",
            # "sessionfeed",
            # "trackfeed",
            # "commentaryfeed",
            # "timefeed",
            # "racedetailsfeed"
        ]), hub.invoke("JoinFeeds", "F2", [
            "data",
            # "weather",
            # "status",
            # "time",
            # "commentary",
            # "racedetails"
        ]))
        await client.wait(timeout=5)


async def main():
    await asyncio.gather(
        s.heartbeat(),
        run_client(),
    )

if __name__ == "__main__":
    asyncio.run(main())
