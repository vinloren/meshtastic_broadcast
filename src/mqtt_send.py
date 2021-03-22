import string,threading,sqlite3,datetime,time,sys
import paho.mqtt.client as mqtt
from random import seed
from random import random

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, \
            QVBoxLayout,QHBoxLayout,QLineEdit,QTextEdit,QLabel,QPushButton      

#=============================================================#
# mqtt_send.py risiede nella stessa directory che ospita      #
# broadcast_msg_pyq5.py e ha lo scopo di inviare a un server  #
# mqtt i dati del mesh attivo in tempo reale in modo che chi  #
# fosse collegato in subscribe possa avere contezza del suo   #
# stato. Per ottenere ciò mqtt_send accede al DB sqlite3 ogni #
# 375 secs per leggere tutti i record inseriti fra data e     #
# data e inviarli al server mqtt tralasciando i record che    #
# non cambiano posizione per meno di 10mt.                    #
#=============================================================#


class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.title = 'Pubblica dati Mesh'
        self.initUI()
        
    def initUI(self):
        iniziolbl = QLabel("Pubblica da ")
        finelbl = QLabel("a ")
        self.inizio = QLineEdit()
        self.fine = QLineEdit()
        self.startb = QPushButton("START",self)
        channlbl =  QLabel("My Mesh:")
        self.chann = QLineEdit()
        self.chann.setText('vinloren')
        voidlbl = QLabel("")
        voidlbl.setMinimumWidth(240)
        hhead = QHBoxLayout()
        hhead.addWidget(iniziolbl)
        hhead.addWidget(self.inizio)
        hhead.addWidget(finelbl)
        oggi = datetime.datetime.now().strftime("%y/%m/%d")
        self.inizio.setText(oggi)
        domanit = time.time()+86400
        domanis = time.localtime(domanit)
        domani = str(domanis.tm_year-2000)+"/"
        if(domanis.tm_mon < 10):
            domani = domani +'0'+str(domanis.tm_mon)+'/'
        else:
            domani = domani + str(domanis.tm_mon)+'/'
        if(domanis.tm_mday < 10):
            domani = domani + '0'+str(domanis.tm_mday)
        else:
            domani = domani + str(domanis.tm_mday)
        self.fine.setText(domani)
        hhead.addWidget(self.fine)
        hhead.addWidget(channlbl)
        hhead.addWidget(self.chann)
        self.startb.clicked.connect(self.start_click)
        hhead.addWidget(self.startb)
        hhead.addWidget(voidlbl)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(self.title)
        self.layout.addLayout(hhead)
        self.log = QTextEdit()
        self.layout.addWidget(self.log)
        self.setGeometry(100, 100, 700,450)
        self.show()

    def start_click(self):
        connetti()


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

def checkLast(dbObj,inizio,fine):
    qr = "select * from connessioni where data >='"+inizio+"' and data < '"+fine+"' and dist is not null order by user,_id"
    res = dbObj.retrieve_db_record(qr)
    fields = ['data','ora','user','alt','lat','lon','batt','snr','dist','rilev']
    messages = []
    lastuser = ""
    r = 0
    for row in res:
        msg = {}
        i = 0
        for field in fields:
            msg[field] = str(row[i])
            i += 1   
        if(lastuser != msg['user']):
            lastuser = msg['user']
            messages.append(msg)
            r += 1
            #print(lastuser)
        else:
            prvdist = float(messages[r-1]['dist'])
            #print(str(prvdist)+" "+msg['dist'])
            if(abs(prvdist-float(msg['dist']))>10):
                messages.append(msg)
                r += 1
            else:
                messages[r-1] = msg
    print("numero record:"+str(r))
    for msg in messages:
        msg.update({'nrec': r})
        #print(msg['user'])
        publish_To_Topic(pubtopic,str(msg))

    
MQTT_Broker = "broker.emqx.io"
pubtopic = "meshtastic/"

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
    dataora = datetime.datetime.now().strftime("%d/%m/%y %T")
    ex.log.append(dataora+" Published: "+message+" on Topic: " + str(pubtopic))

client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo",password='none')
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_Broker, 1883, 60)

def publish_to_MQTT():
    dbObj = DatabaseManager()
    tmr = threading.Timer(375.0, publish_to_MQTT)
    tmr.start()
    checkLast(dbObj,ex.inizio.text(),ex.fine.text())
    del dbObj

def connetti():
    global pubtopic
    pubtopic = "meshtastic/"+ex.chann.text()
    publish_to_MQTT()    
    client.loop_start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_()) 
