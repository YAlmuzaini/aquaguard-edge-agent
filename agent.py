"""
AquaGuard Edge Agent

Reads sensors from Point A (0x48, GPIO17) and Point B (0x49, GPIO27),
then sends telemetry to the Supabase ingest-telemetry Edge Function.

Graceful fallback:
  - If an ADS1115 is not detected, all ADC sensors on that point
    (pH, TDS, pressure) use simulated values.
  - If DS18B20 temperature probes are not found, temperature is simulated.
  - If pH is uncalibrated (>3.5V), pH is simulated.
  - If flow GPIO fails, flow is simulated.

The agent always starts and always sends data, even with no hardware
connected — the dashboard will receive readings either way.
"""

from datetime import datetime, timezone
import os
import random
import time

from dotenv import load_dotenv
import requests

load_dotenv()

PIPELINE_ID = os.environ.get("PIPELINE_ID", "a0000000-0000-0000-0000-000000000001")
INGEST_URL = os.environ["INGEST_URL"]
INGEST_SECRET = os.environ["INGEST_TOKEN"]
LOOP_INTERVAL_SEC = int(os.environ.get("SAMPLE_INTERVAL_SEC", "3"))
REQUEST_TIMEOUT_SEC = int(os.environ.get("REQUEST_TIMEOUT_SEC", "10"))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_payload(point, readings):
    return {
        "pipeline_id": PIPELINE_ID,
        "point": point,
        "timestamp": utc_now(),
        "flow": round(readings["flow"], 2),
        "pressure": round(readings["pressure"], 2),
        "temperature": round(readings["temperature"], 2),
        "ph": round(readings["ph"], 2),
        "tds": round(readings["tds"], 2),
        "battery": None,
        "signal": None,
        "is_replayed": False,
    }


def send_payload(payload):
    response = requests.post(
        INGEST_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT_SEC,
        headers={
            "Authorization": f"Bearer {INGEST_SECRET}",
            "x-ingest-secret": INGEST_SECRET,
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    return response.json()


class SimulatedSensor:
    """Fallback sensor that returns a fixed value with small noise."""

    def __init__(self, name, base_value, noise=0.3):
        self.name = name
        self.base_value = base_value
        self.noise = noise
        self.simulated = True

    def read(self):
        return round(self.base_value + random.uniform(-self.noise, self.noise), 2)

    def cleanup(self):
        pass


def try_init_ads(i2c, address):
    """Try to initialise an ADS1115 at the given address. Returns the ADS
    object on success or None if not found."""
    import adafruit_ads1x15.ads1115 as ADS

    try:
        ads = ADS.ADS1115(i2c, address=address)
        ads.gain = 1
        return ads
    except (ValueError, OSError):
        return None


def init_sensors():
    """Detect available hardware and build sensor dicts for points A and B.
    Returns (sensors_dict, status_lines)."""
    from sensors.flow_sensor import FlowSensor
    from sensors.temp_sensor import TemperatureSensor, discover_temperature_sensors

    status = []

    # --- I2C / ADS1115 ---
    ads_a = None
    ads_b = None
    try:
        import board
        import busio

        i2c = busio.I2C(board.SCL, board.SDA)
        ads_a = try_init_ads(i2c, 0x48)
        ads_b = try_init_ads(i2c, 0x49)
    except Exception:
        pass

    if ads_a:
        status.append("ADS1115 @ 0x48: DETECTED")
    else:
        status.append("ADS1115 @ 0x48: NOT FOUND (ADC sensors on Point A simulated)")
    if ads_b:
        status.append("ADS1115 @ 0x49: DETECTED")
    else:
        status.append("ADS1115 @ 0x49: NOT FOUND (ADC sensors on Point B simulated)")

    # --- Temperature ---
    temp_files = discover_temperature_sensors()
    if len(temp_files) >= 2:
        temp_a = TemperatureSensor(temp_files[0])
        temp_b = TemperatureSensor(temp_files[1])
        status.append("DS18B20: 2 sensors detected")
    elif len(temp_files) == 1:
        temp_a = TemperatureSensor(temp_files[0])
        temp_b = TemperatureSensor(None)
        status.append("DS18B20: 1 sensor detected (Point B simulated)")
    else:
        temp_a = TemperatureSensor(None)
        temp_b = TemperatureSensor(None)
        status.append("DS18B20: NOT FOUND (temperature simulated ~25 C)")

    # --- ADC sensors per point ---
    def build_adc_sensors(ads, point_label):
        if ads is not None:
            from sensors.ph_sensor import PhSensor
            from sensors.tds_sensor import TdsSensor
            from sensors.pressure_sensor import PressureSensor

            return {
                "ph": PhSensor(ads, channel=1),
                "tds": TdsSensor(ads, channel=0),
                "pressure": PressureSensor(ads, channel=2),
            }
        else:
            return {
                "ph": SimulatedSensor(f"ph-{point_label}", 7.2, 0.15),
                "tds": SimulatedSensor(f"tds-{point_label}", 180, 20),
                "pressure": SimulatedSensor(f"pressure-{point_label}", 55.0, 2.0),
            }

    adc_a = build_adc_sensors(ads_a, "A")
    adc_b = build_adc_sensors(ads_b, "B")

    # --- Flow ---
    flow_a = FlowSensor(gpio_pin=17)
    flow_b = FlowSensor(gpio_pin=27)
    if flow_a.simulated:
        status.append("Flow GPIO 17: NOT AVAILABLE (Point A flow simulated)")
    else:
        status.append("Flow GPIO 17: DETECTED")
    if flow_b.simulated:
        status.append("Flow GPIO 27: NOT AVAILABLE (Point B flow simulated)")
    else:
        status.append("Flow GPIO 27: DETECTED")

    sensors = {
        "A": {
            "temperature": temp_a,
            "flow": flow_a,
            **adc_a,
        },
        "B": {
            "temperature": temp_b,
            "flow": flow_b,
            **adc_b,
        },
    }

    return sensors, status


def main():
    sensors, status_lines = init_sensors()

    print("=" * 50)
    print("AquaGuard Edge Agent")
    print("=" * 50)
    print(f"Pipeline : {PIPELINE_ID}")
    print(f"Endpoint : {INGEST_URL}")
    print(f"Interval : {LOOP_INTERVAL_SEC}s")
    print("-" * 50)
    print("Hardware status:")
    for line in status_lines:
        marker = "OK" if "DETECTED" in line else "!!"
        print(f"  [{marker}] {line}")
    print("-" * 50)

    try:
        while True:
            for point, point_sensors in sensors.items():
                try:
                    readings = {
                        "temperature": point_sensors["temperature"].read(),
                        "ph": point_sensors["ph"].read(),
                        "tds": point_sensors["tds"].read(),
                        "pressure": point_sensors["pressure"].read(),
                        "flow": point_sensors["flow"].read(),
                    }
                    payload = build_payload(point, readings)
                    result = send_payload(payload)
                    print(
                        f"[{point}] flow={readings['flow']:.2f} "
                        f"pressure={readings['pressure']:.1f} "
                        f"ph={readings['ph']:.1f} "
                        f"tds={readings['tds']:.0f} "
                        f"temp={readings['temperature']:.1f} "
                        f"-> id={result.get('reading_id', '?')[:8]}... "
                        f"alerts={result.get('alerts_created', 0)}"
                    )
                except Exception as exc:
                    print(f"[{point}] FAILED: {exc}")
            time.sleep(LOOP_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for point_sensors in sensors.values():
            point_sensors["flow"].cleanup()
        print("Cleaned up. Goodbye.")


if __name__ == "__main__":
    main()
