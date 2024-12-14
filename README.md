# AWS IoT Device Integration README

## Overview

This repository provides example Python scripts for integrating IoT devices with AWS IoT Core. These scripts demonstrate how to:

- Publish telemetry data for single and multiple sensor devices.
- Manage device shadow states.
- Handle MQTT communication securely using AWS IoT credentials.

## Requirements

1. **AWS IoT Configuration**:
   - AWS IoT endpoint.
   - Device certificates (private key, public key, and Amazon Root CA).
2. **Python Libraries**:
   - `awscrt`
   - `awsiot`
   - `json`
   - `math`
   - `threading`
3. **IoT Core Setup**:
   - AWS IoT Thing registered in your AWS account.
   - Properly configured IoT policies and certificates.

## Folder Structure

The project contains two Python scripts:

1. **Single Sensor Device (thing-pressure-sensor.py)**: Script for publishing telemetry data from a device with a single sensor.
2. **Multi-Sensor Device (thing-temp-humi-sensor.py)**: Script for publishing telemetry data from a device with multiple sensors.

## Key Constants for AWS IoT

The following constants are essential for configuring the device to communicate with AWS IoT Core:

```python
# AWS IoT constants
ENDPOINT = "<IoT core endPoint>"  # IoT Core endpoint
DEVICE_ID = "<mac-address>"  # Unique device ID for the device
OWNER_ID = "<unique owner id>"  # Identifier for the device owner
PATH_TO_CERTIFICATE = "certs/device.crt"  # Path to the device certificate
PATH_TO_PRIVATE_KEY = "certs/private.key"  # Path to the private key
PATH_TO_AMAZON_ROOT_CA_1 = "certs/ca.pem"  # Path to Amazon Root CA

# Topics
TELEMETRY_TOPIC = f"{DEVICE_ID}/telemetry"  # Publish
DB_ERROR_TOPIC = "error/dynamodb"  # Publish
SHADOW_GET_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/get"  # Publish
SHADOW_UPDATE_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/update"  # Publish
SHADOW_DELTA_TOPIC = f"$aws/things/{DEVICE_ID}/shadow/update/delta"  # Subscribe
SHADOW_GET_ACCEPTED = f"$aws/things/{DEVICE_ID}/shadow/get/accepted"  # Subscribe
SHADOW_GET_REJECTED = f"$aws/things/{DEVICE_ID}/shadow/get/rejected"  # Subscribe
```

## Example Telemetry Data Structure

To send telemetry data, structure your payload as follows:

### Single Sensor Device:
```python
telemetry_data = {
    "ownerID": OWNER_ID,
    "deviceData": {
        "Pressure": round(1000 + 500 * math.sin(t.time() / 10), 2),
        "Pressure-unit": "PSI",
    }
}
```

### Multi-Sensor Device:
```python
telemetry_data = {
    "ownerID": OWNER_ID,
    "deviceData": {
        "Temperature": round(20 + 10 * math.sin(t.time() / 10), 2),
        "Temperature-unit": "Celsius",
        "Humidity": round(50 + 20 * math.cos(t.time() / 10), 2),
        "Humidity-unit": "Percent",
    }
}
```

## Device Shadow Management

The scripts use AWS IoT Device Shadow for:

1. Fetching the current device state.
2. Handling shadow delta updates for changes in desired state.
3. Sending reported state updates back to AWS IoT Core.

### Topics Used:
- `SHADOW_GET_TOPIC`: Request the shadow state.
- `SHADOW_UPDATE_TOPIC`: Update the reported state.
- `SHADOW_DELTA_TOPIC`: Handle delta updates.

## Usage Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install Dependencies**:
   ```bash
   pip install awscrt awsiot
   ```

3. **Configure Constants**:
   Update the constants in the scripts to match your AWS IoT Core setup.

4. **Run the Script**:
   - For single sensor device:
     ```bash
     python single_sensor_device.py
     ```
   - For multi-sensor device:
     ```bash
     python multi_sensor_device.py
     ```

## Notes

- The telemetry interval can be dynamically adjusted using the AWS IoT Device Shadow.
- Ensure that the AWS IoT Thing policy allows necessary operations (`iot:Publish`, `iot:Subscribe`, `iot:Connect`, `iot:GetThingShadow`, `iot:UpdateThingShadow`).

## Troubleshooting

- **Connection Issues**: Verify the endpoint, certificates, and IoT policy.
- **Telemetry Not Updating**: Check the shadow delta topic for pending desired state updates.
- **JSON Decode Errors**: Ensure the payload structure matches the expected format.

