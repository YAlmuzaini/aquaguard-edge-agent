"""
Read flow from a hall-effect water flow sensor on a Raspberry Pi GPIO pin.
Counts pulses using GPIO interrupts and prints flow in L/min once per second.
Adjust the GPIO pin and pulses-per-liter constant for your specific sensor.
"""
import time

import RPi.GPIO as GPIO

# BCM GPIO pin connected to the flow sensor signal wire.
FLOW_GPIO_PIN = 17
# Common YF-S201-style approximation: frequency (Hz) = 7.5 * flow (L/min).
PULSES_PER_LITER_PER_MINUTE = 7.5

pulse_count = 0


def count_pulse(_channel):
    global pulse_count
    pulse_count += 1


GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(FLOW_GPIO_PIN, GPIO.FALLING, callback=count_pulse)

last_count = 0
last_time = time.monotonic()

try:
    while True:
        time.sleep(1)
        now = time.monotonic()
        elapsed = max(now - last_time, 0.1)
        pulses = pulse_count - last_count
        last_time = now
        last_count = pulse_count

        pulses_per_second = pulses / elapsed
        flow_l_min = pulses_per_second / PULSES_PER_LITER_PER_MINUTE
        print(f"Pulses: {pulses:4d}   Flow: {flow_l_min:.2f} L/min")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    GPIO.remove_event_detect(FLOW_GPIO_PIN)
    GPIO.cleanup(FLOW_GPIO_PIN)
