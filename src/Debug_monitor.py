import serial,sys,time
from PyQt5.QtWidgets import QApplication, QWidget,QVBoxLayout,  \
            QHBoxLayout,QLineEdit,QTextEdit,QLabel,QPushButton, \
            QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal

class portaSeriale(QThread):
    encoding = 'utf-8'
    numOfLines = 0
    ser = serial.Serial()
    ser.port = "COM8"
    logFile = open('debugLog.log','wt')
    FOUND = False
    GIRA = True
    pbarset = pyqtSignal(int)
    shwdata = pyqtSignal(str)

    def initPorta(self,port,brate):
        #initialization and open the port
        #possible timeout values:
        #    1. None: wait forever, block call
        #    2. 0: non-blocking mode, return immediately
        #    3. x, x is bigger than 0, float allowed, timeout block call
        self.ser.port = port
        self.ser.baudrate = brate
        self.ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        self.ser.parity = serial.PARITY_NONE #set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        self.ser.timeout = None     #block read
        #ser.timeout = 1            #non-block read
        #ser.timeout = 2            #timeout block read
        self.ser.xonxoff = False    #disable software flow control
        self.ser.rtscts = False     #disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False     #disable hardware (DSR/DTR) flow control
        #ser.writeTimeout = 2       #timeout for write

        try: 
            self.ser.open()
            self.logFile = open('debugLog.log','wt')
        except serial.SerialException as err:
            print (str(err))
            return (False)

        if self.ser.isOpen():
            self.ser.flushInput()    #flush input buffer, discarding all its contents
            #self.ser.flushOutput()  #flush output buffer, aborting current output 
                                #and discard all that is in buffer
            time.sleep(0.5)     #give the serial port sometime to receive the data
        else:
            print ("cannot open serial port ")
            return (False)
        return (True)

    def stopRcv(self,c):
        print ('ricevuto stop')
        self.GIRA = False

    def run(self):
        ex.stoprcv.connect(self.stopRcv)
        print('connesso in run')
        try: 
            while self.GIRA == True:
                response = self.ser.readline()
                try:
                    data = response.decode(self.encoding)
                    data = data.replace('\r\n',' ')
                except:
                    print("Decoding error")
                    continue
                if(ex.skip.text() in data):
                    continue
                #print(data)
                #ex.dblog.append(data)
                self.shwdata.emit(data)
                try:
                    if(len(ex.righe) < ex.toprighe):
                        ex.righe.append(data+'\n')
                    else:
                        ex.righe.pop(0)
                        ex.righe.append(data+'\n')

                    if((len(ex.righe) % 5) == 0):
                        val = (len(ex.righe)/ex.toprighe)*100
                        self.pbarset.emit(round(val))

                except:
                    print("Errore gestione righe / prog. bar")
            
                if(ex.stop.text() in data):
                    self.FOUND = True
                    print("Fine log trovata..")
                    ex.progress.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: red;"
                      "}")
                
                if(self.FOUND == False):
                    ex.progress.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: lightgreen;"
                      "}")  
            
                if(self.FOUND == True):
                    self.numOfLines += 1   
            
                if (self.numOfLines > 250):
                    break
            
            ex.progress.setStyleSheet("QProgressBar::chunk "
                      "{"
                      "background-color: yellow;"
                      "}") 
            print("Fine ricezione.")

            while(len(ex.righe) > 0):
                self.logFile.write(ex.righe.pop(0))
            self.logFile.close()
            self.ser.close()
            ex.RUNNING = False

        except serial.SerialException as e:
            print ('(run)'+str(e))


class App(QWidget):
    stoprcv = pyqtSignal(int)
    portser = object 
    RUNNING = False
    righe = list()
    toprighe = 500
    
    def __init__(self):
        super().__init__()
        self.title = 'Debug manager'
        self.initUI()
        
    def initUI(self):
        startb = QPushButton("START",self)
        startb.clicked.connect(self.start_click)
        stopb = QPushButton("STOP",self)
        stopb.clicked.connect(self.stop_click)
        lblport = QLabel("Porta:")
        self.porta = QLineEdit('COM8')
        self.porta.setMaximumWidth(40)
        lblspeed = QLabel("Velocità")
        self.speed = QLineEdit('115200')
        self.speed.setMaximumWidth(50)
        lblskip = QLabel("Skip msg con")
        self.skip = QLineEdit('[mqtt]')
        self.skip.setMaximumWidth(70)
        lblstop = QLabel("Stop su")
        self.stop = QLineEdit('[Screen] Done with boot')
        lblprogre =  QLabel("Size out file")
        self.progress = QProgressBar(self)
        lbllog = QLabel("Debug log")
        self.dblog = QTextEdit()
        self.dblog.setFontFamily('Courier New')

        self.layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(startb)
        hbox.addWidget(stopb)
        hbox.addWidget(lblport)
        hbox.addWidget(self.porta)
        hbox.addWidget(lblspeed)
        hbox.addWidget(self.speed)
        hbox.addWidget(lblskip)
        hbox.addWidget(self.skip)
        hbox.addWidget(lblstop)
        hbox.addWidget(self.stop)
        hbox.addWidget(lblprogre)
        hbox.addWidget(self.progress)
        self.layout.addLayout(hbox)
        self.layout.addWidget(lbllog)
        self.layout.addWidget(self.dblog)
        self.setWindowTitle(self.title)
        self.setGeometry(100, 50, 1024,640)
        self.show()

    def start_click(self):
        self.dblog.clear()
        if(self.RUNNING == False):
            self.portser = portaSeriale()
            if(self.portser.initPorta(self.porta.text(),self.speed.text()) == True):
                self.portser.pbarset.connect(self.setPbar)
                self.portser.shwdata.connect(self.appendData)
                self.portser.start()
                self.RUNNING = True

    def stop_click(self):
        if(self.RUNNING == True):
            self.stoprcv.emit(1)
            #print("Emesso stop")

    def appendData(self,data):
        self.dblog.append(data)

    def setPbar(self,prog):
        #print('rcv '+str(prog))
        self.progress.setProperty("value", prog)

    def closeEvent(self, event):
        print('Fine applicazione')
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App() 
    sys.exit(app.exec_())  