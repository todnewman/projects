#!/usr/bin/env python
# -*- coding: utf-8 -*-
from RPi_AS3935 import RPi_AS3935
import RPi.GPIO as GPIO
import thread
import pandas as pd
import time
from time import sleep
from datetime import datetime
from Adafruit_BME280 import *
from threading import Thread


filename = '/home/pi/lightning_sensor_data.csv'

test = False

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
print ("GPIO setmode")

# pin used for interrupts
pin = 17
# 1 Raspberry Pis should leave bus set at 0, while rev. 2 Pis should set
# bus equal to 1. The address should be changed to match the address of the
# sensor.

#sensor = RPi_AS3935(address=0x03, bus=1)
#sensor.reset()
sensor_env = BME280(p_mode=BME280_OSAMPLE_8, t_mode=BME280_OSAMPLE_2, h_mode=BME280_OSAMPLE_1, filter=BME280_FILTER_16)

# Change this value to the tuning value for your sensor

time.sleep(0.005)
#sensor.calibrate(tun_cap=0x02)
time.sleep(0.005)

# Indoors = more sensitive (can miss very strong lightnings)
# Outdoors = less sensitive (can miss far away lightnings)

#sensor.set_indoors(False)
#sensor.set_noise_floor(1)


# Prevent single isolated strikes from being logged => interrupts begin after 5 strikes, then are fired normally

#sensor.set_min_strikes(1)

last_alert = datetime.min
strikes_since_last_alert = 0

cols = ['Time', 'Energy', 'Distance', 'Temperature (deg F)', 'Pressure (HP-900)', 'Humidity (%)','Full Light Spectrum', 'IR Spectrum', 'Luminosity (lux)']

def data_collect(cur_time, energy, distance):
 
    lst = []
    degrees = sensor_env.read_temperature()*9.0/5.0+32
    pascals = sensor_env.read_pressure()
    hectopascals = pascals / 100
    humidity = sensor_env.read_humidity()
    Temp      = '{0:0.3f} deg F'.format(degrees)
    Pressure  = '{0:0.2f} hPa'.format(hectopascals)
    Humidity  = '{0:0.2f} %'.format(humidity)
    lux, full, ir = call_tsl2591()
    print (Temp, Pressure, Humidity, full, ir, lux)

 
    lst.append([cur_time, energy, distance, degrees, hectopascals, humidity, full, ir, lux ])
    data = pd.DataFrame(lst, columns = cols)
    
    df = pd.read_csv(filename, index_col=0)
    
    df = df.append(data, ignore_index=False)

    df.to_csv(filename)

def periodic_data():
    current_timestamp = datetime.now()
    cur_time = current_timestamp.strftime('%H:%M:%S - %Y/%m/%d')
    distance = 0
    energy = 0
    data_collect(cur_time, energy, distance)

def call_tsl2591():
    import tsl2591

    tsl = tsl2591.Tsl2591()  # initialize
    full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
    lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
    return (lux, full, ir)


# Interrupt handler
def handle_interrupt( channel):
    global last_alert
    global strikes_since_last_alert
    global sensor
    global LastStatus
    global LastInterrupt
    current_timestamp = datetime.now()
    time.sleep(0.003)
    
    # Set up Pandas Dataframe for data collection
    
    logf = open("/home/pi/error.log", "a")
    try:
        #reason = sensor.get_interrupt()
        reason = 15
        LastInterrupt = reason
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        logf.write("%s: Had to run 12cdetect to handle an i2c error\n" % current_timestamp )      
    if reason == 0x00:
        LastStatus = 'Spurious Interrupt'
    elif reason == 0x01:
        LastStatus = 'Noise level too high'
        noise = sensor.get_noise_floor()
        if (noise < 7):
            print("Noise level too high - adjusting")
            logf.write("%s: External Noise level is too high - adjusting noise floor to be %s\n" % (current_timestamp, noise+1))
            sensor.raise_noise_floor()
            #noise = sensor.get_noise_floor()
            #logf.write("Noise level now at %s\n" % noise)
    elif reason == 0x04:
        LastStatus = 'Disturber detected'
        print("Disturber detected. Masking subsequent disturbers")
        logf.write("%s: Disturber detected. Masking subsequent disturbers\n" % current_timestamp)
        sensor.set_mask_disturber(True)
    elif reason == 0x08:
        LastStatus = 'Lightning detected'
        cur_time = current_timestamp.strftime('%H:%M:%S - %Y/%m/%d')
        print("We sensed lightning! (%s)" % cur_time)
        logf.write("%s: We sensed lightning!\n" % current_timestamp)
        if (current_timestamp - last_alert).seconds < 300:
            print("Last strike is too recent, incrementing counter since last alert.\n")
            logf.write("%s: Last strike is too recent, incrementing counter since last alert.\n" % current_timestamp)
            strikes_since_last_alert += 1
            return
        distance = sensor.get_distance()
        energy = sensor.get_energy()
        print("Energy: " + str(energy) + " - distance: " + str(distance) + "km")
        last_alert = current_timestamp
        data_collect(cur_time, energy, distance)
    # If no strike has been detected for the last hour, reset the strikes_since_last_alert (consider storm finished)
    elif test:
        cur_time = current_timestamp.strftime('%H:%M:%S - %Y/%m/%d')
        distance = 40
        energy = 60
        data_collect(cur_time, energy, distance)
    if (current_timestamp - last_alert).seconds > 1800 and last_alert != datetime.min:
        strikes_since_last_alert = 0
        last_alert = datetime.min
    logf.close()
    #GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    time.sleep(0.005)
    sensor.calibrate(tun_cap=0x02)
    time.sleep(0.005)


def wait_for_lightning():

    print("Waiting for lightning - or at least something that looks like it")

    try:
        while True:
            # Read/clear the sensor data every 10s in case we missed an interrupt (interrupts happening too fast ?)
            time.sleep(1)
            handle_interrupt( pin)
    finally:
        # cleanup used pins... just because cleanliness is next to Godliness!  
        GPIO.cleanup()
        
if __name__ == '__main__':

    # Use a software Pull-Down on interrupt pin
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #sensor.set_mask_disturber(False)
    GPIO.add_event_detect(pin, GPIO.RISING, callback=handle_interrupt, bouncetime=300)
    #GPIO.add_event_detect(pin, GPIO.FALLING, callback=handle_interrupt, bouncetime=300)

    #Thread(target=wait_for_lightning).start() # Start watching for lightning.  We'll always trigger any time it comes in.
    Thread(target=periodic_data).start() # Look for environmental data every hour. Initialize here. 
    while True:
        sleep(3600)
        Thread(target=periodic_data).start() # Every hour start the Thread again.
