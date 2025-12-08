import yaml
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8765

@dataclass
class DeviceConfig:
    id: str
    class_name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AppConfig:
    server: ServerConfig
    devices: List[DeviceConfig]

def load_config(path: str) -> AppConfig:
    logger.debug(f"Reading config file: {path}")
    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    server_data = data.get('server', {})
    server_config = ServerConfig(
        host=server_data.get('host', '0.0.0.0'),
        port=server_data.get('port', 8765)
    )

    devices_data = data.get('devices', [])
    device_configs = []
    for d in devices_data:
        device_configs.append(DeviceConfig(
            id=d['id'],
            class_name=d['class'],
            args=d.get('args', []),
            kwargs=d.get('kwargs', {})
        ))
    
    logger.debug(f"Loaded {len(device_configs)} devices from config")
    return AppConfig(server=server_config, devices=device_configs)
