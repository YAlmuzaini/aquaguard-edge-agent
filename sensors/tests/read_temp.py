"""
Read temperature from a DS18B20 sensor on the Raspberry Pi 1-Wire bus.
Prints smoothed temperature in °C once per second. On read or CRC errors,
reports --- and clears the smoothing history. Enable 1-Wire in raspi-config.
"""
# Find device folders for 1-Wire sensors (e.g. 28-... for DS18B20).
import glob
# Pause between readings so output isn't flooded.
import time
# Ring buffer for keeping only the last N temperature samples (moving average).
from collections import deque

# Linux 1-Wire devices are exposed under this path.
BASE_DIR = '/sys/bus/w1/devices/'
# Number of samples to average for smoothing.
SMOOTHING_SAMPLES = 10

# Find first DS18B20 (1-Wire address 28*)
# Match any folder whose name starts with 28 (DS18B20 family).
device_folders = glob.glob(BASE_DIR + '28*')
# Fail early if no sensor is connected or 1-Wire is disabled.
if not device_folders:
    raise RuntimeError('No DS18B20 found. Enable 1-Wire: raspi-config → Interface Options → 1-Wire')
# Read temperature from this file (kernel driver writes raw value here).
device_file = device_folders[0] + '/w1_slave'

# moving average of last N readings
# Holds only the last SMOOTHING_SAMPLES values; oldest drops when we append.
temp_history = deque(maxlen=SMOOTHING_SAMPLES)


def read_temp_raw():
    """Read raw lines from sensor. Returns (ok, temp_c) or (False, None) on CRC/parse error."""
    # Open the kernel-provided w1_slave file for this device.
    try:
        with open(device_file) as f:
            lines = f.readlines()
    # Device unplugged or bus error.
    except (OSError, IOError):
        return False, None
    # File should have 2 lines (CRC line + t= line).
    if len(lines) < 2:
        return False, None
    # First line must contain YES to indicate valid CRC.
    if 'YES' not in lines[0]:
        return False, None  # CRC fail
    # Second line holds t=xxxxx (temp in millidegrees).
    if 't=' not in lines[1]:
        return False, None
    # Parse millidegrees and convert to degrees C.
    temp_c = float(lines[1].split('t=')[1]) / 1000
    return True, temp_c


# Keep reading and printing temperature indefinitely; Ctrl+C exits cleanly.
try:
    while True:
        # Get one raw reading; ok is False on CRC/read error.
        ok, raw = read_temp_raw()

        # On error, clear history so next good reading isn't skewed.
        if not ok:
            temp_history.clear()
            print("Temperature: --- (read error)")
            time.sleep(1)
            continue

        # Add this reading to the moving-average buffer.
        temp_history.append(raw)
        # Smoothed temperature = average of last N readings.
        temp = sum(temp_history) / len(temp_history)
        print(f"Temperature: {temp:.2f} °C")

        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
