from collections import deque

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn

IN_WATER_VOLTAGE_THRESHOLD = 0.15
SMOOTHING_SAMPLES = 10


class TdsSensor:
    def __init__(self, ads_address, channel):
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c, address=ads_address)
        self.channel = AnalogIn(ads, channel)
        self.history = deque(maxlen=SMOOTHING_SAMPLES)

    def read(self):
        raw = self.channel.voltage
        if raw < IN_WATER_VOLTAGE_THRESHOLD:
            self.history.clear()
            return 0.0
        self.history.append(raw)
        voltage = sum(self.history) / len(self.history)
        return (133.42 * voltage**3 - 255.86 * voltage**2 + 857.39 * voltage) * 0.5
