import sys,math,io
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTabWidget, \
            QTableWidgetItem,QVBoxLayout,QHBoxLayout,QLineEdit,QTextEdit,QLabel,QCheckBox, \
            QPushButton,QRadioButton,QComboBox       
from PyQt5.QtGui import QIcon
import folium
from PyQt5 import QtWidgets, QtWebEngineWidgets

import sqlite3 as dba
import meshtastic
from pubsub import pub
import threading
import time
from time import sleep
import datetime

RUNNING = False
count = 0
msgcount = 1
homeLoc = {}
nodeInfo = []

class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.title = 'Meshtastic data show'
        self.initUI()
        
    def initUI(self):
        self.labels = ['data ora','origine','destinazione','tipo messaggio','payload','utente', \
            'da_id','a_id','altitudine','latitudine','longitudine','rxSnr','distanza','rilevamento']
        self.labels1 = ['data ora','user','altitudine','latitudine','longitudine','batteria%', \
            'rxsnr','distanza','rilevamento']
        self.csvFile = open('meshtastic_data.csv','wt')
        mylatlbl = QLabel("Home lat:")
        mylonlbl = QLabel("Home lon:")
        voidlbl = QLabel("")
        voidlbl.setMinimumWidth(300)
        self.mylat = QLineEdit()
        self.mylon = QLineEdit()
        #mylatlbl.setMaximumWidth(60)
        #mylonlbl.setMaximumWidth(60)
        mapbtn =  QPushButton("SHOW MAP",self)
        #mapbtn.setMaximumWidth(110)
        self.radiob = QRadioButton('Storico giorno:')
        #self.setMaximumWidth(100)
        self.combobox = QComboBox(self)
        self.combobox.setMinimumWidth(90)
        fra = QLabel("fra")
        self.fragiorno = QLineEdit()
        self.fragiorno.setText('21/01/01')
        #self.fragiorno.setMaximumSize(70,24)
        et = QLabel("e")
        self.egiorno = QLineEdit()
        oggi = datetime.datetime.now().strftime("%y/%m/%d")
        self.egiorno.setText(oggi)
        #self.egiorno.setMaximumSize(70,24)
        mapbtn.clicked.connect(self.showMap)
        #self.mylat.setMaximumWidth(80)
        #self.mylon.setMaximumWidth(80)
        self.mylat.setText('45.641174')
        self.mylon.setText('9.114828')
        lblmap = QLabel("Tipo Map")
        self.combomap = QComboBox(self)
        self.combomap.addItem("OpenStreetMap")
        self.combomap.addItem('Stamen Terrain')
        self.combomap.addItem("Stamen Toner")
        self.combomap.addItem("CartoDB positron")
        self.combomap.addItem("CartoDB dark_matter")
        hhome = QHBoxLayout()
        hhome.addWidget(mylatlbl)
        hhome.addWidget(self.mylat)
        hhome.addWidget(mylonlbl)
        hhome.addWidget(self.mylon)
        hhome.addWidget(mapbtn)
        hhome.addWidget(self.radiob)
        hhome.addWidget(self.combobox)
        hhome.addWidget(fra)
        hhome.addWidget(self.fragiorno)
        hhome.addWidget(et)
        hhome.addWidget(self.egiorno)
        hhome.addWidget(lblmap)
        hhome.addWidget(self.combomap)
        hhome.addWidget(voidlbl)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(self.title)
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.inText = QLineEdit()
        self.inText.setMaximumWidth(250)
        self.inText.setText("cq de I1LOZ")
        label2 = QLabel("Dati inviati: ")
        label2.setMaximumWidth(70)
        self.rbtn1 = QCheckBox('Solo ricezione') 
        self.rbtn2 = QCheckBox('Genera csv file')
        self.rbtn1.setMaximumWidth(150)
        self.rbtn2.setMinimumWidth(600)
        startb = QPushButton("START",self)
        startb.clicked.connect(self.start_click)
        hbox = QHBoxLayout()
        hbox.addWidget(startb)
        hbox.addWidget(label2)
        hbox.addWidget(self.inText) 
        hbox.addWidget(self.rbtn1)
        hbox.addWidget(self.rbtn2)
        # Add tabs
        self.tabs.addTab(self.tab1,"Messaggi")
        self.tabs.addTab(self.tab2,"Connessi")
        self.tabs.addTab(self.tab3,"GeoMap")
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.labels))
        self.table.setHorizontalHeaderLabels(self.labels)
        self.tab1.layout = QVBoxLayout()
        self.tab1.layout.addWidget(self.table)
        self.tab1.setLayout(self.tab1.layout)

        self.table1 = QTableWidget()
        self.table1.setColumnCount(len(self.labels1))
        self.table1.setHorizontalHeaderLabels(self.labels1)
        self.tab2.layout = QVBoxLayout()
        self.tab2.layout.addWidget(self.table1)
        self.tab2.setLayout(self.tab2.layout)
        label = QLabel("Log dati ricevuti")
        self.log = QTextEdit()
        self.log.setMaximumHeight(180)
        self.rbtn2.clicked.connect(self.handleFile)
        self.layout.addLayout(hhome)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(label)
        self.layout.addWidget(self.log)
        self.layout.addLayout(hbox)
        self.setGeometry(100, 50, 1200,640)
        self.show()


    def showMap(self):
        homeLoc['lat'] = float(self.mylat.text())
        homeLoc['lon'] = float(self.mylon.text())
        # tiles = 'OpenStreetMap'
        # tiles = 'Stamen Terrain'
        # tiles = 'Stamen Toner'
        # tiles = 'CartoDB dark_matter'
        # tiles = "CartoDB positron"
        self.map1 = folium.Map(
            location=[homeLoc['lat'],homeLoc['lon']], tiles=self.combomap.currentText(), \
                zoom_start=13
        )
        folium.Marker([homeLoc['lat'],homeLoc['lon']],
            #Make color/style changes here
            icon = folium.Icon(color='blue'),
            popup = 'Home node',
          ).add_to(self.map1)
        if(self.radiob.isChecked()):
            #read connessioni in meshDB and mark all record = combobox selected
            qr = "select user,lat,lon,dist,ora,snr from connessioni where data = '"+self.combobox.currentText()+ \
                "' and dist is not null"
            conn = dba.connect('meshDB.db')
            cur = conn.cursor()
            rows = cur.execute(qr)
            datas = rows.fetchall()
            prevd = 0
            for row in datas:
                user = row[0]
                lat = row[1]
                lon = row[2]
                dist = row[3]
                ora = row[4]
                snr = row[5]
                dist = round(dist)
                dist = dist/1000
                if(abs(dist-prevd)>0.01):
                    prevd = dist
                    folium.Marker([lat,lon],
                        icon = folium.Icon(color='red'),
                        popup = user+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                            ora+'<br>snr: '+str(snr)+'<br>Km: '+str(dist),
                    ).add_to(self.map1)
                    folium.Marker([lat,lon],
                        icon=folium.DivIcon(html=f"""<div style='font-size: 22px; font-weight: bold;'>{user}</div>""")
                    ).add_to(self.map1)
                    print("Mark added")
            cur.close()
            conn.close()
        else:
            #add a marker for each node in nodeInfo
            for node in nodeInfo:
                if('lat' in node):
                    dist = haversine([homeLoc['lat'],homeLoc['lon']],[node['lat'],node['lon']])
                    dist = round(dist)
                    dist = dist/1000
                    ora = node['time'].split(' ')[1]
                    if(dist > 0.01):
                        folium.Marker([node['lat'],node['lon']],
                            icon = folium.Icon(color='red'),
                            popup = node['user']+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                                ora+'<br>snr: '+str(node['snr'])+'<br>Km: '+str(dist),
                        ).add_to(self.map1)
                        folium.Marker([node['lat'],node['lon']],
                        icon=folium.DivIcon(html=f"""<div style='font-size: 22px; font-weight: bold;'>{node['user']}</div>""")
                    ).add_to(self.map1)
        data = io.BytesIO()
        self.map1.save(data, close_file=False)
        self.map1 = QtWebEngineWidgets.QWebEngineView()
        self.map1.setHtml(data.getvalue().decode())
        self.tabs.removeTab(2)
        self.tab3.destroy()
        self.tab3 = QWidget()
        self.tabs.addTab(self.tab3,"GeoMap")
        self.tab3.layout = QVBoxLayout()
        self.tab3.layout.addWidget(self.map1)
        self.tab3.setLayout(self.tab3.layout)
        self.map1.show()


    def start_click(self):
        global RUNNING,interface
        if(RUNNING==True):
            return
        interface = meshtastic.SerialInterface()
        RUNNING = True


    def handleFile(self):
        if(self.rbtn2.isChecked()):
            if(self.csvFile.closed):
                self.csvFile = open('meshtastic_data.csv','wt')
            l = 0
            while(l < len(self.labels)-1):
                self.csvFile.write(self.labels[l]+';')
                l += 1
            self.csvFile.write(self.labels[l]+'\n')
        else:
            self.csvFile.close()


