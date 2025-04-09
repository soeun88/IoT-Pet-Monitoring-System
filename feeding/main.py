from umqtt.simple import MQTTClient
import network
import time
import ujson
from machine import Pin, PWM

WIFI_SSID = 'Wokwi-GUEST'
WIFI_PASS = ''

print("Connecting to WiFi network '{}'".
format(WIFI_SSID))
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

while not wifi.isconnected():
    time.sleep(1)
    print('WiFi connect retry ...')
print('WiFi IP:', wifi.ifconfig()[0])

MQTT_CLIENT_ID = "ee00adf5d28247a0a39f21a7e79e3e09"
MQTT_BROKER = "mqtt.thingsboard.cloud"
MQTT_USER = "Ozlzj76CY6PohFzZaaVZ"
MQTT_PASSWORD = ""
MQTT_PORT = "1883"
MQTT_TELEMETRY = "v1/devices/me/telemetry"
MQTT_TOPIC = "v1/devices/me/rpc/request/+"
MQTT_RPC_RESPONSE = "v1/devices/me/rpc/response/"


print("Connecting to MQTT server... ", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT,
user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()
print("Connected!")

def send_RPC(key, value):
    message = ujson.dumps({
        key: value,
    })
    client.publish(MQTT_TELEMETRY, message)


def sub_cb(topic, msg):
    global feedingStatus
    global wateringStatus
    global feedAlert

    print("sub_cb")
    print((topic, msg))
    jsLoads = ujson.loads(msg)
    print(type(jsLoads), jsLoads)

    decode_topic = topic.decode('utf-8')
    start=decode_topic.index("v1/devices/me/rpc/request/")+len("v1/devices/me/rpc/request/")
    requestID = decode_topic[start:].strip()
    
    if jsLoads["method"] == "FeedingON":
        print("feeding ON")
        feedingStatus = 1

    if jsLoads["method"] == "wateringON":
        print("watering ON")
        wateringStatus = 1



    client.publish(MQTT_RPC_RESPONSE + requestID, msg)

        
 



def publish():
    global feedingStatus
    global feedingAmount
    global waterAmount

    message = ujson.dumps({
        "feedAlert" : feedAlert,
        "feedAmount" : feedAmount,
        "waterAmount" : waterAmount
    })
    client.publish(MQTT_TELEMETRY, message, qos=1)


def feeding():
    global feedAmount
    global feedingStatus
    global feedAlert

    if feedingStatus == 1:
        feedAmount += 50
        feedingStatus = 0
        feedAlert = 0
        
    if feedAmount > 0:
        feedAmount -= 1
        print(feedAmount)
    if feedAmount == 0:
        feedAlert = 1
    
    print(feedAlert)

    
    send_RPC("Feeding", feedAlert)


def watering():
    global waterAmount
    global wateringStatus 
    if wateringStatus == 1:
        if waterAmount > 50:
            waterAmount = 100
            wateringStatus = 0
        else :
            waterAmount += 50
            wateringStatus = 0
    if waterAmount == 0:
        waterAmount += 50
    if waterAmount > 0:
        waterAmount -= 1
    if waterAmount >= 100:
        waterAmount = 100


led_r = PWM(Pin(27, Pin.OUT), freq = 1000, duty = 0)
led_g = PWM(Pin(26, Pin.OUT), freq = 1000, duty = 0)
led_b = PWM(Pin(25, Pin.OUT), freq = 1000, duty = 0)

def led_control():
    global feedAlert

    if feedAlert == 1:
        led_r.duty(1000)
        led_g.duty(0)
        led_b.duty(0)
        print("led ON")
    else:
        led_r.duty(0)
        led_g.duty(0)
        led_b.duty(0)



feedingStatus = 0
feedAmount = 10
waterAmount = 30
wateringStatus = 0
feedAlert = 0
##main##
client.set_callback(sub_cb)
client.subscribe(MQTT_TOPIC)
while True:
    publish()
    
   
    client.check_msg()
    feeding()
    watering()
    led_control()

