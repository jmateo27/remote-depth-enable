<<<<<<< HEAD
#little change
=======

>>>>>>> a21a98ef3035cc783a015c0fab0243d3fc07d966
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

            # Long range tuning
            self.write_reg(0xFF, 0x01)
            self.write_reg(0x00, 0x00)
            self.write_reg(0x91, self._stop_variable)
            self.write_reg(0x00, 0x01)
            self.write_reg(0xFF, 0x00)
            self.write_reg(0x80, 0x00)

            # Signal rate limit = 0.25 MCPS
            self.write_reg16(0x44, int(0.25 * (1 << 7)))

            # SPAD setup skipped (optional)

            # Write default tuning settings
            default_tuning = [
                (0xFF, 0x01), (0x00, 0x00), (0xFF, 0x00), (0x09, 0x00),
                (0x10, 0x00), (0x11, 0x00), (0x24, 0x01), (0x25, 0xFF),
                (0x75, 0x00), (0xFF, 0x01), (0x4E, 0x2C), (0x48, 0x00),
                (0x30, 0x20), (0xFF, 0x00), (0x30, 0x09), (0x54, 0x00),
                (0x31, 0x04), (0x32, 0x03), (0x40, 0x83), (0x46, 0x25),
                (0x60, 0x00), (0x27, 0x00), (0x50, 0x06), (0x51, 0x00),
                (0x52, 0x96), (0x56, 0x08), (0x57, 0x30), (0x61, 0x00),
                (0x62, 0x00), (0x64, 0x00), (0x65, 0x00), (0x66, 0xA0),
                (0xFF, 0x01), (0x22, 0x32), (0x47, 0x14), (0x49, 0xFF),
                (0x4A, 0x00), (0xFF, 0x00), (0x7A, 0x0A), (0x7B, 0x00),
                (0x78, 0x21), (0xFF, 0x01), (0x23, 0x34), (0x42, 0x00),
                (0x44, 0xFF), (0x45, 0x26), (0x46, 0x05), (0x40, 0x40),
                (0x0E, 0x06), (0x20, 0x1A), (0x43, 0x40), (0xFF, 0x00),
                (0x34, 0x03), (0x35, 0x44), (0xFF, 0x01), (0x31, 0x04),
                (0x4B, 0x09), (0x4C, 0x05), (0x4D, 0x04), (0xFF, 0x00),
                (0x44, 0x00), (0x45, 0x20), (0x47, 0x08), (0x48, 0x28),
                (0x67, 0x00), (0x70, 0x04), (0x71, 0x01), (0x72, 0xFE),
                (0x76, 0x00), (0x77, 0x00), (0xFF, 0x01), (0x0D, 0x01),
                (0xFF, 0x00), (0x80, 0x01), (0x01, 0xF8), (0xFF, 0x01),
                (0x8E, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00),
            ]
            for reg, val in default_tuning:
                self.write_reg(reg, val)

            # Set GPIO interrupt config to new sample ready
            self.write_reg(0x0A, 0x04)
            val = self.read_reg(0x84)
            self.write_reg(0x84, val & ~0x10)
            self.write_reg(0x0B, 0x01)

            # Do calibrations
            self.write_reg(0x01, 0xE8)
            self._perform_single_ref_calibration(0x40)
            self.write_reg(0x01, 0x01)
            self._perform_single_ref_calibration(0x00)
            self.write_reg(0x01, 0xE8)

        except Exception as e:
            raise RuntimeError("Sensor init failed: " + str(e))

    def read_distance(self):
        # Start measurement
        self.write_reg(0x80, 0x01)
        self.write_reg(0xFF, 0x01)
        self.write_reg(0x00, 0x00)
        self.write_reg(0x91, self._stop_variable)
        self.write_reg(0x00, 0x01)
        self.write_reg(0xFF, 0x00)
        self.write_reg(0x80, 0x00)

        # Wait for result
        start = time.ticks_ms()
        while not (self.read_reg(0x13) & 0x07):
            if time.ticks_diff(time.ticks_ms(), start) > 200:
                raise RuntimeError("Timeout waiting for distance ready")
            time.sleep_ms(5)

        distance = self.read_reg16(0x14 + 10)
        self.write_reg(0x0B, 0x01)
        return distance

# Main loop
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
