import string,sys,ast
import paho.mqtt.client as mqtt
from random import seed
from random import random

MQTT_Broker = "broker.emqx.io"  
channel     = "meshtastic/vinloren"
    
print("MQTT_Broker = "+MQTT_Broker)
print("Channel id  = "+channel)

subtopic = channel

# seed random number generator
seed(7)
s = str(random())
cname = "Myclient-"+s[2:19]
print(cname)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(subtopic,0)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+":")
    b = msg.payload
    dats = ast.literal_eval(b.decode("utf-8"))
    if(dats['lat'] != 'None'):
        dats['lat'] = dats['lat'][0:8]
    if(dats['lon'] != 'None'):
        dats['lon'] = dats['lon'][0:8]
    if(dats['rilev'] != 'None'):
        dats['rilev'] = dats['rilev'][0:5]
    if(dats['dist'] != 'None'):
        dist = float(dats['dist'])/1000
        dists = str(dist)[0:5]
        dats['dist'] = dists
    print(dats)
    
client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo",password='none')
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_Broker, 1883, 60) 

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()