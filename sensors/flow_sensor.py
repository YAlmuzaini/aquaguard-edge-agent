import time
import threading
import random

try:
    import RPi.GPIO as GPIO

    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    _GPIO_AVAILABLE = False

PULSES_PER_LITER_PER_MINUTE = 7.5


class FlowSensor:
    """Flow sensor using polling in a background thread.

    Falls back to simulated values if GPIO is not available (e.g. not
    running on a Raspberry Pi or the sensor is not wired).
    """

    def __init__(self, gpio_pin):
        self.gpio_pin = gpio_pin
        self.count = 0
        self.last_count = 0
        self.last_time = time.monotonic()
        self._running = True
        self.simulated = False

        if not _GPIO_AVAILABLE:
            self.simulated = True
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
        except RuntimeError:
            self.simulated = True

    def _poll_loop(self):
        last_state = GPIO.input(self.gpio_pin)
        while self._running:
            current_state = GPIO.input(self.gpio_pin)
            if last_state == 1 and current_state == 0:
                self.count += 1
            last_state = current_state
            time.sleep(0.001)

    def read(self):
        if self.simulated:
            return round(random.uniform(0.0, 0.05), 2)

        now = time.monotonic()
        elapsed = max(now - self.last_time, 0.1)
        pulses = self.count - self.last_count
        self.last_time = now
        self.last_count = self.count
        pulses_per_second = pulses / elapsed
        return pulses_per_second / PULSES_PER_LITER_PER_MINUTE

    def cleanup(self):
        self._running = False
        if not self.simulated:
            self._thread.join(timeout=2)
