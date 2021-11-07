# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import os
import signal
import sys
import threading
import time

import RPi.GPIO as GPIO
from azure.iot.device.aio import IoTHubModuleClient

PIN_NUMBER = int(os.getenv('PIN_NUMBER', '10'))

# Event indicating client stop
stop_event = threading.Event()


def create_client():
    client = IoTHubModuleClient.create_from_edge_environment()
    return client


async def run_sample(client):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def button_callback(channel):
        print("Button was pushed!")
        asyncio.run(client.send_message_to_output("pushed", "output1"))

    GPIO.add_event_detect(PIN_NUMBER, GPIO.RISING, callback=button_callback)
    while True:
        await asyncio.sleep(1000)


def main():
    if not sys.version >= "3.5.3":
        raise Exception(
            "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version)
    print("IoT Hub Client for Python")

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print("IoTHubClient sample stopped by Edge")
        stop_event.set()
        GPIO.cleanup()  # Clean up

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        print("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
