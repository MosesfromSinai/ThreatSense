# ThreatSense

## Distributed Threat Detection and Classification System

ThreatSense is a distributed proof-of-concept threat detection system designed for real-time object detection at the edge. The project demonstrates how devices such as a Jetson Nano can process live video locally, detect possible threats, and send alerts to a fog-layer device such as a laptop or lab computer.

For safety in our demo, we use fruits such as bananas and cucumbers as mock weapon-shaped objects instead of real weapons.

## Project Overview

Traditional security camera systems often record video passively or rely on cloud-based processing. This can create problems such as:

- slower response times
- single points of failure
- delayed alerts during emergencies

ThreatSense addresses these issues by performing real-time object detection locally and only sends alert information when a potential threat-like object is detected.

## Use Case

This system is designed for security and public safety environments such as:

- schools
- offices
- parking structures
- apartment complexes
- smart infrastructure environments

In a real emergency, response time is very important. ThreatSense is meant to demonstrate how edge and fog computing can be used to detect potential threats faster and organize alerts more efficiently.

## System Design

![ThreatSense System Design](assets/ThreatSense_SysDesign.png)

## Technologies Used

- Jetson Nano
- Camera module or USB webcam
- Laptop or lab computer
- Python
- YOLOv8-N
- TensorRT
- OpenCV
- Local networking
- Alert logging system

## Main Features

- Real-time object detection at the edge
- Mock threat detection using safe objects
- Alert generation with object type, confidence score, timestamp, and frame
- Communication between edge and fog devices
- Real-time alert display
- Detection logging for future analysis

## Project Goals

The main goals of this project are to:

- demonstrate edge-based AI detection
- reduce reliance on cloud processing
- improve alert response time
- create a scalable distributed system design
- safely simulate threat detection using harmless objects

## Running the Demo

Start the fog server on the laptop or lab computer:

```bash
python fog/server.py
```

Test one edge alert without running YOLO:

```bash
python edge/alert_sender.py
```

Run the edge detection camera loop:

```bash
python edge/detect.py
```

## Fog Endpoints

- `GET /` - simple browser dashboard
- `POST /alert` - receives JSON alerts from edge devices
- `GET /alerts` - returns received alerts as JSON
- `GET /devices` - summarizes alerts by device ID
- `GET /health` - checks whether the fog server is running

## Cloud Demo

The cloud layer runs as a Flask API on an AWS EC2 VM:

```bash
python cloud/server.py
```

- Cloud dashboard: `http://52.53.150.132:5001`
- Cloud alert endpoint: `http://52.53.150.132:5001/cloud-alert`
- Cloud alerts API: `http://52.53.150.132:5001/alerts`
- Cloud health check: `http://52.53.150.132:5001/health`
- Cloud verification form: `POST /verify/<alert_id>`

The EC2 security group must allow inbound TCP traffic on port `5001`.

Cloud alerts are stored in `cloud/data/alerts.json`, and captured alert frames
are stored in `cloud/static/alerts/`. The cloud dashboard lets the demo admin
mark each alert as credible or not credible.

## Alert JSON Format

Edge devices send alerts to the fog server as JSON:

```json
{
  "alert_id": "jetson-nano-01-20260519-143000",
  "device_id": "jetson-nano-01",
  "camera_id": 0,
  "timestamp": "2026-05-19 14:30:00",
  "object": "banana",
  "threat_label": "mock_gun_threat",
  "confidence": 0.95,
  "bbox": {
    "x1": 100,
    "y1": 100,
    "x2": 300,
    "y2": 300
  },
  "image_filename": "jetson-nano-01-20260519-143000.jpg",
  "image_data": "base64-encoded-jpeg-data"
}
```

## Team Members

Thursday Project Group 2 - ThreatSense

- Ishaan Venkatraman
- Harshini Saraff
- Ryan Pinto
- Adolfo Magallanes
- Moses Avila