class RepeatedTimer(object): # Timer helper class
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False


#riempi table1 con valori in nodeInfo
def showInfo():
    r = 0
    ex.table1.setRowCount(r)
    for info in nodeInfo:
        ex.table1.setRowCount(r+1)
        item0 = QTableWidgetItem()
        item0.setText(info['time'])
        ex.table1.setItem(r,0,item0)
        item1 = QTableWidgetItem()
        item1.setText(info['user'])
        ex.table1.setItem(r,1,item1)
        item2 = QTableWidgetItem()
        if('alt' in info):
            item2.setText(str(info['alt']))
            ex.table1.setItem(r,2,item2)
        if('lat' in info):
            item3 = QTableWidgetItem()
            item3.setText(str(info['lat'])[0:8])
            ex.table1.setItem(r,3,item3)
        if('lon' in info):
            item4 = QTableWidgetItem()
            item4.setText(str(info['lon'])[0:8])
            ex.table1.setItem(r,4,item4)
        if('batteryLevel' in info):
            item5 = QTableWidgetItem()
            item5.setText(str(info['batteryLevel']))
            ex.table1.setItem(r,5,item5)
        if('snr' in info):
            item6 = QTableWidgetItem()
            item6.setText(str(info['snr']))
            ex.table1.setItem(r,6,item6)
        if('distance' in info):
            item7 = QTableWidgetItem()
            item7.setText(str(round(info['distance'])))
            ex.table1.setItem(r,7,item7)
        if('rilevamento' in info):
            item8 = QTableWidgetItem()
            item8.setText(str(round(info['rilevamento']*10)/10))
            ex.table1.setItem(r,8,item8)
        r += 1


