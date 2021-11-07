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
from azure.iot.device import MethodResponse

LED_PIN_NUMBER = int(os.getenv('LED_PIN_NUMBER', '7'))

# Event indicating client stop
stop_event = threading.Event()


def create_client():
    client = IoTHubModuleClient.create_from_edge_environment()

    # Define function for handling received messages
    async def receive_message_handler(message):
        thread = threading.Thread(target=blink_led)
        thread.start()
        await client.send_message_to_output(message, "output1")

    def blink_led():
        for _ in range(10):
            GPIO.output(LED_PIN_NUMBER, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LED_PIN_NUMBER, GPIO.LOW)
            time.sleep(0.2)

    async def receive_method_request_handler(method_request):
        thread = threading.Thread(target=blink_led)
        thread.start()
        method_response = MethodResponse.create_from_method_request(method_request, 200, None)
        await client.send_method_response(method_response)

    try:
        # Set handler on the client
        client.on_message_received = receive_message_handler
        client.on_method_request_received = receive_method_request_handler
    except:
        # Cleanup if failure occurs
        client.shutdown()
        raise

    return client


async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(LED_PIN_NUMBER, GPIO.OUT)
    # e.g. sending messages
    while True:
        await asyncio.sleep(1000)


def main():
    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "IoT Hub Client for Python" )

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print ("IoTHubClient sample stopped by Edge")
        stop_event.set()

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
