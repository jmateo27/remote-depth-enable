import time
from machine import Pin, I2C
from vl53l0x import VL53L0X

print("setting up i2c")
id = 0
sda = Pin(4)
scl = Pin(5)
i2c = I2C(id=id, sda=sda, scl=scl)

print(i2c.scan())

tof = VL53L0X(i2c)
tof.set_measurement_timing_budget(40000)

def setShortRange():
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[0], 12)
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[1], 8)

def setLongRange():
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[0], 18)
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[1], 14)

setShortRange()
isShortRange = True
threshold = 0.3  # meters

# Rolling average buffer params
ROLLING_WINDOW_SIZE = 10
rolling_buffer = []

def rolling_average(buffer):
    return sum(buffer) / len(buffer) if buffer else 0

while True:
    try:
        raw_measurement = (tof.ping()) / 1000.0  # Convert mm to meters and offset
        if isShortRange:
            raw_measurement -= 0.025
        # Add new measurement to buffer
        rolling_buffer.append(raw_measurement)
        if len(rolling_buffer) > ROLLING_WINDOW_SIZE:
            rolling_buffer.pop(0)  # Remove oldest

        avg_measurement = rolling_average(rolling_buffer)

        print(f"Raw: {raw_measurement:.3f} m, Avg: {avg_measurement:.3f} m")

        if isShortRange:
            if avg_measurement > threshold:
                print("Switching to long range")
                setLongRange()
                isShortRange = False
                rolling_buffer.clear()  # Clear buffer to avoid stale data
        else:
            if avg_measurement <= threshold:
                print("Switching to short range")
                setShortRange()
                isShortRange = True
                rolling_buffer.clear()

    except Exception as e:
        print("Read error:", e)

    time.sleep_ms(100)
