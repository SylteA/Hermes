import atexit
import json
import os
import signal
import subprocess
from datetime import timedelta

import dotenv
import rx
import rx.operators as ops
from influxdb_client import InfluxDBClient, Point, WriteOptions

dotenv.load_dotenv()


def do_speedtest():
    """
    Runs a speedtest and returns relevant information
    """

    print("Running speedtest")
    process = subprocess.Popen(
        ["speedtest", "-f" "json", "--accept-license", "--accept-gdpr"],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    last_line = ""
    while True:
        line = process.stdout.readline().decode()

        if line.startswith("{"):
            return create_point(line)

        if line != last_line:
            print(line, end="")
            last_line = line


def create_point(line: str) -> Point:
    """Creates a point from our JSON data."""
    data = json.loads(line)

    point = Point(measurement_name="speedtest")

    # Correct timestamp
    point.time(data["timestamp"])

    # Add tags and fields
    point.field("download_bandwidth", data["download"]["bandwidth"])
    point.field("upload_bandwidth", data["upload"]["bandwidth"])

    print(f"Read: {point}")

    return point


def on_exit(**kwargs) -> None:
    for obj in kwargs.values():
        obj.close()


data = rx.interval(period=timedelta(seconds=60)).pipe(
    ops.map(lambda t: do_speedtest()),
    ops.distinct_until_changed(),
    ops.map(lambda point: point.to_line_protocol()),
)

client = InfluxDBClient(
    url=os.environ["INFLUXDB_URL"],
    token=os.environ["INFLUXDB_TOKEN"],
    org=os.environ["INFLUXDB_ORG"],
)
write_api = client.write_api(write_options=WriteOptions(batch_size=1))
write_api.write(bucket="Hermes", record=data)

atexit.register(on_exit, client=client, write_api=write_api)
signal.pause()
