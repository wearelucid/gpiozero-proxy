import asyncio
import json
import websockets
from typing import Dict, Set, Any, Optional
import logging
from collections import defaultdict
from .config import AppConfig
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)

# JSON-RPC Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

class GPIOProxyServer:
    def __init__(self, config: AppConfig, device_manager: DeviceManager):
        self.config = config
        self.device_manager = device_manager
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[websockets.WebSocketServerProtocol, Set[str]] = defaultdict(set)
        
        self.loop = asyncio.get_event_loop()
        
        # Track which events we have already hooked
        self.hooked_events: Set[str] = set() # "device_id:event_name"

    async def start(self):
        start_server = websockets.serve(
            self.handler, 
            self.config.server.host, 
            self.config.server.port
        )
        logger.info(f"Starting server on {self.config.server.host}:{self.config.server.port}")
        await start_server

    async def handler(self, websocket: websockets.WebSocketServerProtocol):
        self.clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.clients)}")
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.error(f"Client connection error: {e}")
        finally:
            self.clients.remove(websocket)
            if websocket in self.client_subscriptions:
                del self.client_subscriptions[websocket]
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def process_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        logger.debug(f"Received message: {message}")
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await self.send_error(websocket, None, PARSE_ERROR, "Parse error")
            return

        # Validate JSON-RPC 2.0
        if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
            await self.send_error(websocket, data.get('id'), INVALID_REQUEST, "Invalid Request")
            return

        method = data.get("method")
        params = data.get("params")
        msg_id = data.get("id")

        if not method:
             await self.send_error(websocket, msg_id, INVALID_REQUEST, "Method is required")
             return

        # Dispatch
        try:
            if method == "call":
                await self.handle_call(websocket, msg_id, params)
            elif method == "read":
                await self.handle_read(websocket, msg_id, params)
            elif method == "write":
                await self.handle_write(websocket, msg_id, params)
            elif method == "subscribe":
                await self.handle_subscribe(websocket, msg_id, params)
            elif method == "list_devices":
                await self.handle_list_devices(websocket, msg_id)
            else:
                await self.send_error(websocket, msg_id, METHOD_NOT_FOUND, f"Method '{method}' not found")
        except Exception as e:
            logger.error(f"Internal error processing {method}: {e}", exc_info=True)
            await self.send_error(websocket, msg_id, INTERNAL_ERROR, str(e))

    async def handle_call(self, websocket, msg_id, params):
        if not isinstance(params, dict):
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "Params must be an object")
             return
             
        device_id = params.get('device_id')
        method_name = params.get('method')
        args = params.get('args', [])
        kwargs = params.get('kwargs', {})

        if not device_id or not method_name:
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "device_id and method are required")
             return

        device = self.device_manager.get_device(device_id)
        if not device:
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Device '{device_id}' not found")
            return

        if not hasattr(device, method_name):
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Method '{method_name}' not found on device")
            return

        attr = getattr(device, method_name)
        if not callable(attr):
                await self.send_error(websocket, msg_id, INVALID_PARAMS, f"'{method_name}' is not callable")
                return
        
        try:
            result = attr(*args, **kwargs)
            await self.send_response(websocket, msg_id, result)
        except Exception as e:
            await self.send_error(websocket, msg_id, INTERNAL_ERROR, str(e))

    async def handle_read(self, websocket, msg_id, params):
        if not isinstance(params, dict):
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "Params must be an object")
             return

        device_id = params.get('device_id')
        prop_name = params.get('property')

        if not device_id or not prop_name:
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "device_id and property are required")
             return

        device = self.device_manager.get_device(device_id)
        if not device:
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Device '{device_id}' not found")
            return

        if not hasattr(device, prop_name):
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Property '{prop_name}' not found on device")
            return

        try:
            value = getattr(device, prop_name)
            if hasattr(value, 'value'): 
                 value = value.value
            
            await self.send_response(websocket, msg_id, value)
        except Exception as e:
            await self.send_error(websocket, msg_id, INTERNAL_ERROR, str(e))

    async def handle_write(self, websocket, msg_id, params):
        if not isinstance(params, dict):
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "Params must be an object")
             return

        device_id = params.get('device_id')
        prop_name = params.get('property')
        value = params.get('value')

        if not device_id or not prop_name:
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "device_id and property are required")
             return

        device = self.device_manager.get_device(device_id)
        if not device:
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Device '{device_id}' not found")
            return

        if not hasattr(device, prop_name):
            await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Property '{prop_name}' not found on device")
            return

        try:
            setattr(device, prop_name, value)
            await self.send_response(websocket, msg_id, "ok")
        except Exception as e:
            await self.send_error(websocket, msg_id, INTERNAL_ERROR, str(e))

    async def handle_subscribe(self, websocket, msg_id, params):
        if not isinstance(params, dict):
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "Params must be an object")
             return

        device_id = params.get('device_id')
        event_name = params.get('event') 
        
        if not device_id or not event_name:
             await self.send_error(websocket, msg_id, INVALID_PARAMS, "device_id and event are required")
             return

        device = self.device_manager.get_device(device_id)
        if not device:
             await self.send_error(websocket, msg_id, INVALID_PARAMS, f"Device '{device_id}' not found")
             return

        hook_key = f"{device_id}:{event_name}"
        self.client_subscriptions[websocket].add(hook_key)

        if hook_key not in self.hooked_events:
            attr_name = f"when_{event_name}"
            if hasattr(device, attr_name):
                def callback(device_instance=None): 
                     self.broadcast_event(device_id, event_name, getattr(device, 'value', None))
                
                setattr(device, attr_name, callback)
                self.hooked_events.add(hook_key)
                logger.info(f"Hooked event {attr_name} for {device_id}")
            else:
                logger.warning(f"Device {device_id} has no event {attr_name}")
                # We could return an error, but subscription might be optimistic
        
        await self.send_response(websocket, msg_id, "subscribed")

    async def handle_list_devices(self, websocket, msg_id):
        devices = []
        for device_conf in self.config.devices:
            devices.append({
                "id": device_conf.id,
                "class": device_conf.class_name
            })
        await self.send_response(websocket, msg_id, devices)

    def broadcast_event(self, device_id, event_name, value):
        message = json.dumps({
            "jsonrpc": "2.0",
            "method": "gpio.event",
            "params": {
                "device_id": device_id,
                "event": event_name,
                "data": value
            }
        })
        hook_key = f"{device_id}:{event_name}"
        
        asyncio.run_coroutine_threadsafe(self._broadcast_message(message, hook_key), self.loop)

    async def _broadcast_message(self, message, hook_key):
        targets = []
        for client in self.clients:
            if hook_key in self.client_subscriptions[client]:
                targets.append(client)
        
        if targets:
            await asyncio.gather(
                *[client.send(message) for client in targets], 
                return_exceptions=True
            )

    async def send_response(self, websocket, req_id, result):
        if req_id is None: return # Notifications don't get responses
        msg = {
            "jsonrpc": "2.0",
            "result": result,
            "id": req_id
        }
        await websocket.send(json.dumps(msg))

    async def send_error(self, websocket, req_id, code, message):
        msg = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": req_id
        }
        await websocket.send(json.dumps(msg))
