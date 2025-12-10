#!/bin/bash

# Exit on error
set -e

echo "Installing GPIOZero Proxy Server..."

# Get the directory where the script is running
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
USER_NAME=$(whoami)
GROUP_NAME=$(id -gn)

# Parse arguments
usage() {
    echo "Usage: $0 [-c|--config <path_to_config>]"
    exit 1
}

CUSTOM_CONFIG=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -c|--config) CUSTOM_CONFIG="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Configuration Setup
if [ -n "$CUSTOM_CONFIG" ]; then
    CONFIG_FILE="$CUSTOM_CONFIG"
    # Convert to absolute path if possible (realpath might not be available on all minimal systems, but usually is)
    if command -v realpath >/dev/null 2>&1 && [ -f "$CONFIG_FILE" ]; then
        CONFIG_FILE=$(realpath "$CONFIG_FILE")
    fi
    echo "Using custom config file: $CONFIG_FILE"
else
    CONFIG_FILE="$SCRIPT_DIR/config.yaml"
    EXAMPLE_CONFIG="$SCRIPT_DIR/config.yaml.example"

    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$EXAMPLE_CONFIG" ]; then
            echo "Creating config.yaml from example..."
            cp "$EXAMPLE_CONFIG" "$CONFIG_FILE"
        else
            echo "Warning: config.yaml.example not found!"
        fi
    else
        echo "config.yaml already exists, skipping creation."
    fi
fi

# Virtual Environment Setup
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" --system-site-packages
fi

# Install Dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Service Configuration
SERVICE_NAME="gpiozero-proxy"
TEMPLATE_FILE="$SCRIPT_DIR/systemd/gpiozero-proxy.service.template"
SERVICE_FILE="/tmp/$SERVICE_NAME.service"
PYTHON_EXEC="$VENV_DIR/bin/python"

echo "Generating systemd service file..."
sed -e "s|{{USER}}|$USER_NAME|g" \
    -e "s|{{GROUP}}|$GROUP_NAME|g" \
    -e "s|{{WORKDIR}}|$SCRIPT_DIR|g" \
    -e "s|{{PYTHON_EXEC}}|$PYTHON_EXEC|g" \
    -e "s|{{CONFIG_FILE}}|$CONFIG_FILE|g" \
    "$TEMPLATE_FILE" > "$SERVICE_FILE"

echo "Installing service (requires sudo)..."
sudo mv "$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"
sudo chown root:root "/etc/systemd/system/$SERVICE_NAME.service"
sudo chmod 644 "/etc/systemd/system/$SERVICE_NAME.service"

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable "$SERVICE_NAME"

echo "Starting service..."
sudo systemctl restart "$SERVICE_NAME"

echo "------------------------------------------------"
echo "Installation Complete!"
echo "Status: sudo systemctl status $SERVICE_NAME"
echo "Logs:   sudo journalctl -u $SERVICE_NAME -f"
echo "------------------------------------------------"

