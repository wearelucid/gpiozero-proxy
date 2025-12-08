# GPIOZero Proxy Server API Specification

This document defines the WebSocket API for the GPIOZero Proxy Server. The server uses the **JSON-RPC 2.0** protocol to enable remote control of Raspberry Pi GPIO devices.

## Connection

- **Protocol**: WebSocket (ws:// or wss://)
- **Default Port**: 8765
- **Path**: `/` (root)

## Protocol: JSON-RPC 2.0

All messages (requests, responses, and notifications) must adhere to the [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification).

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": { ... },
  "id": "request_id"
}
```

### Response Format (Success)

```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": "request_id"
}
```

### Response Format (Error)

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32xxx,
    "message": "Error description"
  },
  "id": "request_id"
}
```

---

## Methods

### 1. `call`

Executes a method on a device instance.

**Parameters:**

- `device_id` (string, required): The ID of the device as defined in the server configuration.
- `method` (string, required): The name of the method to call on the device (e.g., `on`, `off`, `blink`, `toggle`).
- `args` (array, optional): Positional arguments for the method.
- `kwargs` (object, optional): Keyword arguments for the method.

**Result:**

- Returns the return value of the called method (can be `null`).

**Example:**
_Turn on an LED._

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "device_id": "led1",
    "method": "on"
  },
  "id": 1
}

// Response
{
  "jsonrpc": "2.0",
  "result": null,
  "id": 1
}
```

### 2. `read`

Reads the value of a property from a device.

**Parameters:**

- `device_id` (string, required): The ID of the device.
- `property` (string, required): The name of the property to read (e.g., `value`, `is_pressed`, `is_active`).

**Result:**

- Returns the value of the property.

**Example:**
_Check if a button is pressed._

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "read",
  "params": {
    "device_id": "btn1",
    "property": "is_pressed"
  },
  "id": 2
}

// Response
{
  "jsonrpc": "2.0",
  "result": true,
  "id": 2
}
```

### 3. `write`

Sets the value of a property on a device.

**Parameters:**

- `device_id` (string, required): The ID of the device.
- `property` (string, required): The name of the property to set.
- `value` (any, required): The value to assign to the property.

**Result:**

- Returns `"ok"` on success.

**Example:**
_Set PWM LED brightness to 50%._

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "write",
  "params": {
    "device_id": "pwm1",
    "property": "value",
    "value": 0.5
  },
  "id": 3
}

// Response
{
  "jsonrpc": "2.0",
  "result": "ok",
  "id": 3
}
```

### 4. `subscribe`

Subscribes to a device event. When the event occurs on the server, a notification will be sent to the client. The server maps the event name to `when_{event}`.

**Parameters:**

- `device_id` (string, required): The ID of the device.
- `event` (string, required): The event name (e.g., `pressed` for `when_pressed`, `released` for `when_released`).

**Result:**

- Returns `"subscribed"` on success.

**Example:**
_Subscribe to button press events._

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "subscribe",
  "params": {
    "device_id": "btn1",
    "event": "pressed"
  },
  "id": 4
}

// Response
{
  "jsonrpc": "2.0",
  "result": "subscribed",
  "id": 4
}
```

### 5. `list_devices`

Retrieves a list of all configured devices.

**Parameters:**

- None

**Result:**

- Returns an array of device objects, each containing `id` and `class`.

**Example:**
_Get all devices._

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "list_devices",
  "id": 5
}

// Response
{
  "jsonrpc": "2.0",
  "result": [
    { "id": "my_led", "class": "LED" },
    { "id": "my_button", "class": "Button" }
  ],
  "id": 5
}
```

---

## Notifications (Server to Client)

### `gpio.event`

Sent by the server when a subscribed event triggers.

**Params:**

- `device_id` (string): The ID of the device that triggered the event.
- `event` (string): The event name (e.g., `pressed`).
- `data` (any): The current value of the device at the time of the event (e.g., `1` for pressed, `0` for released).

**Example:**
_Notification received when 'btn1' is pressed._

```json
{
  "jsonrpc": "2.0",
  "method": "gpio.event",
  "params": {
    "device_id": "btn1",
    "event": "pressed",
    "data": 1
  }
}
```

---

## Error Codes

| Code   | Message          | Description                                   |
| :----- | :--------------- | :-------------------------------------------- |
| -32700 | Parse error      | Invalid JSON was received by the server.      |
| -32600 | Invalid Request  | The JSON sent is not a valid Request object.  |
| -32601 | Method not found | The method does not exist / is not available. |
| -32602 | Invalid params   | Invalid method parameter(s).                  |
| -32603 | Internal error   | Internal JSON-RPC error.                      |

---

## Client Implementation Guidelines

1.  **Connection Management**: Implement logic to reconnect automatically if the WebSocket connection drops.
2.  **ID Generation**: Use unique IDs for each request to correctly match responses (e.g., incrementing integer or UUID).
3.  **Notification Handling**: Do not expect an ID in `gpio.event` messages. Register a handler for the `gpio.event` method.
4.  **Error Handling**: Check for the `error` field in responses and handle accordingly.
