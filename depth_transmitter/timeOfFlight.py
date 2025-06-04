import machine
import time

VL53L0X_ADDR = 0x29
SDA_PIN = 4
SCL_PIN = 5
I2C_ID = 0
I2C_FREQ = 100_000

class VL53L0X:
    def __init__(self, i2c):
        self.i2c = i2c
        if VL53L0X_ADDR not in self.i2c.scan():
            raise RuntimeError("VL53L0X not found.")
        self._stop_variable = 0
        self._init_sensor()

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(VL53L0X_ADDR, reg, bytes([value]))

    def read_reg(self, reg):
        return self.i2c.readfrom_mem(VL53L0X_ADDR, reg, 1)[0]

    def read_reg16(self, reg):
        data = self.i2c.readfrom_mem(VL53L0X_ADDR, reg, 2)
        return (data[0] << 8) | data[1]

    def write_reg16(self, reg, value):
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        self.i2c.writeto_mem(VL53L0X_ADDR, reg, bytes([high, low]))

    def _perform_single_ref_calibration(self, vhv_init_byte):
        self.write_reg(0x00, 0x01)
        start = time.ticks_ms()
        while not (self.read_reg(0x13) & 0x07):
            if time.ticks_diff(time.ticks_ms(), start) > 200:
                raise RuntimeError("Timeout during reference calibration")
            time.sleep_ms(5)
        self.write_reg(0x0B, 0x01)

    def _init_sensor(self):
        try:
            self.write_reg(0x88, 0x00)
            self.write_reg(0x80, 0x01)
            self.write_reg(0xFF, 0x01)
            self.write_reg(0x00, 0x00)
            self._stop_variable = self.read_reg(0x91)
            self.write_reg(0x00, 0x01)
            self.write_reg(0xFF, 0x00)
            self.write_reg(0x80, 0x00)

            # Recommended long-range tuning
            self.write_reg(0xFF, 0x01)
            self.write_reg(0x00, 0x00)
            self.write_reg(0x91, self._stop_variable)
            self.write_reg(0x00, 0x01)
            self.write_reg(0xFF, 0x00)
            self.write_reg(0x80, 0x00)

            # Set signal rate limit to 0.1 MCPS (default is 0.25)
            self.write_reg16(0x44, int(0.1 * (1 << 7)))

            # VCSEL periods for long range
            self.write_reg(0x50, 0x12)  # PRE_RANGE_CONFIG_VCSEL_PERIOD = 18 PCLKs
            self.write_reg(0x70, 0x0E)  # FINAL_RANGE_CONFIG_VCSEL_PERIOD = 14 PCLKs

            # Increase timing budget (e.g., 200ms)
            self.write_reg16(0x71, 0x00C8)

            # Final reference calibrations
            self._perform_single_ref_calibration(0x40)
            self._perform_single_ref_calibration(0x00)

        except Exception as e:
            raise RuntimeError("Sensor init failed: " + str(e))

    def read_distance(self):
        # Start single measurement
        self.write_reg(0x80, 0x01)
        self.write_reg(0xFF, 0x01)
        self.write_reg(0x00, 0x00)
        self.write_reg(0x91, self._stop_variable)
        self.write_reg(0x00, 0x01)
        self.write_reg(0xFF, 0x00)
        self.write_reg(0x80, 0x00)

        # Wait for measurement
        start = time.ticks_ms()
        while not (self.read_reg(0x13) & 0x07):
            if time.ticks_diff(time.ticks_ms(), start) > 200:
                raise RuntimeError("Timeout waiting for distance ready")
            time.sleep_ms(5)

        distance = self.read_reg16(0x14 + 10)  # RESULT_RANGE_STATUS + 10
        self.write_reg(0x0B, 0x01)  # Clear interrupt
        return distance

# ---------------------------
# Main Loop
# ---------------------------

i2c = machine.I2C(I2C_ID, scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=I2C_FREQ)

try:
    tof = VL53L0X(i2c)
    print("VL53L0X initialized.")

    while True:
        try:
            dist = tof.read_distance()
            print(f"Distance: {dist} mm")
        except Exception as e:
            print("Error reading distance:", e)
        time.sleep(1)

except Exception as e:
    print("VL53L0X init failed:", e)
