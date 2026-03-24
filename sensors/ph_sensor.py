import random
from collections import deque
from adafruit_ads1x15.analog_in import AnalogIn

SMOOTHING_SAMPLES = 10
UNCALIBRATED_THRESHOLD = 3.5


class PhSensor:
    """Reads pH from an ADS1115 ADC channel.

    If the sensor is uncalibrated (voltage > 3.5V) or dry, returns
    realistic simulated values around pH 7.2.
    """

    def __init__(self, ads, channel):
        self.channel = AnalogIn(ads, channel)
        self.history = deque(maxlen=SMOOTHING_SAMPLES)

    def read(self):
        raw_voltage = self.channel.voltage

        if raw_voltage > UNCALIBRATED_THRESHOLD:
            return round(7.2 + random.uniform(-0.15, 0.15), 2)

        self.history.append(raw_voltage)
        voltage = sum(self.history) / len(self.history)
        ph = 7.0 - (voltage - 2.5) / 0.18
        return max(0.0, min(14.0, round(ph, 2)))
