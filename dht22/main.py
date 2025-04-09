from umqtt.simple import MQTTClient
import network
import time
import ujson
from machine import Pin, PWM
import dht

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

MQTT_CLIENT_ID = "e61e37cf682b45939e89808f5857e40f"
MQTT_BROKER = "mqtt.thingsboard.cloud"
MQTT_USER = "Cenn6WiPqNto8WMf19qo"
MQTT_PASSWORD = ""
MQTT_PORT = "1883"
MQTT_TELEMETRY = "v1/devices/me/telemetry"
MQTT_RPC_REQUEST = "v1/devices/me/rpc/request/+"
MQTT_RPC_RESPONSE = "v1/devices/me/rpc/response/"


print("Connecting to MQTT server... ", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT,
user=MQTT_USER, password=MQTT_PASSWORD)
client.connect()
print("Connected!")
#------------------------------------------------------------------

dht22 = dht.DHT22(Pin(15))
led_r = PWM(Pin(26, Pin.OUT), freq = 1000, duty = 0)
led_g = PWM(Pin(25, Pin.OUT), freq = 1000, duty = 0)
led_b = PWM(Pin(33, Pin.OUT), freq = 1000, duty = 0)

prev_weather = ""

temperature = 25.0
humidity = 40.0
humBoolean = 0
setTemperatureStatus = 0

def publish():
    message = ujson.dumps({
        "temperature": temperature,
        "humidity": humidity,
    })
    client.publish(MQTT_TELEMETRY, message, qos=1)

def send_RPC(key, value):
    message = ujson.dumps({
        key: value,
    })
    client.publish(MQTT_TELEMETRY, message)

def sub_cb(topic, msg):
    global humBoolean
    global setTemperatureStatus
    print((topic, msg))
    jsLoadmsg = ujson.loads(msg)
    
    decode_topic = topic.decode('utf-8')
    start = decode_topic.index("v1/devices/me/rpc/request/") + len("v1/devices/me/rpc/response/")
    requestID = decode_topic[start:].strip()

    if jsLoadmsg["method"] == "humLEDstatus":
        send_RPC("humLEDstatus", humBoolean)

    if jsLoadmsg["method"] == "temperatureControl":
        send_RPC("temperatureControl", tempBoolean)
    
    if jsLoadmsg["method"] == "setTemperature":
        if jsLoadmsg["params"] == "ON":
            setTemperatureStatus = 1
            change_dht22()

        else :
            setTemperatureStatus = 0
            change_dht22()
    
    client.publish(MQTT_RPC_RESPONSE + requestID, msg)

    

def change_dht22():

    global temperature
    global humidity
    global humBoolean
    global setTemperatureStatus


    
    print(temperature, humidity)
    if temperature <= 10:
        led_r.duty(0)
        led_g.duty(0)
        led_b.duty(1000)

    
    if humidity <= 25:
        led_r.duty(0)
        led_g.duty(1000)
        led_b.duty(1000)
        humBoolean = 1
        send_RPC("humLEDstatus", humBoolean)
        print(humBoolean)

    if setTemperatureStatus == 1: #난방 on
        led_r.duty(1000)
        led_g.duty(0)
        led_b.duty(0)
        temperature += 1
        humidity -= 0.5
        if humidity <= 0:
            humidity = 0
        if temperature >= 28:
            setTemperatureStatus = 0
    
    else : #난방 off
        temperature -= 1.0
        humidity -= 0.5
        if humidity <= 0:
            humidity = 0

        if temperature > 10 and humidity > 25:
            led_r.duty(0)
            led_g.duty(0)
            led_b.duty(0)
        
        send_RPC("humLEDstatus", humBoolean)




client.set_callback(sub_cb)                                                                                                
client.subscribe(MQTT_RPC_REQUEST)
def main():
    global temperature
    global humidity
    global prev_weather

    while True:
        dht22.measure()

        change_dht22()
        publish()
     

        client.check_msg()
        

if __name__ == '__main__':
    main()
