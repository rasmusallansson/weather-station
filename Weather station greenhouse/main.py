# Internal imports. Doesn't require any files.
import pycom                            # Base library for Pycom devices. Here used for the onboard LED.
import time                             # Allows use of time.sleep() for delays.
import machine                          # To be able to use the deepsleep.
from machine import Timer               # To be able to use the timer.
from network import LTE                 # To be able to deinitialize the lte modem before going into deepsleep.

# lib file imports. Files you manually have to put in the project lib folder if not already there.
import keys                             # Imports all passwords. Should be erased if you paste your Ubidots Token straight into main.py.
from pysense import Pysense             # For communication to the Pysense shield.
from telenor import StartIoT            # To establish the internet connection. This might need to be changed if not on a Telenor SIM card.
from umqtt import MQTTClient            # For connection with MQTT protocol.
from LTR329ALS01 import LTR329ALS01     # Light sensor library.
from SI7006A20 import SI7006A20         # Humidity and Temperature sensor library.
from MPL3115A2 import MPL3115A2,PRESSURE # Barometric pressure sensor library.

pycom.heartbeat(False) # Turns the blinking LED (heartbeat) off.

# Global variables. Creates them without giving them a value. To be used later.
chrono = ''
CLIENT_ID = ''
client = ''


def resetTimer():
    # Starts a timer counting the elapsed time since startup.
    # This is used so the board always starts every 300 seconds (5 minutes).
    global chrono
    chrono = Timer.Chrono()
    chrono.reset()
    chrono.start()


def lteConnect():
    # Create a new Telenor Start IoT object using the LTE-M network.
    # Change the `network` parameter if you want to use the NB-IoT
    # network like this: iot = StartIoT(network='nb-iot')
    # You must flash the correct Sequans modem firmware before changing network protocol!
    iot = StartIoT(network='lte-m') # Imports the StartIoT class from telenor.py as iot. This might need to be changed if not on a Telenor SIM card.

    # Connect to the network
    print("Started connecting to the network...")
    iot.connect() # Runs the 'connect' function in the telenor.py file.


def serverConnect():
    global CLIENT_ID
    CLIENT_ID = "fipy-pycom"  # The name you want to call your device.
    SERVER = "things.ubidots.com" # The address to the Ubidots server.
    PORT = 1883
    USER = keys.ubidots_token() # Your Ubidots token.
    KEY = "" # Should be left empty.
    # END OFF SETTINGS

    # Using the MQTT protocol to connect to Ubidots.
    global client
    client = MQTTClient(CLIENT_ID, SERVER, PORT, USER, KEY)
    client.connect() # Establishes the connection to Ubidots.


def publishData():
    # The following three blocks catches the data from the sensors, manipulates the values and saves them as variables.
    py = Pysense()
    lt = LTR329ALS01(py)
    si = SI7006A20(py)
    mp = MPL3115A2(py)

    # Calculates the mean of the intensity of red and blue color sensors.
    sum = 0
    for i in lt.light():
        sum = sum + i
    l = round(sum / len(lt.light()), 1)

    # Rounds the numbers. The last value sets number of decimals.
    t = round(si.temperature(), 1)
    h = round(si.humidity(), 1)
    p = round(mp.pressure()/100, 1) # Makes it hPa as is more commonly used.

    global client
    global CLIENT_ID
    # The words before the : in the next line is the Ubidots variable names. These can be changed for your preference.
    # The %s is a placeholder for the variables you want to send, placed in paranthesis at the end.
    # "value" is just to let Ubidots know what type of data is received.
    msg = b'{"light": {"value": %s}, "temperature": {"value": %s}, "humidity": {"value": %s}, "pressure": {"value": %s}}' % (l, t, h, p)
    print(msg)
    client.publish(b"/v1.6/devices/" + CLIENT_ID, msg)
    time.sleep(5) # This holds the code for 5 seconds so the publishing doesn't get interrupted.


def sleep():
    global client
    client.disconnect()   # Disconnects from Ubidots server.
    client = None
    print("Disconnected from Ubidots.")

    lte = LTE()
    lte.deinit()    # Disables the LTE modem to lower the power consumption during deepsleep.

    global chrono
    time = 300 - chrono.read() # Calculates the time in seconds for how long the deepsleep will be active.
    print("Going to sleep for %s seconds." % (time))
    sleepTime = int(time * 1000) # Converts the time to milliseconds and the data type to int.
    machine.deepsleep(sleepTime) # Turns deepsleep on. When time has passed the FipY will reboot and read the code from the top of the file.

# This is where the program starts and calls the functions defined above.
resetTimer()

lteConnect()

serverConnect()

publishData()

sleep()
