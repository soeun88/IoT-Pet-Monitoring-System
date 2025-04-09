from umqtt.simple import MQTTClient
import network
import time
import ujson
from machine import Pin
import urandom

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

MQTT_CLIENT_ID = "db51abfec5ac47b39d1a1023f94246d5"
MQTT_BROKER = "mqtt.thingsboard.cloud"
MQTT_USER = "0UDFVxOsIOXuxbMUUq0b"
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



##led##
# LED 핀 설정
pin_index_list = [15, 2, 4, 16, 17]
# Define LED pin list
led_pin_list = []
# Add LED pin object
for i in pin_index_list:
    led_pin_list.append(Pin(i, Pin.OUT))

# LED 초기 상태 설정
for led_pin in led_pin_list:
    led_pin.value(0)

def sub_cb(topic, msg):
    global activityStatus
    print((topic, msg))
    jsLoads = ujson.loads(msg)
    print(type(jsLoads), jsLoads)

    decode_topic = topic.decode('utf-8')
    start=decode_topic.index("v1/devices/me/rpc/request/")+len("v1/devices/me/rpc/request/")
    requestID = decode_topic[start:].strip()
    
    if jsLoads["method"] == "ActivityON":
        activityStatus = 1
        print("Activity ON")
        send_RPC("Activity", activityStatus)
    
    elif jsLoads["method"] == "ActivityOFF":
        activityStatus = 0
        print("Activity OFF")
        send_RPC("Activity", activityStatus)
    
    if jsLoads["method"] == "ledStatus":
        send_RPC("ledStatus", activityStatus)

    client.publish(MQTT_RPC_RESPONSE + requestID, msg)

def send_RPC(key, value):
    message = ujson.dumps({
         key: value,
    })
    client.publish(MQTT_TELEMETRY, message)

def publish():
    message = ujson.dumps({
        "Activity" : activityStatus
    })
    client.publish(MQTT_TELEMETRY, message, qos=1)


def led_control():
    if activityStatus == 1:
        # 무작위로 LED 선택
        random_led = urandom.choice(led_pin_list)
        # 현재 LED 상태의 반대로 전환
        random_led.value(not random_led.value())
        # 1초 대기
        time.sleep(1)
        random_led.value(not random_led.value())
    else:
        for led in led_pin_list:
            led.value(0)



activityStatus = 0
##main##
def main():
    global activityStatus
    client.set_callback(sub_cb)
    client.subscribe(MQTT_TOPIC)

    while True:
        publish()
        client.check_msg()
        led_control()
        print(activityStatus)
        send_RPC("ledStatus", activityStatus)


if __name__ == '__main__':
    main()