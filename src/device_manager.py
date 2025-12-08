import logging
import gpiozero
from typing import Dict, Any, Optional
from .config import AppConfig

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, config: AppConfig):
        self.devices: Dict[str, Any] = {}
        self._initialize_devices(config.devices)

    def _initialize_devices(self, device_configs):
        logger.debug(f"Initializing {len(device_configs)} devices...")
        for device_conf in device_configs:
            try:
                device_class = getattr(gpiozero, device_conf.class_name)
                # Instantiate the device
                instance = device_class(*device_conf.args, **device_conf.kwargs)
                self.devices[device_conf.id] = instance
                logger.info(f"Initialized device '{device_conf.id}' of class '{device_conf.class_name}'")
            except AttributeError:
                logger.error(f"Error: gpiozero class '{device_conf.class_name}' not found.")
            except Exception as e:
                logger.error(f"Error initializing device '{device_conf.id}': {e}")

    def get_device(self, device_id: str) -> Optional[Any]:
        return self.devices.get(device_id)

    def cleanup(self):
        for device in self.devices.values():
            device.close()

