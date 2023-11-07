import apa102
import time
import signal
import sys
import time
import os
import RPi.GPIO as GPIO
import threading
from sensirion_i2c_scd import Scd4xI2cDevice
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection

class Pixels:
    PIXELS_N = 3

    def __init__(self):
        self.colors = [0] * 3 * self.PIXELS_N
        self.dev = apa102.APA102(num_led=self.PIXELS_N)

    def off(self):
        self.write([0] * 3 * self.PIXELS_N)

    def write(self, colors):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(colors[3*i]), int(colors[3*i + 1]), int(colors[3*i + 2]))
        self.dev.show()
        
    def write_one(self, i, color):
        self.dev.set_pixel(i, int(color[0]), int(color[1]), int(color[2]))
        self.dev.show()

pixels = Pixels()

def threadwrap(threadfunc):
    while True:
        try:
            threadfunc()
        except Exception as e:
            time.sleep(1)
            print('{!r}, at time: {}, timestamp: {}; restarting thread'.format(e,time.asctime(time.localtime()),time.time()))


last_sample = {
    'co2': 0,
    'temperature': 0,
    'humidity': 0,
    'presence': 0,
    'scd41_status': 'OK',
    'pir_status': 'OK',
    'pir_average': 0,
    'restarted': 'true'
}

def run_scd41():
    try:
        with LinuxI2cTransceiver('/dev/i2c-1') as i2c_transceiver:
            pixels.write_one(2, [0, 20, 0])
            last_sample['scd41_status'] = 'OK'
            i2c_connection = I2cConnection(i2c_transceiver)    
            scd41 = Scd4xI2cDevice(i2c_connection)
            
            #to fix i2c deadlock
            scd41.stop_periodic_measurement()
            scd41.wake_up()
            scd41.reinit()

            # start periodic measurement in high power mode
            scd41.start_periodic_measurement()

            # Measure every 5 seconds
            while True:
                time.sleep(5)
                co2, temperature, humidity = scd41.read_measurement()
                last_sample['co2'] = co2.co2
                last_sample['temperature'] = temperature.degrees_celsius
                last_sample['humidity'] = humidity.percent_rh
                
                # use default formatting for printing output:
                #print("{}, {}, {}".format(co2, temperature, humidity))
            scd41.stop_periodic_measurement()
    except Exception as e:
        last_sample['scd41_status'] = 'ERROR'
        pixels.write_one(2, [20, 0, 0])
        raise e


def run_pir(interval=0.5, window=30):
    try:
        pixels.write_one(1, [0, 20, 0])
        last_sample['pir_status'] = 'OK'
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(32, GPIO.IN)
        pir_window = [0]*int(window/interval)
        index = 0
        while True:
            if GPIO.input(32) == GPIO.HIGH:
                #print("HIGH")
                pir_window[index] = 1
                index = (index + 1) % len(pir_window)
            else:
                #print("LOW")
                pir_window[index] = 0
                index = (index + 1) % len(pir_window)
            time.sleep(interval)
            last_sample['pir_average'] = sum(pir_window)/len(pir_window)
            if sum(pir_window) > 0:
                last_sample['presence'] = 1
                pixels.write_one(0, [0, 0, 20])
            else:
                last_sample['presence'] = 0
                pixels.write_one(0, [0, 0, 0])
    except Exception as e:
        last_sample['pir_status'] = 'ERROR'
        pixels.write_one(1, [20, 0, 0])
        raise e


def run_logger(interval):
    filename = '/home/siemens/logger/data.csv'
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write('timestamp,co2,temperature,humidity,presence,pir_average,scd41_status,pir_status,restarted\n')
    time.sleep(6)
    with open(filename, 'a') as f:
        while True:
            new_row = '{},{},{},{},{},{},{},{},{}\n'.format(
                time.time(),
                last_sample['co2'],
                last_sample['temperature'],
                last_sample['humidity'],
                last_sample['presence'],
                last_sample['pir_average'],
                last_sample['scd41_status'],
                last_sample['pir_status'],
                last_sample['restarted']
            )
            f.write(new_row)
            #print(new_row)
            f.flush()
            last_sample['restarted'] = 'false'
            time.sleep(interval)

def time_checker():
    last_time = time.time()
    while True:
        time.sleep(1)
        if abs(time.time() - last_time) > 2:
            print('Change on time detected')
            last_sample['restarted'] += ' time changed'
        last_time = time.time()
        print(time.time())

def signal_handler(sig, frame):
    pixels.off()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    t1 = threading.Thread(target=lambda: threadwrap(lambda: run_scd41()), daemon=True)
    t2 = threading.Thread(target=lambda: threadwrap(lambda: run_pir(interval=0.2, window=30)), daemon=True)
    t3 = threading.Thread(target=lambda: threadwrap(lambda: run_logger(interval=30)), daemon=True)
    t4 = threading.Thread(target=lambda: threadwrap(lambda: time_checker()), daemon=True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
