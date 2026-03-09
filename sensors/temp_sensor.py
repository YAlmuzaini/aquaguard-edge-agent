import glob
from collections import deque

SMOOTHING_SAMPLES = 10
BASE_DIR = "/sys/bus/w1/devices/"


def discover_temperature_sensors():
    return sorted(glob.glob(f"{BASE_DIR}28*/w1_slave"))


class TemperatureSensor:
    def __init__(self, device_file):
        self.device_file = device_file
        self.history = deque(maxlen=SMOOTHING_SAMPLES)

    def read(self):
        with open(self.device_file, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        if len(lines) < 2 or "YES" not in lines[0] or "t=" not in lines[1]:
            self.history.clear()
            raise RuntimeError(f"Invalid DS18B20 reading from {self.device_file}")
        temp_c = float(lines[1].split("t=")[1]) / 1000
        self.history.append(temp_c)
        return sum(self.history) / len(self.history)
