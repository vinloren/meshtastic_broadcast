import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, \
            QTableWidgetItem,QVBoxLayout,QHBoxLayout,QLineEdit,QTextEdit,QLabel,QCheckBox          
from PyQt5.QtGui import QIcon

import meshtastic
from pubsub import pub
import threading
import time
from time import sleep
import datetime


count = 0

class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.title = 'Meshtastic data show'
        self.initUI()
        
    def initUI(self):
        self.labels = ['data ora','origine','destinazione','tipo messaggio','payload','utente', \
            'da_id','a_id','altitudine','latitudine','longitudine','rxSnr']
        self.csvFile = open('meshtastic_data.csv','wt')
        self.setWindowTitle(self.title)
        self.inText = QLineEdit()
        self.inText.setMaximumWidth(250)
        self.inText.setText("cq de I1LOZ")
        label2 = QLabel("Dati inviati: ")
        label2.setMaximumWidth(70)
        self.rbtn1 = QCheckBox('Solo ricezione') 
        self.rbtn2 = QCheckBox('Genera csv file')
        self.rbtn1.setMaximumWidth(150)
        self.rbtn2.setMinimumWidth(730)
        hbox = QHBoxLayout()
        hbox.addWidget(label2)
        hbox.addWidget(self.inText) 
        hbox.addWidget(self.rbtn1)
        hbox.addWidget(self.rbtn2)
        vbox = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(self.labels)
        label = QLabel("Log dati ricevuti")
        self.log = QTextEdit()
        self.log.setMaximumHeight(180)
        vbox.addWidget(self.table)
        vbox.addWidget(label)
        vbox.addWidget(self.log)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setGeometry(100, 100, 1200, 700)
        self.rbtn2.clicked.connect(self.handleFile)
        self.show()

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



def onReceive(packet, interface): # called when a packet arrives
    print(f"Received: {packet}")
    row = [';',';',';',';',';',';',';',';',';',';',';',' \n']
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
    if ('data' in packet['decoded']):
        tipmsg = packet['decoded']['data']['portnum']
        row[3] = packet['decoded']['data']['portnum']+';'
        item3 = QTableWidgetItem()
        item3.setText(tipmsg)
        ex.table.setItem(r,3,item3)
        item4 = QTableWidgetItem()
        item4.setText(str(packet['decoded']['data']['payload']))
        row[4] = str(packet['decoded']['data']['payload'])+';'
        ex.table.setItem(r,4,item4)
        if (packet['decoded']['data']['portnum'] == 'NODEINFO_APP'):
            item5 = QTableWidgetItem()
            item5.setText(packet['decoded']['data']['user']['longName'])
            row[5] = packet['decoded']['data']['user']['longName']+';'
            ex.table.setItem(r,5,item5)
        if (packet['decoded']['data']['portnum'] == 'POSITION_APP'):
            if('altitude' in packet['decoded']['data']['position']):
                item8 = QTableWidgetItem()
                item8.setText(str(packet['decoded']['data']['position']['altitude']))
                row[8] = str(packet['decoded']['data']['position']['altitude'])+';'
                ex.table.setItem(r,8,item8)
                item9 = QTableWidgetItem()
                item9.setText(str(packet['decoded']['data']['position']['latitude'])[0:8])
                row[9] = str(packet['decoded']['data']['position']['latitude'])[0:8]+';'
                ex.table.setItem(r,9,item9)
                item10 = QTableWidgetItem()
                item10.setText(str(packet['decoded']['data']['position']['longitude'])[0:8])
                row[10] = str(packet['decoded']['data']['position']['longitude'])[0:8]+';'
                ex.table.setItem(r,10,item10)
            if('rxSnr' in packet):
                item11 = QTableWidgetItem()
                item11.setText(str(packet['rxSnr']))
                row[11] = str(packet['rxSnr'])+'\n'
                ex.table.setItem(r,11,item11)
    else:
        item6 = QTableWidgetItem()
        item6.setText(packet['fromId'])
        row[6] = packet['fromId']+';'
        ex.table.setItem(r,6,item6)
        item7 = QTableWidgetItem()
        item7.setText(packet['toId'])
        row[7] = packet['toId']+';'
        ex.table.setItem(r,7,item7)
        if ('position' in packet['decoded']):
            item8 = QTableWidgetItem()
            item8.setText(str(packet['decoded']['position']['altitude']))
            row[8] = str(packet['decoded']['position']['altitude'])+';'
            ex.table.setItem(r,8,item8)
            item9 = QTableWidgetItem()
            item9.setText(str(packet['decoded']['position']['latitudeI']/10000000)[0:8])
            row[9] = str(packet['decoded']['position']['latitudeI']/10000000)[0:8]+';'
            ex.table.setItem(r,9,item9)
            item10 = QTableWidgetItem()
            item10.setText(str(packet['decoded']['position']['longitudeI']/10000000)[0:8])
            row[10] = str(packet['decoded']['position']['longitudeI']/10000000)[0:8]+';'
            ex.table.setItem(r,10,item10)
            if('rxSnr' in packet):
                item11 = QTableWidgetItem()
                item11.setText(str(packet['rxSnr']))
                row[11] = str(packet['rxSnr'])+'\n'
                ex.table.setItem(r,11,item11)
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
    rt = RepeatedTimer(30, sendText) # no need of rt.start()


def sendText(): # called every x seconds
    if(ex.rbtn1.isChecked()==False):
        currTime = datetime.datetime.now().strftime("%H:%M:%S")
        msg = str(count)+" "+currTime+" "+ex.inText.text()
        interface.sendText(msg)
        ex.log.append("Sending "+" "+msg)
        print("Message sent: " + msg)

 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")
    interface = meshtastic.SerialInterface()
    sys.exit(app.exec_())  
