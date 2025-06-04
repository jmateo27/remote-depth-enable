import asyncio

class TimeOfFlight:
    def __init__(self, vl53l0x, read_interval=0.1, callback=None):
        self.sensor = vl53l0x
        self.read_interval = read_interval
        self.callback = callback
        self._running = False

    async def start(self):
        await self.sensor.init()
        self._running = True
        while self._running:
            distance = await self.sensor.read()
            if self.callback:
                await self.callback(distance)
            await asyncio.sleep(self.read_interval)

    def stop(self):
        self._running = False
