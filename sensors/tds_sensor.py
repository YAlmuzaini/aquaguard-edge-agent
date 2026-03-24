from collections import deque
from adafruit_ads1x15.analog_in import AnalogIn

IN_WATER_VOLTAGE_THRESHOLD = 0.15
SMOOTHING_SAMPLES = 10


class TdsSensor:
    """Reads TDS from an ADS1115 ADC channel.

    When the probe is out of water (voltage < 0.15V) returns 0.
    """

    def __init__(self, ads, channel):
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
