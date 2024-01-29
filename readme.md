# Raspberry Pi Data Logger

## Structure

- `installer.sh` -> set up the raspberry py and install the service
- `enviromental-logger.service` -> systemd service file
- `runner.sh` -> script that runs the python script in the correct environment
- `requirements.txt` -> python dependencies
- `logger.py` -> main python script
- `apa102.py` -> apa102 led strip driver
- `updater.py` -> script that updates the script with the latest version from github

## Functionality

Each core functionality off the logger is implemented in a thread to decouple the reading of the sensor from the writing of the data to the log.
The main thread is responsible for the initialization of the threads and the handling of the signals.

- `run_scd41` is the thread that reads the SCD41 sensor
- `run_pir` is the thread that reads the PIR sensor and keep the window for filtering the data
- `run_logger` is the thread that writes the data to the log file
- `time_checker` is the thread that checks if the time is changed to mark it in the log file

Each thread is wrapped in a block to catch any problem and restart it.

## Installation

```bash
sudo apt install git && git clone https://github.com/FlavioRenzi/RaspberryPi-Enviromental-Data-Logger.git && cd RaspberryPi-Enviromental-Data-Logger

./installer.sh
```
