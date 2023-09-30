import sys,math,io
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTabWidget, \
            QTableWidgetItem,QVBoxLayout,QHBoxLayout,QLineEdit,QTextEdit,QLabel,QCheckBox, \
            QPushButton,QRadioButton,QComboBox,QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor   
from PyQt5.QtGui import QIcon
import folium
from PyQt5 import QtWidgets, QtWebEngineWidgets

import sqlite3 as dba
import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import time
from time import sleep
import datetime


class Interceptor(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info):
            info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9,es;q=0.8,de;q=0.7")

class App(QWidget):
    
    RUNNING = False
    rigacsv = 0
    mynodeId = 0
    count = 0
    msgcount = 1
    homeLoc = {}
    nodeInfo = []
    callmesh = object
    calldb   = object
    dataDB   = pyqtSignal(object)


    def __init__(self):
        super().__init__()
        self.title = 'Meshtastic data show'
        self.interceptor = Interceptor()
        self.initUI()
        
    def initUI(self):
        self.labels = ['data ora','origine','destinazione','tipo messaggio','payload','utente', \
            'da_id','a_id','altitudine','latitudine','longitudine','rxSnr','distanza','rilevamento']
        self.labels1 = ['data ora','long name','altitudine','latitudine','longitudine','batteria%', \
            'rxsnr','distanza','rilevamento','chanUtil','airTxUtil','pressione','temperatura','umidità']
        self.csvFile = open('meshtastic_data.csv','wt')
        mylatlbl = QLabel("Home lat:")
        mylonlbl = QLabel("Home lon:")
        voidlbl = QLabel("")
        voidlbl1 = QLabel("")
        voidlbl2 = QLabel("")
        voidlbl3 = QLabel("")
        voidlbl4 = QLabel("")
        voidlbl.setMinimumWidth(22)
        voidlbl1.setMinimumWidth(22)
        voidlbl2.setMinimumWidth(22)
        voidlbl3.setMinimumWidth(22)
        voidlbl3.setMinimumWidth(22)
        self.mylat = QLineEdit()
        self.mylon = QLineEdit()
        self.mylat.setMaximumWidth(70)
        self.mylon.setMaximumWidth(70)
        mylatlbl.setMaximumWidth(60)
        mylonlbl.setMaximumWidth(60)
        mapbtn =  QPushButton("SHOW MAP",self)
        self.radiob = QRadioButton('Storico giorno:')
        self.combobox = QComboBox(self)
        self.combobox.setMinimumWidth(90)
        lblmant = QLabel("Mantieni ultimi gg in DB")
        self.numgg = QLineEdit()
        self.numgg.setText('10')
        self.numgg.setMaximumSize(24,22)
        self.egiorno = QLineEdit()
        oggi = datetime.datetime.now().strftime("%y/%m/%d")
        self.egiorno.setText(oggi)
        self.egiorno.setMaximumSize(70,24)
        mapbtn.clicked.connect(self.showMap)
        self.mylat.setMinimumWidth(70)
        self.mylon.setMinimumWidth(70)
        self.mylat.setText('45.641174')
        self.mylon.setText('9.114828')
        lblmap = QLabel("Tipo Map")
        self.combomap = QComboBox(self)
        self.combomap.addItem("OpenStreetMap")
        self.combomap.addItem('Stamen Terrain')
        self.combomap.addItem("Stamen Toner")
        self.combomap.addItem("CartoDB positron")
        self.combomap.addItem("CartoDB dark_matter")
        self.lblcbnode = QLabel("Map node:")
        self.combonode = QComboBox(self)
        self.combonode.addItem("map solo i GW")
        self.combonode.setMinimumWidth(130)
        self.combonode.setMaximumWidth(140)
        hhome = QHBoxLayout()
        hhome.addWidget(mylatlbl)
        hhome.addWidget(self.mylat)
        hhome.addWidget(mylonlbl)
        hhome.addWidget(self.mylon)
        hhome.addWidget(mapbtn)
        hhome.addWidget(self.radiob)
        hhome.addWidget(self.combobox)
        hhome.addWidget(lblmant)
        hhome.addWidget(self.numgg)
        hhome.addWidget(lblmap)
        hhome.addWidget(self.combomap)
        hhome.addWidget(self.lblcbnode)
        hhome.addWidget(self.combonode)
        hhome.addWidget(voidlbl)
        hhome.addWidget(voidlbl1)
        hhome.addWidget(voidlbl2)
        hhome.addWidget(voidlbl3)
        hhome.addWidget(voidlbl4)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(self.title)
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.inText = QLineEdit()
        self.inText.setMaximumWidth(250)
        self.inText.setText("Test mesh da IU2RPO_GW_868")
        label2 = QLabel("Dati inviati: ")
        label2.setMaximumWidth(70)
        self.rbtn1 = QCheckBox('Solo ricezione') 
        self.rbtn3 = QCheckBox('Mess. immediato')
        self.rbtn2 = QCheckBox('Genera csv file')
        self.rbtn4 = QCheckBox('Autorisposta')
        self.qsl = QLineEdit()
        self.qsl.setText('RX qsl de IU2RPO_GW_868 a: ')
        self.rbtn1.setMaximumWidth(95)
        self.rbtn2.setMinimumWidth(95)
        startb = QPushButton("START",self)
        startb.clicked.connect(self.start_click)
        self.chusage = QProgressBar(self)
        self.airustx = QProgressBar(self)
        self.chusage.setProperty("value", 0.5)
        self.airustx.setProperty("value", 0.5)
        self.lblchus = QLabel("ChUtil")
        self.lblairu = QLabel("AirUtilTX*10")
        self.lblmsgat = QLabel("Ore 00:00")
        
        hbox = QHBoxLayout()
        hbox.addWidget(startb)
        hbox.addWidget(label2)
        hbox.addWidget(self.inText) 
        hbox.addWidget(self.rbtn1)
        hbox.addWidget(self.rbtn3)
        hbox.addWidget(self.rbtn4)
        hbox.addWidget(self.qsl)
        hbox.addWidget(self.rbtn2)
        hbox.addWidget(self.lblmsgat)
        hbox.addWidget(self.lblchus)
        hbox.addWidget(self.chusage)
        hbox.addWidget(self.lblairu)
        hbox.addWidget(self.airustx)
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
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        self.label1 = QLabel("Log protocollo")
        self.label2 = QLabel("Texts ricevuti/trasmessi")
        self.log = QTextEdit()
        self.ricevuti= QTextEdit()
        hbox1.addWidget(self.label1)
        hbox1.addWidget(self.label2)
        self.log.setFontFamily('Courier New')
        hbox2.addWidget(self.log)
        hbox2.addWidget(self.ricevuti)
        self.log.setReadOnly(True)
        self.ricevuti.setReadOnly(True)
        self.rbtn2.clicked.connect(self.handleFile)
        self.log.setMaximumHeight(180)
        self.ricevuti.setMaximumHeight(180)
        self.layout.addLayout(hhome)
        self.layout.addWidget(self.tabs)
        self.layout.addLayout(hbox1)
        self.layout.addLayout(hbox2)
        self.layout.addLayout(hbox)
        self.setGeometry(100, 50, 1024,640)
        self.show()

    def closeEvent(self, event):
        self.removeOld()
        #salva mylat e mylon in meshnodes
        mylat = self.mylat.text()
        mylon = self.mylon.text()
        qr = "update meshnodes set lat ='"+mylat+"',lon='"+mylon+"' where longname='mioGW'"
        print("Salvo mylat e mylon in DB: "+mylat+' '+mylon)
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        cur.execute(qr)
        conn.commit()
        cur.close()
        conn.close()
        print("Coordinate gps salvate..")

    def showMap(self):
        self.homeLoc['lat'] = float(self.mylat.text())
        self.homeLoc['lon'] = float(self.mylon.text())
        # tiles = 'OpenStreetMap'
        # tiles = 'Stamen Terrain'
        # tiles = 'Stamen Toner'
        # tiles = 'CartoDB dark_matter'
        # tiles = "CartoDB positron"
        self.map1 = folium.Map(
            location=[self.homeLoc['lat'],self.homeLoc['lon']], tiles=self.combomap.currentText(), \
                zoom_start=13
        )
        folium.Marker([self.homeLoc['lat'],self.homeLoc['lon']],
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
                dist = dist/1000.0
                dist = round(dist,1)
                if('GW' in user): #se variazione > 100mt marca pos
                    folium.Marker([lat,lon],
                        icon = folium.Icon(color='red'),
                        popup = user+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                            ora+'<br>snr: '+str(snr)+'<br>Km: '+str(dist),
                    ).add_to(self.map1)
                    folium.Marker([lat,lon],
                        icon=folium.DivIcon(html=f"""<div style='font-size: 12px; font-weight: normal;'>{user}</div>""")
                    ).add_to(self.map1)
                    print("Mark added")
                elif(abs(dist-prevd)>0.1 and self.combonode.currentText() == user):
                    prevd = dist
                    folium.Marker([lat,lon],
                        icon = folium.Icon(color='green'),
                        popup = user+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                            ora+'<br>snr: '+str(snr)+'<br>Km: '+str(dist),
                    ).add_to(self.map1)
                    folium.Marker([lat,lon],
                        icon=folium.DivIcon(html=f"""<div style='font-size: 12px; font-weight: normal;'>{user}</div>""")
                    ).add_to(self.map1)
                    print("Mark added")
                     
            cur.close()
            conn.close()
        else:
            #add a marker for each node GW in nodeInfo
            for node in self.nodeInfo:
                if(node['user'] == None):
                    continue
                if('lat' in node and 'GW' in node['user']):
                    dist = self.haversine([self.homeLoc['lat'],self.homeLoc['lon']],[node['lat'],node['lon']])
                    dist = dist/1000.0
                    dist = round(dist,1)
                    ora = node['time'].split(' ')[1]
                    segndist = "None"
                    if ('snr' in node):
                        segndist = str(node['snr'])  
                    if(dist > 0.01):
                        folium.Marker([node['lat'],node['lon']],
                            icon = folium.Icon(color='red'),
                            popup = node['user']+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                                ora+'<br>snr: '+segndist+'<br>Km: '+str(dist),
                        ).add_to(self.map1)
                        folium.Marker([node['lat'],node['lon']],
                        icon=folium.DivIcon(html=f"""<div style='font-size: 12px; font-weight: normal;'>{node['user']}</div>""")
                    ).add_to(self.map1)
                elif('lat' in node and not self.combonode.currentText() == 'map solo i GW'):
                    if(node['user'] == None):
                            continue   
                    if('lat' in node and self.combonode.currentText() == node['user']):
                        dist = self.haversine([self.homeLoc['lat'],self.homeLoc['lon']],[node['lat'],node['lon']])
                        dist = dist/1000.0
                        dist = round(dist,1)
                        ora = node['time'].split(' ')[1]
                        segndist = "None"
                        if ('snr' in node):
                            segndist = str(node['snr'])  
                            if(dist > 0.01):
                                folium.Marker([node['lat'],node['lon']],
                                    icon = folium.Icon(color='green'),
                                    popup = node['user']+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp&nbsp;<br>ora: '+ \
                                    ora+'<br>snr: '+segndist+'<br>Km: '+str(dist),
                                ).add_to(self.map1)
                            folium.Marker([node['lat'],node['lon']],
                            icon=folium.DivIcon(html=f"""<div style='font-size: 12px; font-weight: normal;'>{node['user']}</div>""")
                            ).add_to(self.map1)    

        data = io.BytesIO()
        self.map1.save(data, close_file=False)
        self.map1 = QtWebEngineWidgets.QWebEngineView()
        self.map1.setHtml(data.getvalue().decode())
        self.map1.page().profile().setUrlRequestInterceptor(self.interceptor)
        self.tabs.removeTab(2)
        self.tab3.destroy()
        self.tab3 = QWidget()
        self.tabs.addTab(self.tab3,"GeoMap")
        self.tab3.layout = QVBoxLayout()
        self.tab3.layout.addWidget(self.map1)
        self.tab3.setLayout(self.tab3.layout)
        self.map1.show()

    def start_click(self):
        if(self.RUNNING ==True): 
            if(self.rbtn1.isChecked()==False):
                self.callmesh.setSendTx(True)  # non invia messaggi periodici
            else:
                self.callmesh.setSendTx(False)
            
            if(self.rbtn3.isChecked()==True):
                msg = self.inText.text()
                self.callmesh.sendImmediate(msg)
            return
        self.callmesh = meshInterface()
        self.calldb = callDB()
        self.calldb.start()
        if(self.rbtn1.isChecked()==False):
            self.callmesh.setSendTx(True)  # non invia messaggi periodici
        else:
            self.callmesh.setSendTx(False) # non invia messaggi periodice
        self.callmesh.actionDone.connect(self.onPacketRcv)
        self.callmesh.start()
        self.RUNNING = True

    def loadHist(self):
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        # aggiorna mylat e mylon 
        qr = "select lat,lon from meshnodes where longname='mioGW'"
        rows = cur.execute(qr)
        datas = rows.fetchall()
        try:
            print(datas[0][0])
            print(datas[0][1])
            self.mylat.setText(str(datas[0][0]))
            self.mylon.setText(str(datas[0][1]))
        except:
            self.mylat.setText('45.6412')
            self.mylon.setText('9.1149')
        #riempi combobox con lista dei giorni presenti in db
        qr = "select DISTINCT data from connessioni order by data ASC"
        rows = cur.execute(qr)
        datas = rows.fetchall()
        for giorno in datas:
            self.combobox.addItem(giorno[0])
        qr = "select * from meshnodes order by longname"
        rows = cur.execute(qr)
        datas = rows.fetchall()
        for record in datas:
            #print(record[3])
            if(record[3]== None):
                continue
            if('GW' not in record[3]):
                self.combonode.addItem(record[3])    
        cur.close()
        conn.close()  

    def removeOld(self):
        #trova data minore di 7gg rispetto oggi
        try:
            ng = int(self.numgg.text())
        except:
            ng = 10
        prv = datetime.datetime.now().timestamp()-86400*ng
        prvdate = datetime.date.fromtimestamp(prv).strftime("%y/%m/%d")
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        #cancella record piu vecchi di 7gg
        qr = "delete from meshnodes where data < '"+prvdate+"'"
        cur.execute(qr)
        conn.commit()
        qr = "delete from airtx where data < '"+prvdate+"'"
        cur.execute(qr)
        conn.commit()
        qr = "delete from connessioni where data < '"+prvdate+"'"
        cur.execute(qr)
        conn.commit()
        qr = "delete from origmsg where data < '"+prvdate+"'"
        cur.execute(qr)
        conn.commit()
        cur.close()
        conn.close()  
        print("Rimossi record vecchi piu di "+str(ng)+" giorni.")

    def loadPeers(self):
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        qr = "update meshnodes set longname='ignoto' where longname is null"
        cur.execute(qr)
        conn.commit()
        qr = "select * from meshnodes order by longname"
        rows = cur.execute(qr)
        datas = rows.fetchall()
        for row in datas:
            info = {}
            dataora = row[0]+' '+row[1]
            info['time'] = dataora
            info['nodenum'] = row[2]
            info['user'] = row[3]
            if((row[4] == None) == False):
                info['alt'] = row[4]
            if((row[5] == None) == False):
                info['lat'] = row[5]
            if((row[6] == None) == False):
                info['lon'] = row[6]
            if((row[7] == None) == False):
                info['battlv'] = row[7]
            if((row[8] == None) == False):
                info['snr'] = row[8]
            if((row[9] == None) == False):
                info['distance'] = row[9]
            if((row[10] == None) == False):
                info['rilevamento'] = row[10]
            if((row[11] == None) == False):
                info['chutil'] = row[11]
            if((row[12] == None) == False):
                info['airutil'] = row[12]
            if((row[13] == None) == False):
                info['pressione'] = row[13]
            if((row[14] == None) == False):
                info['temperatura'] = row[14]
            if((row[15] == None) == False):
                info['humidity'] = row[15]
            self.nodeInfo.append(info)
        cur.close()
        conn.close()  
        #self.showInfo()

    def chusageGreen(self):
        self.chusage.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: lightgreen;"
                      "}")
    def chusageYellow(self):
        self.chusage.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: yellow;"
                      "}")   
    def chusageRed(self):
        self.chusage.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: red;"
                      "}")

    def airustxGreen(self):
        self.airustx.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: lightgreen;"
                      "}")

    def airustxYellow(self):
        self.airustx.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: yellow;"
                      "}")
    def airustxRed(self):
        self.airustx.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: red;"
                      "}")


    def onPacketRcv(self,packet):
        print(packet)
        row = ['-;','-;','-;','-;', \
            '-;','-;','-;','-;', \
            '-;','-;','-;','-;','-;',' \n']
        dataora = datetime.datetime.now().strftime("%d/%m/%y %T")
        row[0] = dataora+';'
        item = QTableWidgetItem()
        item.setText(dataora)
        r = self.count
        self.table.setRowCount(self.count+1)
        self.table.setItem(r,0,item)
        print(dataora)
        print(self.count)
        from_ = packet['from']
        to_ = packet['to']
        item1 = QTableWidgetItem()
        item2 = QTableWidgetItem()
        item1.setText(str(from_))
        row[1] = str(from_)+';'
        item2.setText(str(to_))
        row[2] = str(to_)+';'
        self.table.setItem(r,1,item1)
        self.table.setItem(r,2,item2)
        item6 = QTableWidgetItem()
        if (isinstance(packet['fromId'],str)):
            row[6] = packet['fromId']+';'
            item6.setText(packet['fromId'])
            dachi = packet['fromId']
        else:
            row[6] = 'None;'
            item6.setText('None')
            dachi = 'None'
        self.table.setItem(r,6,item6)
        item7 = QTableWidgetItem()
        if (isinstance(packet['toId'],str)):
            achi = packet['toId']
            row[7] = packet['toId']+';'
            item7.setText(packet['toId'])
        else:
            row[7] = 'None;'
            item7.setText('None')
            achi = 'None'

        self.table.setItem(r,7,item7)
        if ('decoded' in packet):
            tipmsg = packet['decoded']['portnum']
            row[3] = packet['decoded']['portnum']+';'
            item3 = QTableWidgetItem()
            item3.setText(tipmsg)
            self.table.setItem(r,3,item3)
            item4 = QTableWidgetItem()
            item4.setText(str(packet['decoded']['payload']))
            row[4] = str(packet['decoded']['payload'])+';'
            self.table.setItem(r,4,item4)
            if (packet['decoded']['portnum'] == 'NODEINFO_APP'):
                tipmsg = 'NODEINFO_APP'
                item5 = QTableWidgetItem()
                item5.setText(packet['decoded']['user']['longName'])
                row[5] = packet['decoded']['user']['longName']+';'
                self.table.setItem(r,5,item5)
                self.insertUser(from_,packet['decoded']['user']['longName'],packet['fromId'])
                pdict = {}
                nome = packet['decoded']['user']['longName']
                pdict.update({'longname': nome})
                pdict.update({'chiave': from_})
                self.calldb.InsUpdtDB(pdict)
                self.showInfo()
            
            elif (packet['decoded']['portnum'] == 'ADMIN_APP'):
                tipmsg =  'ADMIN_APP'
                if(from_ == to_):
                    self.mynodeId = from_
                    pdict = {}
                    pdict.update({'chiave': from_})
                    pdict.update({'longname': 'mioGW'})
                    # cancella mioGW preesistente e sostotuiscilo con quello attuale
                    self.delmioGW()
                    self.calldb.InsUpdtDB(pdict)

            elif (packet['decoded']['portnum'] == 'POSITION_APP'):
                tipmsg = 'POSITION_APP'
                if('altitude' in packet['decoded']['position']):
                    item8 = QTableWidgetItem()
                    item8.setText(str(packet['decoded']['position']['altitude']))
                    row[8] = str(packet['decoded']['position']['altitude'])+';'
                    self.table.setItem(r,8,item8)
                if('latitude' in packet['decoded']['position']):   
                    item9 = QTableWidgetItem()
                    item9.setText(str(packet['decoded']['position']['latitude'])[0:8])
                    row[9] = str(packet['decoded']['position']['latitude'])[0:8]+';'
                    self.table.setItem(r,9,item9)
                if('longitude' in packet['decoded']['position']):
                    item10 = QTableWidgetItem()
                    item10.setText(str(packet['decoded']['position']['longitude'])[0:8])
                    row[10] = str(packet['decoded']['position']['longitude'])[0:8]+';'
                    self.table.setItem(r,10,item10)
                    #calcola e inserisci distanza
                    coord1 = [float(self.mylat.text()),float(self.mylon.text())]
                    if('longitude' in  packet['decoded']['position'] and 'latitude' in  packet['decoded']['position']):
                        coord2 = [packet['decoded']['position']['latitude'],packet['decoded']['position']['longitude']]
                        distance = self.haversine(coord1,coord2)
                        row[12] = str(round(distance,2)/1000.0)+';'
                        print(distance)
                        #calcola e inserisci rilevamento
                        rilev = self.calcBearing(coord1,coord2)
                        item12 = QTableWidgetItem()
                        item12.setText(str(round(distance,2)/1000.0))
                        item13 = QTableWidgetItem()
                        item13.setText(str(round(rilev*10)/10))
                        self.table.setItem(r,12,item12)
                        self.table.setItem(r,13,item13)
                        row[13] = str(round(rilev*10)/10)+'\n'
                        print(rilev)
                        # aggiorna nodeInfo
                        pdict = {}
                        pdict.update({'dist': distance})
                        pdict.update({'rilev': rilev})
                        pdict.update({'lat': coord2[0]})
                        pdict.update({'lon': coord2[1]})
                        if('altitude' in packet['decoded']['position']):
                            self.updateUser(from_,coord2,packet['decoded']['position']['altitude'],distance,rilev)
                            pdict.update({'alt': packet['decoded']['position']['altitude']})
                            pdict.update({'chiave': from_})
                            self.calldb.InsUpdtDB(pdict)
                        else:
                            self.updateUser(from_,coord2,'0',distance,rilev)
                            pdict.update({'alt': 0})
                            pdict.update({'chiave': from_})
                            self.calldb.InsUpdtDB(pdict)
                    self.showInfo()
                    
                if('rxSnr' in packet):
                    item11 = QTableWidgetItem()
                    item11.setText(str(packet['rxSnr']))
                    row[11] = str(packet['rxSnr'])+';'
                    self.table.setItem(r,11,item11)
                    self.updateSnr(from_,str(packet['rxSnr']))
                    pdict = {}
                    pdict.update({'snr': packet['rxSnr']})
                    pdict.update({'chiave': from_})
                    self.calldb.InsUpdtDB(pdict)
                    self.showInfo() 
                
            elif (packet['decoded']['portnum'] == 'TELEMETRY_APP'):
                    tipmsg = 'TELEMETRY_APP'
                    if('deviceMetrics' in packet['decoded']['telemetry']):
                        battlvl = ' '
                        chanutil = 0
                        airutil = 0
                        if('batteryLevel' in packet['decoded']['telemetry']['deviceMetrics']):
                            battlvl   = packet['decoded']['telemetry']['deviceMetrics']['batteryLevel']
                        if('channelUtilization' in packet['decoded']['telemetry']['deviceMetrics']):
                            chanutil  = packet['decoded']['telemetry']['deviceMetrics']['channelUtilization']
                        if('airUtilTx' in packet['decoded']['telemetry']['deviceMetrics']):
                            airutil   = packet['decoded']['telemetry']['deviceMetrics']['airUtilTx'] 
                        if(packet['from'] == self.mynodeId):
                            if(chanutil > 0):
                                self.chusage.setProperty("value",chanutil)
                                if(chanutil < 50):
                                    self.chusageGreen()
                                elif(chanutil < 76):
                                    self.chusageYellow()
                                else:
                                    self.chusageRed()

                            if(airutil > 10):
                                airutil = 10 
                            if(airutil > 0):
                                self.airustx.setProperty("value",airutil*10)
                                if(airutil < 5.1):
                                    self.airustxGreen()
                                elif(airutil < 10):
                                    self.airustxYellow()
                                else:
                                    self.airustxRed()

                            ora = "Ore "+datetime.datetime.now().strftime("%T")
                            self.lblmsgat.setText(ora)
                        else:
                            try:
                                self.updateTelemetry(packet['from'],battlvl,chanutil,airutil) 
                                self.showInfo()
                                pdict ={}
                                pdict.update({'batt': battlvl})
                                pdict.update({'chanutil': chanutil})
                                pdict.update({'airutiltx': airutil})
                                pdict.update({'chiave': from_})
                                self.calldb.InsUpdtDB(pdict)
                            except:
                                print("Update saltata per campi nulli in Telemetry")
                            
                    if('environmentMetrics' in packet['decoded']['telemetry']):
                        temperatura = 0
                        pressione = 0
                        humidity = 0
                        voltage = 0
                        current = 0
                        if('temperature' in packet['decoded']['telemetry']['environmentMetrics']):
                            temperatura = packet['decoded']['telemetry']['environmentMetrics']['temperature']
                        if('barometricPressure' in packet['decoded']['telemetry']['environmentMetrics']):
                            pressione = packet['decoded']['telemetry']['environmentMetrics']['barometricPressure']
                        if('relativeHumidity' in packet['decoded']['telemetry']['environmentMetrics']):
                            humidity = packet['decoded']['telemetry']['environmentMetrics']['relativeHumidity']  
                        if('voltage' in packet['decoded']['telemetry']['environmentMetrics']):
                            voltage = packet['decoded']['telemetry']['environmentMetrics']['voltage']  
                        if('current' in packet['decoded']['telemetry']['environmentMetrics']):
                            current =packet['decoded']['telemetry']['environmentMetrics']['current'] 
                        self.updateSensors(packet['from'],temperatura,pressione,humidity,voltage,current)
                        self.showInfo()
                        pdict ={}
                        pdict.update({'pressione': pressione})
                        pdict.update({'temperat': temperatura})
                        pdict.update({'umidita': humidity})
                        pdict.update({'chiave': from_})
                        self.calldb.InsUpdtDB(pdict)
                        

            elif (packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP'):
                tipmsg = 'TEXT_MESSAGE_APP'
                msgda = self.findUser(from_)
                testo = datetime.datetime.now().strftime("%d/%m/%y %T") + \
                    " "+packet['decoded']['text']+" de "+msgda
                self.ricevuti.append(testo) 
                if('qsl?' in packet['decoded']['text'] and self.rbtn4.isChecked()):
                    rmsg = self.qsl.text()
                    rmsg = rmsg + packet['decoded']['text']+" da "+msgda
                    self.callmesh.sendImmediate(rmsg)
            
            if(self.rbtn2.isChecked()):
                i = 0
                while(i < len(row)):
                    try:
                        self.csvFile.write(row[i])
                    except:
                        self.csvFile.write("-;")
                        msg = "(csvFile) Errore in contenuti campo "+str(i)
                        print(msg)
                        self.log.append(msg)
                    i += 1
                self.rigacsv += 1
                record = "riga csv #"+str(self.rigacsv)+" creata"
                print(record)
                self.log.append(record)
            self.count += 1
            print("ID and FROM")
            print(packet['id'])
            msgID = packet['id']
            print(packet['from'])
            orig = packet['from']
            longname = self.findUser(orig)
            if(self.testMsgOrig(msgID,orig) == True):
                #print("POSSO INSERIRE msgID e ORIGINE")
                ora = datetime.datetime.now().strftime("%T")
                data = datetime.datetime.now().strftime("%y/%m/%d")
                qr = "insert into origmsg (data,ora,msgid,origin,longname,tipmsg) \
                    values('"+data+"','"+ora+"','"+str(msgID)+"','"+str(orig)+"','"+longname+"','"+tipmsg+"')"
                self.insertDB(qr)
            else: 
                msg = datetime.datetime.now().strftime("%d/%m/%y %T")+" "+str(msgID)+" da "+longname+" duplicato"
                self.log.append(msg)    

        else:
            tipmsg = 'NON_GESTITO'
        user = self.findUser(from_)
        if(user == None):
            user = "unknown"
        if(len(user) > 20):
            user = user[:20]
        while(len(user) < 20):
                user += ' '
        self.logpMsg(dachi,user,achi,tipmsg)

        
    def delmioGW(self):
        qr = "delete from meshnodes where longname = 'mioGW'"
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        try:
            cur.execute(qr)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(qr)
        cur.close()
        conn.close()
    
    def logpMsg(self,dachi,user,achi,tipomsg):
        ora = datetime.datetime.now().strftime("%d/%m/%y %T")
        if(isinstance(dachi,str)):
           lgm = ora+'\t'+dachi+'\t'+user+'\t'+achi+'\t'+tipomsg
        else:
           lgm = ora+'\tNone\t'+user+'\t'+achi+'\t'+tipomsg 
        self.log.append(lgm)    

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
            self.log.append("File meshtastic_data.csv pronto per uso.")

    def showInfo(self):
        r = 0
        self.table1.setRowCount(r)
        for info in self.nodeInfo:
            if('ts' in info):
                self.table1.setRowCount(r+1)
                item0 = QTableWidgetItem()
                item0.setText(info['time'])
                self.table1.setItem(r,0,item0)
                item1 = QTableWidgetItem()
                if('user' in info):
                    item1.setText(info['user'])
                    self.table1.setItem(r,1,item1)
                item2 = QTableWidgetItem()
                if('alt' in info):
                    item2.setText(str(info['alt']))
                    self.table1.setItem(r,2,item2)
                if('lat' in info):
                    item3 = QTableWidgetItem()
                    item3.setText(str(info['lat'])[0:8])
                    self.table1.setItem(r,3,item3)
                if('lon' in info):
                    item4 = QTableWidgetItem()
                    item4.setText(str(info['lon'])[0:8])
                    self.table1.setItem(r,4,item4)
                if('battlv' in info):
                    item5 = QTableWidgetItem()
                    item5.setText(str(info['battlv']))
                    self.table1.setItem(r,5,item5)
                if('snr' in info):
                    item6 = QTableWidgetItem()
                    item6.setText(str(info['snr']))
                    self.table1.setItem(r,6,item6)
                if('distance' in info):
                    item7 = QTableWidgetItem()
                    dist = (float)(info['distance']/1000.0)
                    dist = round(dist,2)
                    item7.setText(str(dist))
                    self.table1.setItem(r,7,item7)
                if('rilevamento' in info):
                    item8 = QTableWidgetItem()
                    item8.setText(str(round(info['rilevamento']*10)/10))
                    ex.table1.setItem(r,8,item8)
                if('chutil' in info):
                    item9 = QTableWidgetItem()
                    item9.setText(str(round(info['chutil']*10)/10))
                    self.table1.setItem(r,9,item9)
                if('airutil' in info):
                    item10 =  QTableWidgetItem()
                    item10.setText(str(round(info['airutil']*10)/10))
                    self.table1.setItem(r,10,item10)
                if('pressione' in info):
                    item11 = QTableWidgetItem()
                    item11.setText(str(round(info['pressione']*10)/10))
                    self.table1.setItem(r,11,item11)
                if('temperatura' in info):
                    item12 = QTableWidgetItem()
                    item12.setText(str(round(info['temperatura']*10)/10))
                    self.table1.setItem(r,12,item12)
                if('humidity' in info):
                    item13 = QTableWidgetItem()
                    item13.setText(str(round(info['humidity']*10)/10))
                    self.table1.setItem(r,13,item13)
                r += 1
    
    def testMsgOrig(self,msgID,orig):
        qr = "select count(*) from origmsg where msgid='"+str(msgID)+"' and origin='"+str(orig)+"'"
        self.calldb.dbbusy = True
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchall()
        #print(datas)
        cur.close()
        conn.close()
        self.calldb.dbbusy = False
        if(datas[0][0] == 0):
            return True
        return False

    
    def insertDB(self,query):
        timstr = time.perf_counter_ns()
        self.calldb.dbbusy = True
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
            print("Insert OK")
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(query)
        cur.close()
        conn.close()
        timtot = time.perf_counter_ns() - timstr
        print(f"InsertDB Tab. connessioni eseguita in {timtot // 1000000}ms.")
        self.calldb.dbbusy = False

        #inserisci nuovo user in dictionary
    def insertUser(self,nodenum,user,id):
        n = len(self.nodeInfo)
        i = 0
        while(i<n):
            if (nodenum == self.nodeInfo[i]['nodenum']):
                break
            else:
                i += 1
        if(i==n):   # nodenum non esiste, aggiungi nuovo user e id
            newuser = {}
            newuser['nodenum']=nodenum
            newuser['user']=user
            newuser['id'] = id
            newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
            newuser['ts'] = datetime.datetime.now().timestamp()
            # Insert newuser in DB
            qr = "insert into connessioni (data,ora,user) values('"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                "','"+datetime.datetime.now().strftime('%T')+"','"+user+"')"
            self.insertDB(qr)
            newuser['_id'] = self.max_IdDB()
            self.nodeInfo.append(newuser)
            print(newuser)
        else:
            self.nodeInfo[i]['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")           
            self.nodeInfo[i]['user'] = user
            self.nodeInfo[i]['id'] = id
            if('_id' in self.nodeInfo[i]):
                print("aggiorno orario su record trovato")
                qr = "update connessioni set user='"+user+"',data='"+datetime.datetime.now().strftime("%y/%m/%d")+ \
                "',ora='"+datetime.datetime.now().strftime("%T")+"' where _id="+str(self.nodeInfo[i]['_id'])  
                self.insertDB(qr)
            else:
                print("Inserisco record dopo attribuito _id")
                qr = "insert into connessioni (data,ora,user) values('"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                "','"+datetime.datetime.now().strftime('%T')+"','"+user+"')"
                self.insertDB(qr)
                self.nodeInfo[i]['_id'] = self.max_IdDB()
            self.nodeInfo[i]['ts'] = datetime.datetime.now().timestamp()
            self.showInfo()     # insert data in Table1 and set marker on geomap
            print(self.nodeInfo[i])


    def max_IdDB(self):
        qr = "select max(_id) from connessioni"
        self.calldb.dbbusy = True
        conn = dba.connect('meshDB.db')
        cur = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchall()
        print(datas)
        nr = datas[0][0]
        cur.close()
        conn.close()
        self.calldb.dbbusy = False
        return nr

    def findUser(self,nodenum):
        for info in self.nodeInfo:
            if(info['nodenum'] == nodenum):
                if('user' in info):
                    return (info['user'])
                else:
                    return("unknown")
        return ("unknown")

    def updateUser(self,nodenum,coord,altitude,distance,rilev):
        #trova id in nodeInfo
        i = 0
        lat, lon = coord
        for info in self.nodeInfo:
            if(info['nodenum'] == nodenum):
                if('user' not in info):
                    self.nodeInfo[i].update({'user': self.findUser(nodenum)}) 
                batt = ' '
                if('battlv' in self.nodeInfo[i]):
                    batt = str(self.nodeInfo[i]['battlv'])
                if('_id' in self.nodeInfo[i]):
                    # se la distanza precedente differisce di meno di 100mt dall'attuale
                    # lascia tutto inalterato e aggiorna solo la data e ts altrimenti
                    # crea nuovo record in connessioni 
                    if('distance' in info ):
                        if(abs(info['distance']-distance) < 100):
                            qr = "update connessioni set data='"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                                "',ora='"+datetime.datetime.now().strftime('%T')+"' where _id ="+str(self.nodeInfo[i]['_id'])
                            self.insertDB(qr)
                            self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                            self.nodeInfo[i].update({'ts': datetime.datetime.now().timestamp()})
                            print("Aggiornato data-ora in record con gps entro 100mt")
                        else:
                            # crea nuovo record coi nuovi parametri
                            dp = abs(info['distance']-distance)
                            #print(distance)
                            #print(info['distance'])
                            print("Distanza fra i due punti gps: "+str(dp))
                            #self.ricevuti.append("Distanza fra i due punti gps: "+str(dp))
                            newuser = {}
                            newuser['nodenum']=nodenum
                            newuser['_id'] = self.max_IdDB()+1
                            self.nodeInfo[i]['_id'] = newuser['_id']
                            newuser['lat'] = lat
                            self.nodeInfo[i]['lat'] = lat
                            newuser['lon'] = lon
                            self.nodeInfo[i]['lon'] = lon
                            newuser['alt'] = altitude
                            self.nodeInfo[i]['alt'] = altitude
                            newuser['distance'] = distance
                            self.nodeInfo[i]['distance'] = distance
                            newuser['rilevamento'] = rilev
                            self.nodeInfo[i]['rilevamento'] = rilev
                            newuser['battlv'] = batt
                            self.nodeInfo[i]['battlv'] = batt
                            newuser['user'] = self.findUser(nodenum)
                            self.nodeInfo[i]['user'] = newuser['user']
                            newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
                            self.nodeInfo[i]['time'] = newuser['time']
                            newuser['ts'] = datetime.datetime.now().timestamp()
                            self.nodeInfo[i]['ts'] = newuser['ts'] 
                            qr = "insert into connessioni (user,lat,lon,alt,dist,rilev,batt,data,ora) values('"+\
                                newuser['user']+"','"+str(newuser['lat'])+"','"+str(newuser['lon'])+ \
                                "','"+str(newuser['alt'])+"','"+str(newuser['distance'])+"','"+ \
                                str(newuser['rilevamento'])+"','"+newuser['battlv']+"','"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                                "','"+datetime.datetime.now().strftime('%T')+"')"
                            self.insertDB(qr)
                            print("(updateUser) Nuovo record gps mosso oltre 100mt")
                            print(newuser)
                    else: # non c'erano coordinate precedenti allora setta le attuali
                        self.nodeInfo[i].update({'lat': lat})
                        self.nodeInfo[i].update({'lon': lon})
                        self.nodeInfo[i].update({'alt': altitude})
                        self.nodeInfo[i].update({'distance': distance})
                        self.nodeInfo[i].update({'rilevamento': rilev})
                        self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                        self.nodeInfo[i].update({'ts': datetime.datetime.now().timestamp()})
                        qr = "update connessioni set lat="+str(self.nodeInfo[i]['lat'])+",lon="+str(self.nodeInfo[i]['lon'])+ \
                            ",alt="+str(self.nodeInfo[i]['alt'])+",dist="+str(self.nodeInfo[i]['distance'])+",rilev="+ \
                            str(self.nodeInfo[i]['rilevamento'])+",batt='"+batt+"',data='"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                            "',ora='"+datetime.datetime.now().strftime('%T')+"' where _id ="+str(self.nodeInfo[i]['_id'])
                        self.insertDB(qr)
                        print("(updateUser) aggiorno record per mancanza coord. precedenti")
                        print(self.nodeInfo[i])
                else:
                    # mancava _id inserisci nuovo record con le coordinate ricevute
                    try:
                        qr = "insert into connessioni (data,ora,lat,lon,alt,dist,rilev,data,ora,user) values('"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                            "','"+datetime.datetime.now().strftime('%T')+"','"+str(lat)+"','"+str(lon)+"','"+str(altitude)+\
                            "','"+str(distance)+"','"+str(rilev)+"','"+datetime.datetime.now().strftime('%y/%m/%d')+"','"+\
                            datetime.datetime.now().strftime('%T')+"','"+self.nodeInfo[i]['user']+"')"
                        self.insertDB(qr)
                        self.nodeInfo[i]['_id'] = self.max_IdDB()   
                        self.nodeInfo[i].update({'ts': datetime.datetime.now().timestamp()}) 
                        self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                        print("(updateUser) creato _id in record vecchio riaggiornato") 
                        print(self.nodeInfo[i]) 
                    except:
                        print("Campi null nella creazioni qr, record scartato")
                break
            i += 1
            if(len(self.nodeInfo) == i): # nuovo utente mai collegato prima
                newuser = {}
                newuser['nodenum'] = nodenum
                newuser['_id'] = self.max_IdDB()+1
                newuser['lat'] = lat
                newuser['lon'] = lon
                newuser['alt'] = altitude
                newuser['distance'] = distance
                newuser['rilevamento'] = rilev
                newuser['battlv'] = ' '
                newuser['user'] = self.findUser(nodenum)
                newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
                newuser['ts'] = datetime.datetime.now().timestamp()
                self.nodeInfo.append(newuser)
                qr = "insert into connessioni (user,lat,lon,alt,dist,rilev,batt,data,ora) values('"+\
                        newuser['user']+"','"+str(newuser['lat'])+"','"+str(newuser['lon'])+ \
                        "','"+str(newuser['alt'])+"','"+str(newuser['distance'])+"','"+ \
                        str(newuser['rilevamento'])+"','"+newuser['battlv']+"','"+datetime.datetime.now().strftime('%y/%m/%d')+ \
                        "','"+datetime.datetime.now().strftime('%T')+"')"
                self.insertDB(qr)
                print("(updateUser) nuovo utente mai collegato prima")
                print((newuser))

    def updateSnr(self,nodenum,snr):
        #trova/inserisci _id in nodeInfo
        i = 0
        for info in self.nodeInfo:
            if(info['nodenum'] == nodenum):
                self.nodeInfo[i].update({'snr': snr})
                self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                if('user' not in info):
                    self.nodeInfo[i]['user'] = self.findUser(nodenum)
                if('_id' in info):
                    qr = "update connessioni set snr="+str(self.nodeInfo[i]['snr'])+" where _id="+str(info['_id'])
                    self.insertDB(qr)
                break
            i += 1
            if(len(self.nodeInfo) == i):
                newuser = {}
                newuser['nodenum'] = nodenum
                newuser['_id'] = self.max_IdDB()+1
                newuser['snr'] = snr
                newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
                newuser['ts'] = datetime.datetime.now().timestamp()
                newuser['user'] = self.findUser(nodenum)
                self.nodeInfo.append(newuser)
                qr = "insert into connessioni (user,snr,data,ora) values('"+newuser['user']+\
                    "','"+newuser['snr']+"','"+datetime.datetime.now().strftime('%y/%m/%d')+"','"+ \
                    datetime.datetime.now().strftime('%T')+"')"
                self.insertDB(qr)
                print(newuser)

    def updateTelemetry(self,nodenum,battlv,chanutil,airutil):
        i = 0
        for info in self.nodeInfo:
            if(info['nodenum'] == nodenum):
                if('user' not in info):
                    self.nodeInfo[i].update({'user': self.findUser(nodenum)})
                if(battlv == ' '):
                    if('voltage' in self.nodeInfo[i]): # se controlliamo batteria da 12V / solar panel
                        if(self.nodeInfo[i]['voltage'] > 10.4):
                            carica = ((self.nodeInfo[i]['voltage']-10.5)/2.3)*100 # carica a 100% se batt = 12.8V
                        else:   # batteria interna a Tlora
                            carica = ((self.nodeInfo[i]['voltage']-3.6)/0.6)*100
                        battlv = round(carica,1)       
                self.nodeInfo[i].update({'battlv': battlv})
                self.nodeInfo[i].update({'chutil': round(chanutil,2)})
                self.nodeInfo[i].update({'airutil': round(airutil,2)})
                self.nodeInfo[i].update({'tsTl': datetime.datetime.now().timestamp()})
                self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                if('_id' in info):
                    qr = "update connessioni set batt='"+str(battlv)+"',data='"+datetime.datetime.now().strftime("%y/%m/%d")+\
                    "',ora='"+datetime.datetime.now().strftime("%T")+"' where _id="+str(info['_id'])
                    self.insertDB(qr)
                # aggiungere insert in connessioni in caso manchi _id
                else:
                    newuser = {}
                    self.nodeInfo[i]['_id'] = self.max_IdDB()+1
                    self.nodeInfo[i]['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
                    self.nodeInfo[i]['ts'] = datetime.datetime.now().timestamp()
                    if(isinstance(battlv,int)):
                        self.nodeInfo[i]['battlv'] = str(battlv)
                    else:
                        self.nodeInfo[i]['battlv'] = ' '
                    self.nodeInfo[i]['chutil'] = round(chanutil,2)
                    self.nodeInfo[i]['airutil'] = round(airutil,2)
                    self.nodeInfo[i]['tsTl'] = datetime.datetime.now().timestamp()
                    newuser['user'] = self.findUser(nodenum)   
                    qr = "insert into connessioni (batt,data,ora,user) values('"+str(battlv)+ \
                        "','"+datetime.datetime.now().strftime('%y/%m/%d')+"','"+ \
                        datetime.datetime.now().strftime('%T')+"','"+newuser['user']+"')"
                    self.insertDB(qr)
                    print("(telemetry) inserito nuovo record aggiornando _id") 
                    print(newuser)
                break
            i = i+1
        if(len(self.nodeInfo) == i):
            newuser = {}
            newuser['nodenum'] = nodenum
            newuser['_id'] = self.max_IdDB()+1
            newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
            newuser['ts'] = datetime.datetime.now().timestamp()
            newuser['battlv'] = battlv
            newuser['chutil'] = round(chanutil,2)
            newuser['airutil'] = round(airutil,2)
            newuser['tsTl'] = datetime.datetime.now().timestamp()
            newuser['user'] = self.findUser(nodenum)
            self.nodeInfo.append(newuser)
            qr = "insert into connessioni (batt,data,ora,user) values('"+str(battlv)+ \
                "','"+datetime.datetime.now().strftime('%y/%m/%d')+"','"+ \
                datetime.datetime.now().strftime('%T')+"','"+newuser['user']+"')"
            self.insertDB(qr)
            print("(telemetry) inserito nuovo record da user mai visto prima")
            print(self.nodeInfo[i])

    def updateSensors(self,nodenum,temperatura,pressione,humidity,voltage,corrente):
        i = 0
        for info in self.nodeInfo:
            if(info['nodenum'] == nodenum):
                if('user' not in info):
                    self.nodeInfo[i].update({'user': self.findUser(nodenum)})
                self.nodeInfo[i].update({'temperatura': temperatura})
                self.nodeInfo[i].update({'pressione': pressione})
                self.nodeInfo[i].update({'humidity': humidity})
                self.nodeInfo[i].update({'voltage': voltage})
                self.nodeInfo[i].update({'corrente': corrente})
                self.nodeInfo[i].update({'time': datetime.datetime.now().strftime("%d/%m/%y %T")})
                self.nodeInfo[i].update({'ts': datetime.datetime.now().timestamp()})   
                if('_id' not in info):
                    self.nodeInfo[i].update({'_id': self.max_IdDB()+1})
                    qr = "insert into connessioni (user,data,ora) values('"+self.nodeInfo[i]['user']+\
                    "','"+datetime.datetime.now().strftime('%y/%m/%d')+"','"+ \
                    datetime.datetime.now().strftime('%T')+"')"
                    self.insertDB(qr)
                    print("(UpdateSensors) Inserito nuovo record con _id")
                    print(self.nodeInfo[i])
                break
            i += 1
        if(len(self.nodeInfo) == i):
            newuser = {}
            newuser['nodenum'] = nodenum
            newuser['_id'] = self.max_IdDB()+1
            newuser['time'] = datetime.datetime.now().strftime("%d/%m/%y %T")
            newuser['ts'] = datetime.datetime.now().timestamp()
            newuser['temperatura'] = temperatura
            newuser['pressione'] = pressione
            newuser['humidity'] = humidity
            newuser['voltage'] = voltage
            newuser['corrente'] = corrente
            newuser['user'] = self.findUser(nodenum)
            print("(UpdateSensors) aggiunto record da user mai visto prima")
            self.nodeInfo.append(newuser)
            print(self.nodeInfo[i])


    #Horisontal Bearing
    def calcBearing(self,coord1,coord2):
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

    def haversine(self,coord1,coord2):
        R = 6372800  # Earth radius in meters
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        phi1, phi2 = math.radians(lat1), math.radians(lat2) 
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + \
            math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))


class meshInterface(QThread):
    packet     = {}
    pdict      = {}
    actionDone = pyqtSignal(object)
    interface = object
    msgcount = 1
    sendtx   = True
    secondi  = 0
    lastcnt  = -1

    def setInterface(self):    
        try:
            self.interface =  meshtastic.serial_interface.SerialInterface()
            pub.subscribe(self.onReceive, "meshtastic.receive") 
            print("Set interface..")
            return True
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Time out in attesa meshtastic.SerialInterface")
            ex.log.append("Errore time-out sulla seriale: STACCARE E RICOLLEGARE il device verificare poi che CLI meshtastic --info funzioni e quando OK rilanciare applicazione.")
            return False

    def setSendTx(self,st):
        self.sendtx = st
        if(st == False):
            if(ex.rbtn3.isChecked == False):
                print("Non Manderò messaggi periodici")
                ex.log.append("Non Manderò messaggi periodici")
        else:
            if(ex.rbtn3.isChecked == False):
                print("Manderò messaggi periodici")
                ex.log.append("Manderò messaggi periodici")

    def sendImmediate(self,msg):
        currTime = datetime.datetime.now().strftime("%H:%M:%S")
        msg = currTime+" "+ msg
        self.interface.sendText(msg)
        ex.ricevuti.append("Sending immediate: "+msg)
        print("Immediate message sent: " + msg)

    
    def run(self):
        print("meshInterface started..")
        if(self.setInterface() == False):
            return
        
        if(self.sendtx == True):
            ex.ricevuti.append("Hello mesh, manderò messaggi periodici.")
            self.interface.sendText("Hello mesh, manderò messaggi periodici.")
        else:
            ex.ricevuti.append("Hello mesh, non manderò messaggi periodici.")
            self.interface.sendText("Hello mesh, non manderò messaggi periodici.")

        while(True):
            time.sleep(1)
            self.secondi += 1
            if(self.secondi % 600 == 0):
                if(self.sendtx == True):
                    currTime = datetime.datetime.now().strftime("%H:%M:%S")
                    msg = str(self.msgcount)+" "+currTime+" "+ ex.inText.text()
                    self.interface.sendText(msg)
                    ex.ricevuti.append("Sending "+" "+msg)
                    print("Message sent: " + msg)
                    self.msgcount += 1
            
            if(self.packet == {}):
                continue
            else:
                ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
                print(ts+" Emit packet..")
                self.actionDone.emit(self.packet)
                self.packet = {}    
        ex.log.append("While loop in Thread interrotto..")

        
    
    def onReceive(self,packet,interface): # called when a packet arrives
        if(self.secondi > self.lastcnt):
            self.packet = packet
            ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
            print(ts)

        

class callDB(QThread):
    timstart = 0.0
    timtot   = 0.0
    dbbusy   = False
    slptcnt  = 0
    arraypdict = []

    def InsUpdtDB(self, pdict): 
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
        self.arraypdict.append(pdict)
        print(ts+" Acquisito dict"+str(len(self.arraypdict))+" per InsUpdtDB")
       
    def execInsUpdtDB(self,dict):
        #print("Inizio InsUpdt")
        print(dict)
        self.timstart = time.perf_counter_ns()
        chiave = dict['chiave']
        del dict['chiave']
        qr = "select count(*) from meshnodes where nodenum = "+str(chiave)
        data = datetime.datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.datetime.now().strftime("%T") 
        conn = dba.connect('meshDB.db')
        cur  = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchall()
        nr = datas[0][0]
        cur.close()
        conn.close()
        #print("Update o Insert?")
        campi = list(dict.keys())
        if(nr > 0):
            qr = "update meshnodes set data='"+data+"',ora='"+ora+"'"
            i = 0
            while(i < len(campi)):
                qr += ","+campi[i]+"='"+str(dict.get(campi[i]))+"'"
                i += 1           
            qr += " where nodenum="+str(chiave)
            #print(qr)
            self.insertDB(qr)
        else:
            qr = "insert into meshnodes (nodenum,data,ora,"
            i = 0
            while(i < len(campi)-1):
                qr += campi[i]+","
                i += 1
            qr += campi[i]+") values("+str(chiave)+",'"+data+"','"+ora+"','"
            i=0
            while(i < len(campi)-1):
                qr += str(dict.get(campi[i]))+"','"
                i += 1
            qr += str(dict.get(campi[i]))+"')"
            #print(qr)
            self.insertDB(qr)
            self.timtot = time.perf_counter_ns() - self.timstart
        print(f"InsUpdtDB eseguita in {self.timtot // 1000000}ms.")

    def insertDB(self,query):
        #print("callDB: Insert/Update")
        #print(query)
        try:
            conn = dba.connect('meshDB.db')
            #print("callDB conn.dba..")
        except:
            print("conn time-out in InsUpdtDB")
            return
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(query)
        cur.close()
        conn.close()

    def run(self):
        while(True):
            time.sleep(0.5)
            self.slptcnt += 1
            #ogni 5 minuti salva valori chanUtil e AirUtilTX di mioGW
            if(self.slptcnt % 600 == 0):
                myair = ex.airustx.text()
                myair = myair[0:len(myair)-1]
                myair = float(myair)/10
                mycha = ex.chusage.text()
                mycha = float(mycha[0:len(mycha)-1])
                data = datetime.datetime.now().strftime("%y/%m/%d") 
                ora  = datetime.datetime.now().strftime("%T") 
                qr = "insert into airtx (data,ora,nodenum,longname,chanutil,airutiltx) \
                    values('"+data+"','"+ora+"','"+str(ex.mynodeId)+"','mioGW','"+str(mycha)+\
                    "','"+str(myair)+"')"
                self.insertDB(qr)
                print("Miei valori ChanUtil e AirUtilTX inseriti..")
                #ora inserisci ChanUtil e AirUtilTX per tutti i peers presenti in nodeInfo[]
                tstamp = datetime.datetime.now().timestamp()
                for info in ex.nodeInfo:
                    qr = "insert into airtx (data,ora,nodenum,longname,chanutil,airutiltx,battlv,pressione,temperatura,umidita,voltage,corrente) values('"\
                        +data+"','"+ora+"','"
                    #if('tsTl' in info):
                    if('chutil'in info and 'airutil' in info and not info['user'] == 'mioGW'):
                        #tdiff = tstamp - info['tsTl']
                        press = ' '
                        if('pressione' in info):
                            press = str(round(info['pressione'],1))
                        tempr = ' '
                        if('temperatura' in info):
                            tempr = str(round(info['temperatura'],1))
                        umid = ' '
                        if('humidity' in info):
                            umid = str(round(info['humidity'],1))
                        voltage = ' '
                        if('voltage' in info):
                            voltage =  str(round(info['voltage'],2))
                        corrente = ' '
                        if('corrente' in info):
                            corrente = str(round(info['corrente'],2))
                        #if(tdiff < 500):    #ultimo msg non più vecchio di 10min
                        qr += str(info['nodenum'])+"','"+info['user']+"','"+str(round(info['chutil'],2))+"','"+ \
                                str(round(info['airutil'],2))+"','"+str(info['battlv'])+"','"+press+"','"+tempr+"','"+umid+"','"+voltage+"','"+corrente+"')"
                        self.insertDB(qr)
                        print("Aggiornato AirUtilTX di "+info['user'])
                        #print(info)

            if(len(self.arraypdict) == 0):  
                continue
            else:
                if(self.dbbusy == False):
                    for pdict in self.arraypdict:
                        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")         
                        print(ts+" Eseguo InsUpdtDB..")
                        self.execInsUpdtDB(pdict)
                    self.arraypdict = []
                else:
                    print("meshDB occupato..")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App() 
    ex.loadHist()
    ex.loadPeers()
    sys.exit(app.exec_())  