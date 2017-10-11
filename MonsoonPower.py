import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import time
from time import sleep
import numpy
import json
import sys
from threading import Thread

MONSOON_USB_MODE = 'MONSOON_USB_MODE'
MONSOON_MAIN_MODE = 'MONSOON_MAIN_MODE'
MONSOON_AUX_MODE = 'MONSOON_AUX_MODE'

class myMonsoon(Thread):
 
    # set up a monsoon for main, USB or aux monitoring
    def __init__(self, configuration=MONSOON_USB_MODE):
        self.mon = HVPM.Monsoon()
        self.mon.setup_usb()
        self.mon.setVout(4.2)
#        self.mon.setVoltageChannel(0)
        self.engine = sampleEngine.SampleEngine(self.mon)
        self.engine.disableCSVOutput()
        self.engine.ConsoleOutput(False)
        
        #enable all channels for now
        self.engine.enableChannel(sampleEngine.channels.timeStamp)
        self.engine.enableChannel(sampleEngine.channels.MainCurrent)
        self.engine.enableChannel(sampleEngine.channels.MainVoltage)
        self.engine.enableChannel(sampleEngine.channels.USBCurrent)
        self.engine.enableChannel(sampleEngine.channels.USBVoltage)
        self.engine.enableChannel(sampleEngine.channels.AuxCurrent)
        
 #       self.mon.setUSBPassthroughMode(op.USB_Passthrough.Off)
        sleep(0.1)

        self.engine._SampleEngine__Reset()
        self.engine._SampleEngine__sampleLimit = 100000
    

        # get calibration calibration
        self.mon.StartSampling(1,maxTime=0xFFFFFFFF)
        calibrated = False
        for i in range(1,30000):
            self.getsample()
            print(self.engine._SampleEngine__mainCal.zeroCalFine)
        
        exit()
        
        while not calibrated:
            self.getsample()
            calibrated = self.engine._SampleEngine__isCalibrated()
         
        self.mon.stopSampling()
        self.mon.StartSampling(1250)
#        self.engine._SampleEngine__startTime = time.time()
        self.engine._SampleEngine__startTime = 0
        for i in range(1,80):
            self.getsampleDict()
     

    def getsample(self):
    
        buf = self.mon.BulkRead()
        print(buf)
        Sample = self.mon.swizzlePacket(buf)
    #    Sample.append(time.time() - self.engine._SampleEngine__startTime)
        Sample.append(time.time())
        numSamples = Sample[2]
        bulkPackets = self.engine._SampleEngine__processPacket([Sample])
    
        if(len(bulkPackets) > 0):
            self.engine._SampleEngine__vectorProcess(bulkPackets)
        return self.engine.getSamples()

    def getsampleDict(self):
        s= self.getsample()
        # pack into Dict
        return {"sample" : numpy.mean(s[sampleEngine.channels.timeStamp]), \
            "MainCurrent" : numpy.mean(s[sampleEngine.channels.MainCurrent]),\
            "MainVoltage" : numpy.mean(s[sampleEngine.channels.MainVoltage]), \
            "MainPower" : numpy.mean(s[sampleEngine.channels.MainCurrent])*numpy.mean(s[sampleEngine.channels.MainVoltage]),\
            "USBCurrent" : numpy.mean(s[sampleEngine.channels.USBCurrent]), \
            "USBVoltage" : numpy.mean(s[sampleEngine.channels.USBVoltage]),
            "USBPower" : numpy.mean(s[sampleEngine.channels.USBCurrent]) * numpy.mean(s[sampleEngine.channels.USBVoltage]), \
            "AuxCurrent": numpy.mean(s[sampleEngine.channels.AuxCurrent])}
            

def outputcsv(dict):
    count = 0
    for key in dict.keys():
        if count >0:
            sys.stdout.write(",")   
        sys.stdout.write(str(dict[key]))
        count=count+1
    sys.stdout.write("\n")

def outputheader(dict):
    count = 0
    for key in dict.keys():
        if count >0:
            sys.stdout.write(",")   
        sys.stdout.write(str(key))
        count=count+1
    sys.stdout.write("\n")
    sys.stdout.flush()


def main():
    mymonsoon = myMonsoon()
    s=mymonsoon.getsampleDict()
    outputheader(s)
   
    try:
        while True:
            s = mymonsoon.getsampleDict()
            outputcsv(s)
            sleep(0.001)

    except KeyboardInterrupt:
        pass
        
if __name__ == "__main__":
    main()
