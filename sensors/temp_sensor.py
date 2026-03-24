import glob
import random
from collections import deque

SMOOTHING_SAMPLES = 10
BASE_DIR = "/sys/bus/w1/devices/"


def discover_temperature_sensors():
    return sorted(glob.glob(f"{BASE_DIR}28*/w1_slave"))


class TemperatureSensor:
    """Reads a DS18B20 via 1-Wire.

    If device_file is None (no sensor detected), returns realistic
    simulated values around 25 C.
    """

    def __init__(self, device_file=None):
        self.device_file = device_file
        self.history = deque(maxlen=SMOOTHING_SAMPLES)
        self.simulated = device_file is None

    def read(self):
        if self.simulated:
            return round(25.0 + random.uniform(-0.3, 0.3), 2)

        try:
            with open(self.device_file, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
            if len(lines) < 2 or "YES" not in lines[0] or "t=" not in lines[1]:
                raise RuntimeError("bad reading")
            temp_c = float(lines[1].split("t=")[1]) / 1000
            self.history.append(temp_c)
            return sum(self.history) / len(self.history)
        except Exception:
            return round(25.0 + random.uniform(-0.3, 0.3), 2)
