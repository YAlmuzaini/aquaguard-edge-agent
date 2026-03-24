from collections import deque
from adafruit_ads1x15.analog_in import AnalogIn

SMOOTHING_SAMPLES = 10

PRESSURE_VOLTAGE_MIN = 0.5
PRESSURE_VOLTAGE_MAX = 4.5
PRESSURE_MAX_PSI = 80.0


class PressureSensor:
    """Reads pressure from an ADS1115 ADC channel.

    Maps 0.5–4.5V to 0–80 psi with 10-sample smoothing.
    """

    def __init__(self, ads, channel):
        self.channel = AnalogIn(ads, channel)
        self.history = deque(maxlen=SMOOTHING_SAMPLES)

    def read(self):
        self.history.append(self.channel.voltage)
        voltage = sum(self.history) / len(self.history)
        psi = (
            (voltage - PRESSURE_VOLTAGE_MIN)
            / (PRESSURE_VOLTAGE_MAX - PRESSURE_VOLTAGE_MIN)
            * PRESSURE_MAX_PSI
        )
        return max(0.0, min(PRESSURE_MAX_PSI, psi))
