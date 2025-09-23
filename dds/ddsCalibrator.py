"""DDS power calibration"""
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import time
sys.path.append(r'Z:\Tweezer\Code\Python 3.5\PyDex')
sys.path.append(r'Z:\Tweezer\Code\Python 3.5\PyDex\networking')
from networker import PyServer
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
    QFileDialog, QBoxLayout, QLineEdit)
from PyQt5.QtCore import QTimer

class calibrator(QWidget):
    def __init__(self, ):
        super().__init__()
        self.daq_tcp = PyServer(host='', port=8622) # server for DAQ
        self.daq_tcp.textin.connect(self.respond)
        self.daq_tcp.start()
        self.dds_tcp = PyServer(host='', port=8624) # server for DDS
        self.dds_tcp.start()
        
        layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.maxamp = QLineEdit('0.5', self)
        layout.addWidget(self.maxamp)
        self.comport = QLineEdit('COM11', self)
        layout.addWidget(self.comport)
        self.profile = QLineEdit('P7', self)
        layout.addWidget(self.profile)
        self.status = QLabel('n = 0, amp = 0, power = 0')
        layout.addWidget(self.status)
        self.lastval = QLabel('')
        layout.addWidget(self.lastval)
        reset = QPushButton('Reset')
        reset.clicked.connect(self.reset)
        layout.addWidget(reset)
        programme = QPushButton('Programme DDS')
        programme.clicked.connect(self.programme)
        layout.addWidget(programme)
        measure = QPushButton('DAQ Measure')
        measure.clicked.connect(self.measure)
        layout.addWidget(measure)
        store = QPushButton('Store Result')
        store.clicked.connect(self.store)
        layout.addWidget(store)
        save = QPushButton('Save Results')
        save.clicked.connect(self.save)
        layout.addWidget(save)
        auto = QPushButton('Autorun')
        auto.clicked.connect(self.autorun)
        layout.addWidget(auto)
        
        self.amps = np.linspace(0,float(self.maxamp.text()),15)
        # np.random.shuffle(self.amps)
        self.power = np.zeros(len(self.amps))
        self.n = 0 # index for counting
        
    def reset(self):
        try:
            self.amps = np.linspace(0,float(self.maxamp.text()),15)
            # np.random.shuffle(self.amps)
            self.power = np.zeros(len(self.amps))
            self.n = 0
        except Exception as e:
            self.status.setText('n = %s --- exception: '+str(e))
    
    def programme(self):
        try:
            self.dds_tcp.add_message(self.n, 'set_data=[["%s", "%s", "Amp", %s]]'%(self.comport.text(), self.profile.text(), self.amps[self.n])) 
            self.dds_tcp.add_message(self.n, 'programme=stp')
        except Exception as e:
            self.status.setText('n = %s --- exception: '+str(e))
        
    def measure(self):
        """Request a measurement from the DAQ"""
        # self.daq_tcp.add_message(self.n, 'reset graph')
        # time.sleep(1)
        # self.daq_tcp.add_message(self.n, 'start')
        self.daq_tcp.add_message(self.n, 'measure')
        self.daq_tcp.add_message(self.n, 'readout')

    def reset_graph(self):
        """Request the DAQ to reset the graph."""
        self.daq_tcp.add_message(self.n, 'reset graph')
    
    def respond(self, msg): 
        print(msg)
        try:
            float(msg)
            self.lastval.setText(msg)
        except:
            pass

    def store(self): 
        try:
            self.power[self.n] = float(self.lastval.text())
            self.status.setText('n = %s, amp = %s, power = %s'%(
                self.n, self.amps[self.n], self.power[self.n]))
            self.n += 1
        except Exception as e:
            self.status.setText('n = %s --- exception: '+str(e))
        
    def save(self, fname=''):           
        if not fname:
            fname, _ = QFileDialog.getSaveFileName(self, 'Save File')                
        np.savetxt(fname, [self.amps, self.power], delimiter=',')
        plt.plot(self.amps, self.power, 'o-')
        plt.xlabel('DDS Amp')
        plt.ylabel('DAQ signal (V)')
        plt.show()

    def autorun(self):
        self.amp_index = 0
        self.auto_start()

    def auto_start(self):
        if self.amp_index >= len(self.amps):
            self.save()
            return

        self.programme()
        QTimer.singleShot(5000, self.auto_reset_graph)

    def auto_reset_graph(self):
        self.reset_graph()
        QTimer.singleShot(5000, self.auto_measure)

    def auto_measure(self):
        QApplication.processEvents()
        self.measure()
        QTimer.singleShot(5000, self.auto_store)

    def auto_store(self):
        QApplication.processEvents()
        self.store()
        QTimer.singleShot(2000, self.next_amp)

    def next_amp(self):
        self.amp_index += 1
        self.auto_start()
        
if __name__ == "__main__":
    app = QApplication.instance()
    standalone = app is None # false if there is already an app instance
    if standalone: # if there isn't an instance, make one
        app = QApplication(sys.argv) 
        
    boss = calibrator()    
    boss.show()
    if standalone: # if an app instance was made, execute it
        sys.exit(app.exec_()) # when the window is closed, python code stops