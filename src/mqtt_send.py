import string,threading,sqlite3
import paho.mqtt.client as mqtt
from random import seed
from random import random

#=============================================================#
# mqtt_send.py risiede nella stessa directory che ospita      #
# broadcast_msg_pyq5.py e ha lo scopo di inviare a un server  #
# mqtt i dati del mesh attivo in tempo reale in modo che chi  #
# fosse collegato in subscribe possa avere contezza del suo   #
# stato. Per ottenere ciò mqtt_send accede al DB sqlite3 ogni #
# 30 secondi per leggere l'ultimo record inserito e inviarlo  #
# al server mqtt.                                             #
#=============================================================#
# Database Manager Class
class DatabaseManager():
	def __init__(self):
		self.conn = sqlite3.connect(DB_Name)
		self.conn.execute('pragma foreign_keys = on')
		self.conn.commit()
		self.cur = self.conn.cursor()
		#print("Sqlite DB connected..")
		
	def retrieve_db_record(self, sql_query, args=()):
		self.cur.execute(sql_query)
		#self.conn.commit()
		rows = self.cur.fetchall()
		return rows

	def __del__(self):
		self.cur.close()
		self.conn.close()
#==========================================================

# SQLite DB Name
DB_Name =  "meshDB.db"

history = 20   # invia gli ultimi 20 record
dbObj = DatabaseManager()
qr = "select max(_id) from connessioni"
res = dbObj.retrieve_db_record(qr)
lastid = res[0][0]-history
#print ("Last id = "+str(lastid))
del dbObj

def checkLast(dbObj):
    #print("CheckLast..")
    qr = "select max(_id) from connessioni"
    res = dbObj.retrieve_db_record(qr)
    global lastid
    global history
    #print(res,lastid)
    fields = ['data','ora','user','alt','lat','lon','batt','snr','dist','rilev']
    while (res[0][0] > lastid):
        qr = "select * from connessioni where _id > "+str(lastid)+" limit 1"
        lastid = lastid+1 #res[0][0]
        row = dbObj.retrieve_db_record(qr)
        message = {}
        i = 0
        for field in fields:
            message[field] = str(row[0][i])
            i += 1     
        print("message: "+str(message))
        publish_To_Topic(pubtopic,str(message))
    lastid -= history
    del dbObj
    
MQTT_Broker = "broker.emqx.io"
pubtopic = "meshtastic/vinloren"

# seed random number generator
seed(7)
s = str(random())
cname = "Myclient-"+s[2:19]
print(cname)
count = 1

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc != 0:
        print ("Unable to connect to MQTT Broker...")
        pass
    else:
        print ("Connected with MQTT Broker: " + str(MQTT_Broker))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


def on_publish(client, userdata, mid):
    print ("Message "+str(count)+" sent")
    pass
		
def on_disconnect(client, userdata, rc):
    print ("Disconnect status = "+str(rc))
    if rc !=0:
	    pass

def publish_To_Topic(pubtopic,message):
	client.publish(pubtopic,message)
	print ("Published: " + message + " " + "on MQTT Topic: " + str(pubtopic))
	print ("")

client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo",password='none')
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_Broker, 1883, 60)

def publish_to_MQTT():
    dbObj = DatabaseManager()
    tmr = threading.Timer(60.0, publish_to_MQTT)
    tmr.start()
    checkLast(dbObj)
    del dbObj

publish_to_MQTT()    
client.loop_forever()
