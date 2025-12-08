import argparse
import asyncio
import logging
import sys
from .config import load_config
from .device_manager import DeviceManager
from .server import GPIOProxyServer

logger = logging.getLogger(__name__)

def setup_logging(level_name):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    parser = argparse.ArgumentParser(description="GPIOZero Proxy Server")
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level')
    args = parser.parse_args()

    setup_logging(args.log_level)

    try:
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.critical(f"Failed to load config: {e}")
        sys.exit(1)

    device_manager = DeviceManager(config)
    server = GPIOProxyServer(config, device_manager)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server.start())
        logger.info("Server running. Press Ctrl+C to stop.")
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
    finally:
        device_manager.cleanup()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    main()
