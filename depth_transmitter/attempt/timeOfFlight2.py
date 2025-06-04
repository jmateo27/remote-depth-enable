import time
from machine import Pin, I2C
from vl53l0x import VL53L0X

print("setting up i2c")
id = 0
sda = Pin(4)
scl = Pin(5)

i2c = I2C(id=id, sda=sda, scl=scl)

print(i2c.scan())

# print("creating vl53lox object")
# Create a VL53L0X object
tof = VL53L0X(i2c)

# Pre: 12 to 18 (initialized to 14 by default)
# Final: 8 to 14 (initialized to 10 by default)

# the measuting_timing_budget is a value in ms, the longer the budget, the more accurate the reading.
budget = tof.measurement_timing_budget_us
print("Budget was:", budget)
tof.set_measurement_timing_budget(40000)

# Sets the VCSEL (vertical cavity surface emitting laser) pulse period for the
# given period type (VL53L0X::VcselPeriodPreRange or VL53L0X::VcselPeriodFinalRange)
# to the given value (in PCLKs). Longer periods increase the potential range of the sensor.
# Valid values are (even numbers only):

def setShortRange():
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[0], 12)
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[1], 8)
    
def setLongRange():
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[0], 18)
    tof.set_Vcsel_pulse_period(tof.vcsel_period_type[1], 14)
    
setShortRange()
isShortRange = True

while True:
    # Start ranging
    measurement = (tof.ping() - 25) / 1000.0
    if measurement > 0.3 and isShortRange:
        print("Setting to long range")
        setLongRange()
        isShortRange = False
    elif measurement <= 0.3 and not isShortRange:
        print("Setting to short range")
        setShortRange()
        isShortRange = True
    
    print(measurement, "m")

    time.sleep_ms(100)  # Short delay of 0.1 seconds to reduce CPU usage