def insertDB(query):
    global conn,cur
    conn = dba.connect('meshDB.db')
    cur = conn.cursor()
    try:
        cur.execute(query)
        conn.commit()
        print("Insert OK")
    except dba.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
    cur.close()
    conn.close()
    


#inserisci nuovo user in dictionary
def insertUser(user,id):
    n = len(nodeInfo)
    i = 0
    while(i<n):
        if (id == nodeInfo[i]['id']):
            break
        else:
            i += 1
    if(i==n):   #id non esiste, aggiungi nuovo user e id
        newuser = {}
        newuser['user']=user
        newuser['id'] = id
        newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
        newuser['ts'] = datetime.datetime.now().timestamp()
        #Insert newuser in DB
        qr = "insert into connessioni (data,ora,user) values('"+datetime.datetime.now().strftime('%y/%m/%d')+ \
            "','"+datetime.datetime.now().strftime('%T')+"','"+user+"')"
        insertDB(qr)
        newuser['_id'] = max_IdDB()
        nodeInfo.append(newuser)
        print(nodeInfo)
    else:
        print("chiudo vecchio e apro nuovo")
        # se now() - nodeInfo[i]['time'] > 2 secondi fai showInfo() per riempire Tab1
        # e inserire record in DB e poi aggiornalo creando newuser in posizione [i] 
        now = datetime.datetime.now().timestamp()
        prima = nodeInfo[i]['ts']
        if((now-prima)>60):
            showInfo()     # insert data in Table1 and set marker on geomap
            newuser = {}
            newuser['user']=user
            newuser['id'] = id
            newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
            newuser['ts'] = now
            #Insert newuser in DB
            qr = "insert into connessioni (data,ora,user) values('"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                "','"+datetime.datetime.now().strftime('%T')+"','"+user+"')"
            insertDB(qr)
            newuser['_id'] = max_IdDB()
            nodeInfo[i] = newuser
            print(nodeInfo)


