import time

import RPi.GPIO as GPIO

PULSES_PER_LITER_PER_MINUTE = 7.5


class FlowSensor:
    def __init__(self, gpio_pin):
        self.gpio_pin = gpio_pin
        self.count = 0
        self.last_count = 0
        self.last_time = time.monotonic()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.gpio_pin, GPIO.FALLING, callback=self._pulse)

    def _pulse(self, _channel):
        self.count += 1

    def read(self):
        now = time.monotonic()
        elapsed = max(now - self.last_time, 0.1)
        pulses = self.count - self.last_count
        self.last_time = now
        self.last_count = self.count
        pulses_per_second = pulses / elapsed
        return pulses_per_second / PULSES_PER_LITER_PER_MINUTE

    def cleanup(self):
        GPIO.remove_event_detect(self.gpio_pin)
