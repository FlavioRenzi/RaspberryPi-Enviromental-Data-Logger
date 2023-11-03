#!/usr/bin/env bash

# Enable spi and i2c
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

# Install python3
sudo apt update
sudo apt install python3-dev python3-venv -y

# Install python3-venv
python -m venv logger_env
source logger_env/bin/activate
pip install -r requirements.txt

# Install systemd service
sudo cp enviromental_logger.service /etc/systemd/system/logger.service
sudo systemctl daemon-reload
sudo systemctl enable enviromental_logger.service
sudo reboot
