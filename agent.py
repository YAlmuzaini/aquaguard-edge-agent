from datetime import datetime, timezone
import os
import time

from dotenv import load_dotenv
import requests

from sensors.flow_sensor import FlowSensor
from sensors.ph_sensor import PhSensor
from sensors.pressure_sensor import PressureSensor
from sensors.tds_sensor import TdsSensor
from sensors.temp_sensor import TemperatureSensor, discover_temperature_sensors

load_dotenv()

PIPELINE_ID = os.environ.get("PIPELINE_ID", "a0000000-0000-0000-0000-000000000001")
INGEST_URL = os.environ["INGEST_URL"]
INGEST_SECRET = os.environ["INGEST_TOKEN"]
LOOP_INTERVAL_SEC = int(os.environ.get("SAMPLE_INTERVAL_SEC", "3"))
REQUEST_TIMEOUT_SEC = int(os.environ.get("REQUEST_TIMEOUT_SEC", "10"))

POINT_CONFIG = {
    "A": {"ads_address": 0x48, "flow_pin": 17},
    "B": {"ads_address": 0x49, "flow_pin": 27},
}


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


def main():
    temp_files = discover_temperature_sensors()
    if len(temp_files) < 2:
        raise RuntimeError("Expected 2 DS18B20 sensors, found fewer than 2.")

    sensors = {
        "A": {
            "temperature": TemperatureSensor(temp_files[0]),
            "ph": PhSensor(ads_address=POINT_CONFIG["A"]["ads_address"], channel=1),
            "tds": TdsSensor(ads_address=POINT_CONFIG["A"]["ads_address"], channel=0),
            "pressure": PressureSensor(
                ads_address=POINT_CONFIG["A"]["ads_address"], channel=2
            ),
            "flow": FlowSensor(gpio_pin=POINT_CONFIG["A"]["flow_pin"]),
        },
        "B": {
            "temperature": TemperatureSensor(temp_files[1]),
            "ph": PhSensor(ads_address=POINT_CONFIG["B"]["ads_address"], channel=1),
            "tds": TdsSensor(ads_address=POINT_CONFIG["B"]["ads_address"], channel=0),
            "pressure": PressureSensor(
                ads_address=POINT_CONFIG["B"]["ads_address"], channel=2
            ),
            "flow": FlowSensor(gpio_pin=POINT_CONFIG["B"]["flow_pin"]),
        },
    }

    print("AquaGuard edge agent started.")
    print(f"Pipeline: {PIPELINE_ID}")
    print("Sending point A and point B telemetry every 3 seconds.")

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
                        f"[{point}] uploaded reading_id={result.get('reading_id')} "
                        f"alerts_created={result.get('alerts_created', 0)}"
                    )
                except Exception as exc:
                    print(f"[{point}] upload failed: {exc}")
            time.sleep(LOOP_INTERVAL_SEC)
    finally:
        for point_sensors in sensors.values():
            point_sensors["flow"].cleanup()


if __name__ == "__main__":
    main()
