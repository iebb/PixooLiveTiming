import asyncio
import json
import logging

from signalr_async.net import Hub
from signalr_async.net.client import SignalRClient

import merger
from scoreboard import Scoreboard

logging.basicConfig(level=logging.DEBUG)
s = Scoreboard()


class F1SignalRClient(SignalRClient):
    driver_list = {}
    timing_data = {}
    session_data = {}
    session_info = {}

    def LapCount(self, lc):
        pass

    def SessionData(self, session_data):
        merger.merge(self.session_data, session_data)

    def SessionInfo(self, session_info):
        merger.merge(self.session_info, session_info)

    def DriverList(self, drivers):
        merger.merge(self.driver_list, drivers)

    def TimingData(self, timing):
        merger.merge(self.timing_data, timing)

        for driver_number in timing["Lines"]:
            driver = self.driver_list[driver_number]
            driver_timing = self.timing_data["Lines"][driver_number]
            gap = ''
            color = driver['TeamColour']
            pos = driver_timing['Position']
            if not color:
                color = 'ffffff'

            if self.session_info['Type'] == "Qualifying":
                current_part = int(self.timing_data['SessionPart'])
                current_entries = self.timing_data['NoEntries'][current_part - 1]
                if driver_timing['Position'] == '1':
                    gap = driver_timing['BestLapTimes'][current_part - 1]['Value']
                elif int(driver_timing['Position']) > current_entries:
                    gap = 'KO'
                else:
                    gap = driver_timing['Stats'][current_part - 1]['TimeDiffToFastest']
            elif self.session_info['Type'] == "Practice":
                if 'TimeDiffToFastest' in driver_timing:
                    gap = driver_timing['TimeDiffToFastest']
                if driver_timing['Position'] == '1':
                    gap = driver_timing['BestLapTime']['Value']
            elif self.session_info['Type'] == "Race":
                if 'GapToLeader' in driver_timing:  # race
                    print("GapToLeader")
                    gap = driver_timing['GapToLeader']

            s.scoreboard[driver_number] = {
                "Pos": pos,
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
        await hub.invoke("Subscribe", ["Heartbeat", "CarData.z", "Position.z",
                       "ExtrapolatedClock", "TopThree", "RcmSeries",
                       "TimingStats", "TimingAppData",
                       "WeatherData", "TrackStatus", "DriverList",
                       "RaceControlMessages", "SessionInfo",
                       "SessionData", "LapCount", "TimingData"])
        await client.wait(timeout=5)


async def main():
    await asyncio.gather(
        run_client(),
        s.heartbeat()
    )


if __name__ == "__main__":
    asyncio.run(main())
