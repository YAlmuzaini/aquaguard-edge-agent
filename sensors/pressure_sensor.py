from collections import deque

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn

SMOOTHING_SAMPLES = 10


class PressureSensor:
    def __init__(self, ads_address, channel):
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c, address=ads_address)
        self.channel = AnalogIn(ads, channel)
        self.history = deque(maxlen=SMOOTHING_SAMPLES)

    def read(self):
        self.history.append(self.channel.voltage)
        voltage = sum(self.history) / len(self.history)
        return voltage * 100.0