def max_IdDB():
    qr = "select max(_id) from connessioni"
    global conn,cur
    conn = dba.connect('meshDB.db')
    cur = conn.cursor()
    rows = cur.execute(qr)
    datas = rows.fetchall()
    print(datas)
    nr = datas[0][0]
    cur.close()
    conn.close()
    return nr


def updateUser(id,coord,altitude,distance,rilev,batt):
    #trova id in nodeInfo
    i = 0
    for info in nodeInfo:
        if(info['id'] == id):
            lat, lon = coord
            nodeInfo[i].update({'lat': lat})
            nodeInfo[i].update({'lon': lon})
            nodeInfo[i].update({'alt': altitude})
            nodeInfo[i].update({'distance': distance})
            nodeInfo[i].update({'rilevamento': rilev})
            nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
            if('batteryLevel' in nodeInfo[i]):
                if(batt != 'N/A'):
                    nodeInfo[i].update({'batteryLevel': batt})
            else:
                nodeInfo[i].update({'batteryLevel': batt})
            qr = "update connessioni set lat="+str(nodeInfo[i]['lat'])+",lon="+str(nodeInfo[i]['lon'])+ \
                ",alt="+str(nodeInfo[i]['alt'])+",dist="+str(nodeInfo[i]['distance'])+",rilev="+ \
                str(nodeInfo[i]['rilevamento'])+",batt='"+batt+"',data='"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                "',ora='"+datetime.datetime.now().strftime('%T')+"' where _id ="+str(nodeInfo[i]['_id'])
            insertDB(qr)
            break
        i += 1
    print(nodeInfo)


def updateSnr(id,snr):
    #trova id in nodeInfo
    i = 0
    for info in nodeInfo:
        if(info['id'] == id):
            nodeInfo[i].update({'snr': snr})
            nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
            qr = "update connessioni set snr="+str(nodeInfo[i]['snr'])+" where _id="+str(nodeInfo[i]['_id'])
            insertDB(qr)
            break
        i += 1
    print(nodeInfo)


