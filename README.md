# GPIOZero Proxy Server

A WebSocket proxy server for controlling Raspberry Pi GPIO devices using `gpiozero`, utilizing the **JSON-RPC 2.0** protocol.

## Features

- **Configurable**: Define devices in `config.yaml`.
- **JSON-RPC 2.0 API**: Standardized protocol for commands and events.
- **Extensible**: Supports any `gpiozero` class dynamically.

## Installation

### Manual Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python -m src.main --config config.yaml --log-level INFO
   ```

### Systemd Installation (Raspberry Pi OS)

For production use with auto-restart:

1. Run the install script:
   ```bash
   ./install.sh
   ```

This will:

- Create a virtual environment in `./venv`
- Install dependencies
- Register a systemd service `gpiozero-proxy` that starts on boot

You can then manage the service:

```bash
sudo systemctl status gpiozero-proxy
sudo systemctl restart gpiozero-proxy
sudo journalctl -u gpiozero-proxy -f  # Follow logs
```

## Configuration

Edit `config.yaml` to define your devices.

```yaml
server:
  host: 0.0.0.0
  port: 8765

devices:
  - id: my_button
    class: Button
    args: [2]
    kwargs:
      pull_up: true
      bounce_time: 0.1

  - id: my_led
    class: LED
    args: [17]

  - id: my_pwm
    class: PWMLED
    args: [18]
    kwargs:
      frequency: 100

  - id: my_rgb
    class: RGBLED
    args: [9, 10, 11]
    kwargs:
      pwm: true
      initial_value: [0, 0, 0]

  - id: my_motor
    class: Motor
    args: [4, 14]

  - id: my_servo
    class: Servo
    args: [22]
```

## JSON-RPC API

The server supports the following methods.

### 1. Call a Method

Executes a method on the `gpiozero` device instance.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "device_id": "my_led",
    "method": "on",
    "args": [],
    "kwargs": {}
  },
  "id": 1
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": null,
  "id": 1
}
```

### 2. Read a Property

Reads a property value from the device.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "read",
  "params": {
    "device_id": "my_button",
    "property": "is_pressed"
  },
  "id": 2
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": false,
  "id": 2
}
```

### 3. Write a Property

Sets a property value on the device.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "write",
  "params": {
    "device_id": "my_led",
    "property": "value",
    "value": 0.5
  },
  "id": 3
}
```

### 4. Subscribe to Events

Subscribes to `when_` events. For example, subscribing to `pressed` hooks into `when_pressed`.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "subscribe",
  "params": {
    "device_id": "my_button",
    "event": "pressed"
  },
  "id": 4
}
```

**Server Notification (Event):**
When the event triggers, the server sends a JSON-RPC notification (no `id`).

```json
{
  "jsonrpc": "2.0",
  "method": "gpio.event",
  "params": {
    "device_id": "my_button",
    "event": "pressed",
    "data": 1
  }
}
```
