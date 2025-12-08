#!/bin/bash

# Exit on error
set -e

echo "Installing GPIOZero Proxy Server..."

# Get the directory where the script is running
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
USER_NAME=$(whoami)
GROUP_NAME=$(id -gn)

# Virtual Environment Setup
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
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