def onReceive(packet, interface): # called when a packet arrives
    print(f"Received: {packet}")
    row = [';',';',';',';', \
           ';',';',';',';', \
           ';',';',';',';',';',' \n']
    dataora = datetime.datetime.now().strftime("%d/%m/%y %T")
    row[0] = dataora+';'
    ex.log.append(dataora+" "+f"{packet}")
    item = QTableWidgetItem()
    item.setText(dataora)
    global count
    r = count
    ex.table.setRowCount(count+1)
    ex.table.setItem(r,0,item)
    print(dataora)
    print(count)
    from_ = packet['from']
    to_ = packet['to']
    item1 = QTableWidgetItem()
    item2 = QTableWidgetItem()
    item1.setText(str(from_))
    row[1] = str(from_)+';'
    item2.setText(str(to_))
    row[2] = str(to_)+';'
    ex.table.setItem(r,1,item1)
    ex.table.setItem(r,2,item2)
    item6 = QTableWidgetItem()
    row[6] = packet['fromId']+';'
    item6.setText(packet['fromId'])
    ex.table.setItem(r,6,item6)
    item7 = QTableWidgetItem()
    row[7] = packet['toId']+';'
    item7.setText(packet['toId'])
    ex.table.setItem(r,7,item7)
    if ('decoded' in packet):
        tipmsg = packet['decoded']['portnum']
        row[3] = packet['decoded']['portnum']+';'
        item3 = QTableWidgetItem()
        item3.setText(tipmsg)
        ex.table.setItem(r,3,item3)
        item4 = QTableWidgetItem()
        item4.setText(str(packet['decoded']['payload']))
        row[4] = str(packet['decoded']['payload'])+';'
        ex.table.setItem(r,4,item4)
        if (packet['decoded']['portnum'] == 'NODEINFO_APP'):
            item5 = QTableWidgetItem()
            item5.setText(packet['decoded']['user']['longName'])
            row[5] = packet['decoded']['user']['longName']+';'
            ex.table.setItem(r,5,item5)
            insertUser(packet['decoded']['user']['longName'],packet['fromId'])
            showInfo()
        if (packet['decoded']['portnum'] == 'POSITION_APP'):
            if('altitude' in packet['decoded']['position']):
                item8 = QTableWidgetItem()
                item8.setText(str(packet['decoded']['position']['altitude']))
                row[8] = str(packet['decoded']['position']['altitude'])+';'
                ex.table.setItem(r,8,item8)
            if('latitude' in packet['decoded']['position']):   
                item9 = QTableWidgetItem()
                item9.setText(str(packet['decoded']['position']['latitude'])[0:8])
                row[9] = str(packet['decoded']['position']['latitude'])[0:8]+';'
                ex.table.setItem(r,9,item9)
            if('longitude' in packet['decoded']['position']):
                item10 = QTableWidgetItem()
                item10.setText(str(packet['decoded']['position']['longitude'])[0:8])
                row[10] = str(packet['decoded']['position']['longitude'])[0:8]+';'
                ex.table.setItem(r,10,item10)
                #calcola e inserisci distanza
                coord1 = [float(ex.mylat.text()),float(ex.mylon.text())]
                coord2 = [packet['decoded']['position']['latitude'],packet['decoded']['position']['longitude']]
                distance = haversine(coord1,coord2)
                row[12] = str(round(distance))+';'
                print(distance)
                #calcola e inserisci rilevamento
                rilev = calcBearing(coord1,coord2)
                item12 = QTableWidgetItem()
                item12.setText(str(int(distance)))
                item13 = QTableWidgetItem()
                item13.setText(str(round(rilev*10)/10))
                ex.table.setItem(r,12,item12)
                ex.table.setItem(r,13,item13)
                row[13] = str(round(rilev*10)/10)+'\n'
                print(rilev)
                # aggiorna nodeInfo
                batt = 'N/A'
                if('batteryLevel' in packet['decoded']['position']):
                    batt = str(packet['decoded']['position']['batteryLevel'])
                if('altitude' in packet['decoded']['position']):
                    updateUser(packet['fromId'],coord2,packet['decoded']['position']['altitude'],distance,rilev,batt)
                else:
                    updateUser(packet['fromId'],coord2,'0',distance,rilev,batt)
                showInfo()
            if('rxSnr' in packet):
                item11 = QTableWidgetItem()
                item11.setText(str(packet['rxSnr']))
                row[11] = str(packet['rxSnr'])+';'
                ex.table.setItem(r,11,item11)
                updateSnr(packet['fromId'],str(packet['rxSnr']))
                showInfo()

    if(ex.rbtn2.isChecked()):
        i = 0
        while(i < len(row)):
            ex.csvFile.write(row[i])
            i += 1
    count = count+1

def onConnection(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
    print ("starting...")
    interface.sendText("Hello mesh")
    ex.log.append("Starting...")
    rt = RepeatedTimer(120, sendText) # no need of rt.start()


def sendText(): # called every x seconds
    if(ex.rbtn1.isChecked()==False):
        currTime = datetime.datetime.now().strftime("%H:%M:%S")
        global msgcount
        msg = str(msgcount)+" "+currTime+" "+ex.inText.text()
        interface.sendText(msg)
        msgcount += 1
        ex.log.append("Sending "+" "+msg)
        print("Message sent: " + msg)


#Horisontal Bearing
def calcBearing(coord1, coord2):
    lat1,lon1 = coord1
    lat2,lon2 = coord2
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) \
        - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    return bearing

def haversine(coord1, coord2):
    R = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))
 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")
    conn = dba.connect('meshDB.db')
    cur = conn.cursor()
    #riempi combobox con loista dei giorni presenti in db
    qr = "select DISTINCT data from connessioni where data > '"+ex.fragiorno.text()+ \
        "' and data <= '"+ex.egiorno.text()+"' order by data ASC"
    rows = cur.execute(qr)
    datas = rows.fetchall()
    for giorno in datas:
        ex.combobox.addItem(giorno[0])
    cur.close()
    conn.close()
    sys.exit(app.exec_())  
