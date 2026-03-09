"""
Read pressure from an analog pressure sensor via the ADS1115 (I2C) on channel 2.
Prints smoothed voltage and computed pressure once per second. The voltage-to-
pressure conversion is a simple prototype placeholder and should be calibrated.
"""
import time
from collections import deque

import adafruit_ads1x15.ads1115 as ADS
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn

# ADS1115 default I2C address; change if your board uses another address.
ADS_ADDRESS = 0x48
# Use channel 2 (A2) for the pressure sensor voltage.
PRESSURE_CHANNEL = 2
SMOOTHING_SAMPLES = 10

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=ADS_ADDRESS)
chan = AnalogIn(ads, PRESSURE_CHANNEL)

voltage_history = deque(maxlen=SMOOTHING_SAMPLES)

try:
    while True:
        raw = chan.voltage
        voltage_history.append(raw)
        voltage = sum(voltage_history) / len(voltage_history)

        # Prototype placeholder: 1.0 V => 100 pressure units.
        pressure = voltage * 100
        print(f"Voltage: {voltage:.3f} V   Pressure: {pressure:.2f}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
