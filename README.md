# Obico ML API Wrapper integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=baudneo&repository=obico_ml_ha_integration&category=integration)

A Home Assistant integration for CUSTOM self-hosted [Obico](https://www.obico.io/) ML API servers. This integration allows you to detect 3D printing failures by analyzing images from your existing Home Assistant camera/picture entities.

>[!IMPORTANT]
> This integration is NOT affiliated with Obico.io / The Spaghetti Detective. The ML API Wrapper server is a custom wrapper built around the open source, freely available Obico .onnx model for personal use.
> This will not work with an official 'standalone' Obico server installation, you must run the [CUSTOM ML API Wrapper server](https://github.com/baudneo/obico_ml_ha_addon).

>[!NOTE]
> This integration does not continuously stream video/images to the ML server. Instead, it offers a "Trigger" button that you can automate to run inference only when necessary (e.g., when your printer is actually printing), saving resources.

## Features
* **On-Demand Detection**: Manually trigger detection via a Button entity or Action/Service call.
* **Connectivity Monitoring**: Periodically checks your ML server health (`/hc` endpoint).
* **Annotated Camera**: Generates a camera entity showing the latest image with bounding boxes around detected failures (if any).
* **Statistics**: Sensors for Inference Time and Failure Confidence.
* **State Restoration**: Remembers the last detection result and confidence across Home Assistant restarts using the built-in RestoreEntity class.

## Target Audience
This integration is designed for Home Assistant users who:
* Have a 3D printer, a camera with a clear view of the print bed and no built-in failure detection (BambuLabs P1S, etc.).
* Want to leverage their existing Home Assistant camera setup for 3D print failure detection.

## Installation

### Option 1: HACS (Recommended)
1.  Click the "Open in HACS" button above or go to HACS > Integrations > Top Right Menu > Custom Repositories.
2.  Add `https://github.com/baudneo/obico_ml_ha_integration` as an Integration.
3.  Search for "Obico ML API Wrapper" and install.
4.  Restart Home Assistant.

### Option 2: Manual
1.  Copy the `custom_components/obico_ml` directory to your `config/custom_components` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & services**.
2.  Click **Add Integration** and search for **Obico ML API Wrapper**.
3.  Enter the details for your setup:
    * **API URL**: The full URL to your Obico ML server's detection endpoint (e.g., `http://192.168.1.50:3333/detect`).
    * **Camera/Picture to Monitor**: Select the Home Assistant camera/picture entity you want to analyze.
    * **Scan Interval**: How often (in seconds) to check if the ML server is online (Default: 60s). *Note: This does not trigger detection.*
    * **Threshold**: The confidence level (0.0 - 1.0) required to consider a print as "Failed".

## Usage & Automation

### Entities Provided
* **Binary Sensor**: `binary_sensor.obico_ml_failure_detected` (On = Failure, Off = Safe)
* **Connectivity**: `binary_sensor.obico_api_connected`
* **Button**: `button.trigger_detection` (Press to analyze the current camera frame)
* **Camera**: `camera.obico_ml_detection_camera` (Displays the last analyzed frame with bounding boxes)
* **Sensors**: Inference Time (ms) and Confidence (%).

### Service Call
You can trigger a detection via the following service call, the target accepts either a device or an entity of the device which will be used to resolve the device.
The "Trigger Detection" button entity can also be used to trigger detection as it uses this service under the hood.

```yaml
action: obico_ml.trigger_detection
metadata: {}
target:
  device_id: 9ac78b449b222a352196dc52f00006be
data: {}
```

### Example Automation
To save resources, you should only trigger detection when your printer is active. The following automation triggers detection every minute while the printer is printing.
You can take it a step farther and only have this automation enabled when the printer is actively printing and turn the automation off after its been idle for X mins.

```yaml
alias: "Obico: Check for failures while printing"
description: "Triggers Obico ML detection every minute only when the printer is printing."
trigger:
  - platform: time_pattern
    minutes: "/1"  # Run every minute
condition:
  - condition: state
    entity_id: sensor.bambu_p1s_print_status  # Replace with your printer status entity
    state:
      - running
      - Printing
      - printing
action:
  - service: button.press
    target:
      entity_id: button.obico_ml_p1s_trigger_detection
mode: single