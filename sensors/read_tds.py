"""
Read TDS (total dissolved solids) from an analog TDS probe via the ADS1115 (I2C)
on channel 0. Prints smoothed voltage and ppm once per second. When the probe
is out of water (voltage below threshold), reports --- instead of TDS.
"""
# Pause between readings so output isn't flooded and sensor has time to settle.
import time
# Ring buffer for keeping only the last N voltage samples (moving average).
from collections import deque

# CircuitPython board pins (SCL/SDA).
import board
# I2C bus for talking to the ADS1115 ADC.
import busio
# ADS1115 16‑bit ADC driver.
import adafruit_ads1x15.ads1115 as ADS
# Wraps an ADC channel so we read voltage directly.
from adafruit_ads1x15.analog_in import AnalogIn

# Create I2C bus on the board’s SCL/SDA pins.
i2c = busio.I2C(board.SCL, board.SDA)
# Attach the ADS1115 ADC on that bus.
ads = ADS.ADS1115(i2c)
# Use channel 0 (A0) for the TDS probe voltage.
chan = AnalogIn(ads, 0)

# Below this voltage we treat the probe as out of water (dry).
IN_WATER_VOLTAGE_THRESHOLD = 0.15
# Number of samples to average for smoothing.
SMOOTHING_SAMPLES = 10

# moving average of last N voltage readings
voltage_history = deque(maxlen=SMOOTHING_SAMPLES)

# Keep reading and printing TDS indefinitely; Ctrl+C exits cleanly.
try:
    while True:
        # Current voltage from the TDS probe (0–3.3 V typical).
        raw = chan.voltage

        # If probe is out of water, clear history so it reacts immediately next time
        if raw < IN_WATER_VOLTAGE_THRESHOLD:
            # Reset smoothing so next in-water reading isn’t skewed by old dry data.
            voltage_history.clear()
            # Show raw voltage and no TDS when probe is dry.
            print(f"Voltage: {raw:.3f} V   TDS: --- (probe out of water)")
            # Wait before next check to avoid spamming and let probe settle.
            time.sleep(1)
            continue

        # Probe is in water → smooth using last N valid readings
        # Add this reading to the moving-average buffer.
        voltage_history.append(raw)
        # Smoothed voltage = average of last N readings.
        voltage = sum(voltage_history) / len(voltage_history)

        # Empirical polynomial to convert voltage to TDS in ppm (calibrated for this probe).
        tds = (133.42 * voltage**3 - 255.86 * voltage**2 + 857.39 * voltage) * 0.5
        # Print smoothed voltage and computed TDS.
        print(f"Voltage: {voltage:.3f} V   TDS: {int(tds)} ppm")

        # One reading per second when in water.
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
