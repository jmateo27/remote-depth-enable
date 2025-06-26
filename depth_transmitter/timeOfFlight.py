import asyncio
from machine import Pin, I2C
from vl53l0x import VL53L0X
from time import ticks_ms, ticks_diff
import uasyncio as asyncio

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

STEP_SIZE_CM = 2.5
# STEP_SIZE_CM = 1.0
M_PER_CM = 0.01

STEP_TOLERANCE_CM = STEP_SIZE_CM * 0.1
STATIONARY_TOLERANCE_CM = STEP_SIZE_CM * 0.5

class TOF_Interface:
    def __init__(self, event):
        self.i2c = I2C(id=I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
        self.tof = VL53L0X(self.i2c)
        self.tof.set_measurement_timing_budget(40000)
        self.ROLLING_WINDOW_SIZE = 10
        self.rolling_buffer = []
        self.isShortRange = True
        self.RANGE_THRESHOLD = 0.3
        self.MEASUREMENT_BUFFER_MS = 20
        self.SAMPLING_BUFFER_MS = 25
        self.event = event

    def setShortRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 12)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 8)

    def setLongRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 18)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 14)

    async def getRawMeasurement(self):
        out = (await self.tof.ping() / 1000.0)
        if self.isShortRange:
            out -= 0.025
        return out

    async def getGoodMeasurement(self):
        self.rolling_buffer.clear()
        for i in range(self.ROLLING_WINDOW_SIZE):
            t0 = ticks_ms()
            self.rolling_buffer.append(await self.getRawMeasurement())
            elapsed = ticks_diff(ticks_ms, t0)
            await asyncio.sleep_ms(max(0, self.MEASUREMENT_BUFFER_MS / self.ROLLING_WINDOW_SIZE - elapsed))
        
        return sum(self.rolling_buffer) / self.ROLLING_WINDOW_SIZE

    async def sendPulse(self):
        self.event.set()

    async def run_tof(self):
        self.setShortRange()
        self.isShortRange = True

        baseline = await self.getGoodMeasurement()
        print(f"Baseline: {baseline:.3f} m")
        prev_pulse_avg = -1.0

        while True:
            t0 = ticks_ms()

            cur_avg = await self.getGoodMeasurement()
            if (((((cur_avg - baseline) % STEP_SIZE_CM) < STEP_TOLERANCE_CM) or (((cur_avg - baseline) % STEP_SIZE_CM) > STEP_SIZE_CM - STEP_TOLERANCE_CM))
                and (abs(cur_avg - prev_pulse_avg) > STATIONARY_TOLERANCE_CM)
            ):
                await self.sendPulse()
                print(f'Pulse at {round((cur_avg - baseline)*M_PER_CM)}')

            if self.isShortRange:
                if baseline > self.RANGE_THRESHOLD:
                    print("Switching to long range")
                    self.setLongRange()
                    self.isShortRange = False
                    self.rolling_buffer.clear()
            else:
                if baseline <= self.RANGE_THRESHOLD:
                    print("Switching to short range")
                    self.setShortRange()
                    self.isShortRange = True
                    self.rolling_buffer.clear()

            elapsed = ticks_ms() - t0

            asyncio.sleep_ms(max(0, self.SAMPLING_BUFFER_MS - elapsed))
                
            

            

async def main():
    """ Main function """
    tof = TOF_Interface()
    while True:
        tasks = [
            asyncio.create_task(tof.run_tof())
        ]
        await asyncio.gather(*tasks)

# asyncio.run(main())