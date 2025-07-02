import asyncio
from machine import Pin, I2C
from vl53l0x import VL53L0X
from time import ticks_ms, ticks_diff
import uasyncio as asyncio

I2C0_ID = 0
I2C1_ID = 1
I2C_SDA_PINS = [4, 18]
I2C_SCL_PINS = [5, 19]

STEP_SIZE_CM = 2.5
# STEP_SIZE_CM = 1.0
M_PER_CM = 0.01
CM_PER_M = 100

STEP_TOLERANCE_CM = STEP_SIZE_CM * 0.1
STATIONARY_TOLERANCE_CM = STEP_SIZE_CM * 0.7
MAX_MEASUREMENT_M = 2.5

class TOF_Interface:
    def __init__(self, event, i2c_id):
        self.id = i2c_id
        self.i2c = I2C(id=i2c_id, sda=Pin(I2C_SDA_PINS[i2c_id]), scl=Pin(I2C_SCL_PINS[i2c_id]))
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
        
    def getMedian(self):
        if not self.rolling_buffer:
            raise ValueError("no median for empty data")
        data = sorted(self.rolling_buffer)
        return data[5]

    async def getRawMeasurement(self):
        out = (await self.tof.ping() / 1000.0)
        if self.isShortRange:
            out -= 0.025
        return out

    async def getGoodMeasurement(self):
        self.rolling_buffer.clear()
        
        t0 = ticks_ms()
        for i in range(self.ROLLING_WINDOW_SIZE):
            t1 = ticks_ms()
            m = await self.getRawMeasurement()
            self.rolling_buffer.append(m)
            print(ticks_ms() - t1)
#             print(f'{m*CM_PER_M} cm')
            
        average = self.getMedian()
            
        elapsed = ticks_diff(ticks_ms(), t0)
#         print(elapsed)
        await asyncio.sleep_ms(max(0, self.MEASUREMENT_BUFFER_MS - elapsed))
        return average

    async def sendPulse(self):
        self.event.set()

    async def run_tof(self):
        if self.id == I2C1_ID:
            await asyncio.sleep_ms(15)

        self.setShortRange()
        self.isShortRange = True
        
        await asyncio.sleep(1)
        await self.getRawMeasurement()
        baseline = await self.getRawMeasurement()
        print(f"Baseline: {(baseline*CM_PER_M):.3f} cm")
        prev_pulse_avg = -1.0

        while True:
            t0 = ticks_ms()

            cur_avg = await self.getRawMeasurement()

            if ((	((abs((cur_avg - baseline) * CM_PER_M) % STEP_SIZE_CM) < (STEP_TOLERANCE_CM))
                or  ((abs((cur_avg - baseline) * CM_PER_M) % STEP_SIZE_CM) > (STEP_SIZE_CM - STEP_TOLERANCE_CM)))
                and (abs((cur_avg - prev_pulse_avg)) > (STATIONARY_TOLERANCE_CM * M_PER_CM))
                and (cur_avg < MAX_MEASUREMENT_M)
            ):      
                await self.sendPulse()
                print((cur_avg - prev_pulse_avg))
                prev_pulse_avg = cur_avg
#                 print(f'Pulse at {round(((cur_avg - baseline) * CM_PER_M) / STEP_SIZE_CM)}')

            if self.isShortRange:
                if cur_avg > self.RANGE_THRESHOLD:
                    print("Switching to long range")
                    self.setLongRange()
                    self.isShortRange = False
                    self.rolling_buffer.clear()
            else:
                if cur_avg <= self.RANGE_THRESHOLD:
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