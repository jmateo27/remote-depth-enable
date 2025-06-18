import asyncio
from machine import Pin, I2C
from vl53l0x import VL53L0X

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

class TOF_Interface:
    def __init__(self, shared, mutex):
        self.i2c = I2C(id=I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
        self.tof = VL53L0X(self.i2c)
        self.tof.set_measurement_timing_budget(40000)
        self.ROLLING_WINDOW_SIZE = 10
        self.rolling_buffer = []
        self.isShortRange = True
        self.threshold = 0.3
        self.MEASUREMENT_BUFFER_MS = 100
        self.shared = shared
        self.mutex = mutex

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

    def rolling_average(self):
        return sum(self.rolling_buffer) / len(self.rolling_buffer) if self.rolling_buffer else 0

    async def getAverageMeasurement(self):
        self.rolling_buffer.append(await self.getRawMeasurement())
        if len(self.rolling_buffer) > self.ROLLING_WINDOW_SIZE:
            self.rolling_buffer.pop(0)
        return self.rolling_average()

    async def sendPulse(self):
        async with self.mutex:
            self.shared["depthPulse"] = True
        print('Pulse!')
        await asyncio.sleep(0.2)
        async with self.mutex:
            self.shared["depthPulse"] = False

    async def run_tof(self):
        self.setShortRange()
        self.isShortRange = True

        #Change these if you are making a 1cm pulse device
        STEP_SIZE = 0.025
        STEP_TOLERANCE = 0.001
        STATIONARY_TOLERANCE = STEP_SIZE * 0.6

        # Prime the rolling buffer
        for _ in range(self.ROLLING_WINDOW_SIZE):
            await self.getAverageMeasurement()
            await asyncio.sleep_ms(self.MEASUREMENT_BUFFER_MS)

        baseline = await self.getAverageMeasurement()
        # prv_avg = baseline
        print(f"baseline: {baseline:.3f} m")
        # direction = "up"
        prev_pulse_avg = -1.0

        while True:
            try:
                cur_avg
                while True:
                    cur_avg = await self.getAverageMeasurement()
                    # if (cur_avg - prv_avg) > 0:
                    #     direction = "up"
                    # elif (cur_avg - prv_avg) < 0:
                    #     direction = "down"
                    # prv_avg = cur_avg
                    if (abs((cur_avg - baseline) % STEP_SIZE) < STEP_TOLERANCE) or (abs((cur_avg - baseline) % STEP_SIZE) > STEP_SIZE - STEP_TOLERANCE):
                        if (abs(cur_avg - prev_pulse_avg) > STATIONARY_TOLERANCE):
                            continue
                        prev_pulse_avg = cur_avg
                        break
                    self.rolling_buffer.clear()
                    await asyncio.sleep_ms(self.MEASUREMENT_BUFFER_MS)
                
                await self.sendPulse()

                if self.isShortRange:
                    if baseline > self.threshold:
                        print("Switching to long range")
                        self.setLongRange()
                        self.isShortRange = False
                        self.rolling_buffer.clear()
                else:
                    if baseline <= self.threshold:
                        print("Switching to short range")
                        self.setShortRange()
                        self.isShortRange = True
                        self.rolling_buffer.clear()

            except Exception as e:
                print("Read error:", e)

            await asyncio.sleep_ms(self.MEASUREMENT_BUFFER_MS)


async def main():
    """ Main function """
    tof = TOF_Interface()
    while True:
        tasks = [
            asyncio.create_task(tof.run_tof())
        ]
        await asyncio.gather(*tasks)

# asyncio.run(main())