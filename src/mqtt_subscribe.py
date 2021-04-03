import string,sys,ast,io
import paho.mqtt.client as mqtt
from random import seed
from random import random

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTabWidget, \
            QTableWidgetItem,QVBoxLayout,QHBoxLayout,QLineEdit,QLabel,QPushButton,QComboBox     
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
import folium
from PyQt5 import QtWidgets, QtWebEngineWidgets


class Interceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9,es;q=0.8,de;q=0.7")


class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.title = 'Active Mesh Data Show'
        self.interceptor = Interceptor()
        self.initUI()
        
    def initUI(self):
        self.labels = ['data','ora','user','alt','lat','lon','batt','snr','dist','rilev']
        mylatlbl = QLabel("Home lat:")
        mylonlbl = QLabel("Home lon:")
        self.mylat = QLineEdit()
        self.mylon = QLineEdit()
        self.mylat.setText('45.641174')
        self.mylon.setText('9.114828')
        histlabel = QLabel('History Length: ')
        self.hist = QLineEdit()
        histlabel.setMaximumWidth(72)
        self.hist.setMaximumWidth(34)
        self.hist.setText('0')
        channlbl =  QLabel("My Mesh:")
        self.chann = QLineEdit()
        self.chann.setText('vinloren')
        self.chann.setMaximumWidth(60)
        self.startb = QPushButton("START",self)
        self.startb.setMaximumWidth(86)
        self.startb.clicked.connect(self.start_click)
        lblmap = QLabel("Tipo Map")
        self.combomap = QComboBox(self)
        self.combomap.addItem("OpenStreetMap")
        self.combomap.addItem('Stamen Terrain')
        self.combomap.addItem("Stamen Toner")
        self.combomap.addItem("CartoDB positron")
        self.combomap.addItem("CartoDB dark_matter")
        voidlbl = QLabel("")
        voidlbl.setMinimumWidth(280)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(self.title)
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        hhead = QHBoxLayout()
        hhead.addWidget(mylatlbl)
        hhead.addWidget(self.mylat)
        hhead.addWidget(mylonlbl)
        hhead.addWidget(self.mylon)
        hhead.addWidget(histlabel)
        hhead.addWidget(self.hist)
        hhead.addWidget(channlbl)
        hhead.addWidget(self.chann)
        hhead.addWidget(self.startb)
        hhead.addWidget(lblmap)
        hhead.addWidget(self.combomap)
        hhead.addWidget(voidlbl)
         # Add tabs
        self.tabs.addTab(self.tab1,"MyMesh")
        self.tabs.addTab(self.tab2,"Map")
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.labels))
        self.table.setHorizontalHeaderLabels(self.labels)
        self.tab1.layout = QVBoxLayout()
        self.tab1.layout.addWidget(self.table)
        self.tab1.setLayout(self.tab1.layout)
        self.layout.addLayout(hhead)
        self.layout.addWidget(self.tabs)
        self.setGeometry(100, 100, 1000,600)
        self.show()

    def start_click(self):
        global RUNNING
        if(RUNNING == False):
            connetti()
            RUNNING = True
            self.startb.setText('SHOW MAP')
        else:
            if(len(packet) == int(self.hist.text())):
                self.showMap()

    def showMap(self):
        homeLoc = {}
        homeLoc['lat'] = float(self.mylat.text())
        homeLoc['lon'] = float(self.mylon.text())
        self.map1 = folium.Map(
            location=[homeLoc['lat'],homeLoc['lon']], tiles=self.combomap.currentText(), zoom_start=13
        )
        folium.Marker([homeLoc['lat'],homeLoc['lon']],
            #Make color/style changes here
            icon = folium.Icon(color='blue'),
            popup = 'Home node',
        ).add_to(self.map1)
        global packet
        global msgcount
        for msg in packet:
            lat = float(msg['lat'])
            lon = float(msg['lon'])
            user = msg['user']
            snr = msg['snr']
            ora = msg['ora']
            dist = msg['dist']
            folium.Marker([lat,lon],
                icon = folium.Icon(color='red'),
                popup = user+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                ora+'<br>snr: '+str(snr)+'<br>Km: '+str(dist),
            ).add_to(self.map1)
            folium.Marker([lat,lon],
              icon=folium.DivIcon(html=f"""<div style='font-size:20px; font-weight: bold;'>{user}</div>""")
            ).add_to(self.map1)
            print("Mark added")
        data = io.BytesIO()
        self.map1.save(data, close_file=False)
        self.map1 = QtWebEngineWidgets.QWebEngineView()
        self.map1.setHtml(data.getvalue().decode())
        self.map1.page().profile().setUrlRequestInterceptor(self.interceptor)
        self.tabs.removeTab(1)
        self.tab2.destroy()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2,"Map")
        self.tab2.layout = QVBoxLayout()
        self.tab2.layout.addWidget(self.map1)
        self.tab2.setLayout(self.tab2.layout)
        self.map1.show()
        packet = []
        msgcount = 0


MQTT_Broker = "broker.emqx.io"  
channel     = "meshtastic/"
    
print("MQTT_Broker = "+MQTT_Broker)
print("Channel id  = "+channel)

subtopic = channel

# seed random number generator
seed(7)
s = str(random())
cname = "Myclient-"+s[2:19]
print(cname)
msgcount = 0
packet = []
RUNNING = False

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
    ex.hist.setText(str(dats['nrec']))
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
    fillTable(dats)


def fillTable(dats):
    r = int(ex.hist.text())
    ex.table.setRowCount(r)
    global msgcount
    global packet
    items = []
    i = 0
    for field in ex.labels:
        items.append(QTableWidgetItem())
        items[i].setText(dats[field])
        ex.table.setItem(msgcount,i,items[i])
        i += 1
    msgcount += 1
    if(len(packet) < r):
        packet.append(dats)

    
client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo",password='none')
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_Broker, 1883, 60) 

def connetti():
    global channel
    global subtopic
    subtopic = channel+ex.chann.text()
    client.connect(MQTT_Broker, 1883, 60) 
    client.loop_start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_()) 

    