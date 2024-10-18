'''
Created on Oct 17, 2024

@author: luis
'''
import sys
import paho.mqtt.publish as mqttpub
import paho.mqtt.subscribe as mqttsub

from PySide6.QtWidgets import QApplication,QMainWindow,QMessageBox

from hmi.ui_hmi import Ui_MainWindow
from PySide6.QtCore import QThread, Signal, Slot

class MqttThread(QThread):
    
    msgReceived=Signal(str,int)
    
    def __init__(self,group=None):
        if group is not None:
            self.topic = "plcdata/"+group
        else:
            self.topic = "plcdata"
        super().__init__()
    
    def run(self):
        a = True
        while (a):
            message = mqttsub.simple(self.topic + "/+", hostname="localhost")
            msg = message.payload.decode('ascii')
            val = int(message.topic[len(message.topic)-1])
            self.msgReceived.emit(msg,val)
            print(msg)
            if msg == "END":
                a = False
    
class MainWindow(QMainWindow):
    def __init__(self,params=None):
        super().__init__(params)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

class HmiWindow(MainWindow):
    def __init__(self,params=None):
        super().__init__(params)
        
        # Configure mqtt subscriptions
        
        self.lcdThread = MqttThread("lcd")
        self.labelThread = MqttThread("label")
        
        # Create arrays for ui objects
        
        self.dial_array=[self.ui.dial,self.ui.dial_2,self.ui.dial_3,self.ui.dial_4]
        self.button_array=[self.ui.pushButton,self.ui.pushButton_2,self.ui.pushButton_3]
        self.lcd_array=[self.ui.lcdNumber,self.ui.lcdNumber_2,self.ui.lcdNumber_3,self.ui.lcdNumber_4]
        self.label_array=[self.ui.label,self.ui.label_2,self.ui.label_3]
        
        # Disable Stop
        
        self.ui.actionStop.setEnabled(False)
        
        # Connect Signals and Slots
        
        self.ui.actionStart.triggered.connect(self.onStart)
        self.ui.actionStop.triggered.connect(self.onStop)
        self.ui.actionAbout_Qt.triggered.connect(lambda:QMessageBox.aboutQt(self,"About Qt"))
        self.ui.actionAbout.triggered.connect(lambda:QMessageBox.about(self,"About MQTT HMI",
                "(C) 2024 Luis Díaz Saco\nDistributed under AGPL"))
        
        fdial = lambda i: lambda: self.onDial(i)
        for i in range(len(self.dial_array)):
            self.dial_array[i].valueChanged.connect(fdial(i))
        
        fbutton = lambda i: lambda: self.onPushButton(i)
        for i in range(len(self.button_array)):
            self.button_array[i].clicked.connect(fbutton(i))
        
        self.lcdThread.msgReceived.connect(self.onIntMessage)
        self.labelThread.msgReceived.connect(self.onBoolMessage)
        
    def onStart(self):
        self.ui.actionStart.setEnabled(False)
        self.lcdThread.start()
        self.labelThread.start()
        self.ui.actionStop.setEnabled(True)
        
    def onStop(self):
        self.ui.actionStop.setEnabled(False)
        self.lcdThread.terminate()
        self.lcdThread.wait()
        self.labelThread.terminate()
        self.labelThread.wait()
        self.ui.actionStart.setEnabled(True)
           
    def onDial(self,pos):
        mqttpub.single("plcdata/dial/"+str(pos),str(self.dial_array[pos].value()),hostname="localhost")
    
    def onPushButton(self,pos):
        mqttpub.single("plcdata/button/"+str(pos),"Button pressed",hostname="localhost")
    
    @Slot(str,int)    
    def onIntMessage(self,data,pos):
        self.lcd_array[pos].display(data)
        
    @Slot(str,int)
    def onBoolMessage(self,data,pos):
        if data == '0':
            self.label_array[pos].setText("FALSE")
        else:
            self.label_array[pos].setText("TRUE")


        
class hmiApp(QApplication):
    '''
    classdocs
    '''

    def __init__(self,params):
        '''
        Constructor
        '''
        super().__init__(params)
        
def main():
    app = hmiApp(sys.argv)
    win = HmiWindow()
    app.aboutToQuit.connect(win.close)
    win.show()

    ret = app.exec()
    return ret
    
if __name__ == '__main__':
    print('MQTT HMI 0.0.1: (c) 2024 Luis Díaz Saco')
    sys.exit(main())