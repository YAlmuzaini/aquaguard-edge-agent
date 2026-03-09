"""
Read pH from an analog pH probe via the ADS1115 (I2C) on channel 1.
Prints smoothed voltage and computed pH once per second. Calibrate with buffer
solutions and adjust the voltage-to-pH formula for your probe.
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

# Create I2C bus on the board's SCL/SDA pins.
i2c = busio.I2C(board.SCL, board.SDA)
# Attach the ADS1115 ADC on that bus.
ads = ADS.ADS1115(i2c)
# Use channel 1 (A1) for the pH probe voltage (TDS is on channel 0).
chan = AnalogIn(ads, 1)

# Number of samples to average for smoothing.
SMOOTHING_SAMPLES = 10

# moving average of last N voltage readings
voltage_history = deque(maxlen=SMOOTHING_SAMPLES)

# Keep reading and printing pH indefinitely; Ctrl+C exits cleanly.
try:
    while True:
        # Current voltage from the pH probe (range depends on module and solution).
        raw = chan.voltage

        # Add this reading to the moving-average buffer.
        voltage_history.append(raw)
        # Smoothed voltage = average of last N readings.
        voltage = sum(voltage_history) / len(voltage_history)

        # Linear mapping from voltage to pH (calibrate with buffer solutions for your probe).
        ph = 7.0 - (voltage - 2.5) / 0.18
        # Print smoothed voltage and computed pH.
        print(f"Voltage: {voltage:.3f} V   pH: {ph:.2f}")

        # One reading per second.
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
