from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import time as t
import json
import threading
import math

# AWS IoT constants
ENDPOINT = "<IoT core endPoint>"
DEVICE_ID = "<mac-address>"
OWNER_ID = "<unique owner id>"
PATH_TO_CERTIFICATE = "certs/device.crt"
PATH_TO_PRIVATE_KEY = "certs/private.key"
PATH_TO_AMAZON_ROOT_CA_1 = "certs/ca.pem"
TELEMETRY_TOPIC = f"{DEVICE_ID}/telemetry"
DB_ERROR_TOPIC = "error/dynamodb"
SHADOW_GET_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/get"
SHADOW_UPDATE_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/update"
SHADOW_DELTA_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/update/delta"
SHADOW_GET_ACCEPTED = f"$aws/things/{DEVICE_ID}/shadow/get/accepted"
SHADOW_GET_REJECTED = f"$aws/things/{DEVICE_ID}/shadow/get/rejected"

TELEMETRY_INTERVAL = 10  # Seconds

# Global MQTT connection
mqtt_connection = None

def on_message_received(topic, payload, **kwargs):
    """Handle incoming messages for subscribed topics."""
    print(f"Received message on topic {topic}: {payload.decode('utf-8')}")
    try:
        message = json.loads(payload.decode("utf-8"))
        if topic == SHADOW_DELTA_TOPIC:
            handle_shadow_delta(message)
        elif topic == SHADOW_GET_ACCEPTED:
            process_shadow_get_response(message)
        elif topic == SHADOW_GET_REJECTED:
            print(f"Shadow GET request rejected: {message}")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON payload: {e}")
    except Exception as e:
        print(f"Unexpected error processing message: {e}")

def process_shadow_get_response(response):
    """Process the shadow state response."""
    print(f"Processing shadow GET response: {response}")
    if "state" in response and "reported" in response["state"]:
        reported_state = response["state"]["reported"]
        print(f"Shadow reported state: {reported_state}")
        # Process the shadow data as needed
    else:
        print("Shadow GET response does not contain 'reported' state.")

def handle_shadow_delta(delta):
    """Handle incoming shadow delta updates and apply changes."""
    global TELEMETRY_INTERVAL
    print(f"Processing shadow delta: {delta}")
    desired_state = delta.get("state", {})
    if "telemetryInterval" in desired_state:
        TELEMETRY_INTERVAL = desired_state["telemetryInterval"]
        print(f"Updated telemetry interval to {TELEMETRY_INTERVAL} seconds")
        send_reported_state({"telemetryInterval": TELEMETRY_INTERVAL})

def send_reported_state(reported_state):
    """Send the reported state back to AWS IoT Thing Shadow."""
    update_payload = {
        "state": {
            "reported": reported_state
        }
    }
    mqtt_connection.publish(
        topic=SHADOW_UPDATE_TOPIC,
        payload=json.dumps(update_payload),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    print(f"Sent reported state: {update_payload}")

def fetch_shadow_state():
    """Request the current shadow state."""
    try:
        mqtt_connection.publish(
            topic=SHADOW_GET_TOPIC,
            payload=json.dumps({}),  # Empty payload as per AWS IoT Shadow protocol
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        print(f"Shadow state fetch requested for {DEVICE_ID}")
    except Exception as e:
        print(f"Error requesting shadow state: {e}")

def publish_telemetry():
    """Publish telemetry data to the telemetry topic."""
    while True:
        telemetry_data = {
            "ownerID": OWNER_ID,
            "deviceData": {
                "Pressure": round(1000 + 500 * math.sin(t.time() / 10), 2),  # Simulated sine wave pressure in PSI
                "Pressure-unit": "PSI",  
            }
        }
        mqtt_connection.publish(
            topic=TELEMETRY_TOPIC,
            payload=json.dumps(telemetry_data),
            qos=mqtt.QoS.AT_LEAST_ONCE
        )
        send_reported_state({"status": "connected"})  # Update shadow status to "connected"
        print(f"Published telemetry: {telemetry_data}")
        t.sleep(TELEMETRY_INTERVAL)

def main():
    global mqtt_connection

    # Set up AWS IoT resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=PATH_TO_CERTIFICATE,
        pri_key_filepath=PATH_TO_PRIVATE_KEY,
        client_bootstrap=client_bootstrap,
        ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
        DEVICE_id=DEVICE_ID,
        clean_session=False,
        keep_alive_secs=6,
    )

    print(f"Connecting to {ENDPOINT} with client ID '{DEVICE_ID}'...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    # Subscribe to shadow topics
    print(f"Subscribing to {SHADOW_DELTA_TOPIC}")
    mqtt_connection.subscribe(
        topic=SHADOW_DELTA_TOPIC,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received,
    )
    print(f"Subscribing to {SHADOW_GET_ACCEPTED}")
    mqtt_connection.subscribe(
        topic=SHADOW_GET_ACCEPTED,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received,
    )
    print(f"Subscribing to {SHADOW_GET_REJECTED}")
    mqtt_connection.subscribe(
        topic=SHADOW_GET_REJECTED,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received,
    )

    print(f"Subscribing to {DB_ERROR_TOPIC}")
    mqtt_connection.subscribe(
        topic=DB_ERROR_TOPIC,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received,
    )

    # Wait to ensure subscriptions are active
    t.sleep(2)

    # Fetch initial shadow state
    fetch_shadow_state()

    # Start telemetry publishing in a separate thread
    telemetry_thread = threading.Thread(target=publish_telemetry)
    telemetry_thread.daemon = True
    telemetry_thread.start()

    # Run indefinitely
    try:
        while True:
            t.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        send_reported_state({"status": "disconnected"})
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")

if __name__ == "__main__":
    main()
