import asyncio
import sys
import time

from pixoo import Pixoo


class Scoreboard:
    scoreboard = {}
    startup_time = 0
    heartbeat_interval = 1
    display_lines = 8
    display_height = 8
    a = "" if len(sys.argv) == 1 else sys.argv[1]
    pixoo = Pixoo(a, 64, True)

    def get_color_for_ranking(self, position):
        if position == 1:
            return 255, 215, 0
        if position == 2:
            return 192, 192, 192
        if position == 3:
            return 199, 123, 48
        return 255, 255, 255

    async def update_screen(self):
        self.pixoo.fill((0, 0, 0))
        if len(self.scoreboard) == 0:
            return
        if not self.startup_time:
            self.startup_time = time.time()
        t = time.time() - self.startup_time
        display_offset = int(t / self.heartbeat_interval) % (len(self.scoreboard) - self.display_lines + 1)
        for driver_num in self.scoreboard:
            d = self.scoreboard[driver_num]
            i = int(d['Pos']) - 1
            y = 0
            if i < 3:
                y = i * 8 + 1
            elif 2 < i - display_offset < self.display_lines:
                y = (i - display_offset) * self.display_height + 1

            color = self.get_color_for_ranking(int(d['Pos']))
            driver_color = color
            if 'Color' in d:
                driver_color = d['Color']
            if y:
                gap = '%4s' % d['Gap']
                self.pixoo.draw_text('%2s.' % d['Pos'], (0, y), color)
                self.pixoo.draw_text(d['TLA'], (12, y), driver_color)
                width = self.pixoo.length_text(gap)
                self.pixoo.draw_text(gap, (63 - width, y), color)
        self.pixoo.push()

    async def heartbeat(self) -> None:
        while True:
            try:
                asyncio.create_task(self.update_screen())
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

