#!/usr/bin/python
'''*****************************************************************************************************************
    Modified from
    Seeed Studio Relay Board Example
    By John M. Wargo
    www.johnwargo.com
********************************************************************************************************************'''
from __future__ import print_function

import sys
import time
import os
import glob
import time
import datetime
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = [glob.glob(base_dir + '28*')[0],glob.glob(base_dir + '28*')[1],glob.glob(base_dir + '28*')[2],glob.glob(base_dir + '28*')[3]]
device_file = (device_folder[0] +'/w1_slave', device_folder[1] +'/w1_slave', device_folder[2] +'/w1_slave', device_folder[3] +'/w1_slave')

#from relay_lib_seeed import *

def read_temp_raw(device):
    f=open(device_file[device], 'r')
    lines=f.readlines()
    f.close()
    return lines

def read_temp(device):
    lines=read_temp_raw(device)
    while lines[0].strip()[-3:]!='YES':
        time.sleep(0.2)
        lines=read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    
#SENSORS  
room_temp=0
water_tank=1
solar_panel=3
wood_stove=2

#PUMPS
pump=20


# valves
floor_valve = 21 #relay 3
stove_valve = 26 # relay 1

# state machine implementation

class State(object):
    """
    We define a state object which provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self):
        print 'Processing current state:', str(self)

    def on_event(self, event):
        """
        Handle events that are delegated to this State.
        """
        pass

# state transitions

class PumpOff(State):
    """
    The state which indicates that there are limited device capabilities.
    """
    def __init__:
        # switch the pump off
        # cameron thinks the code to actually turn the pump off goes here

    def on_ event(self, event):
        if event["TIME_OF_DAY"] and event["SP_GT_WT"]
            return PumpOnNoValues()
            # event["STOVE_HOT"]
            # event["WT_GT_RT"]
            # event["SP_GT_WT"]
        return self


class PumpOnNoValues(State):
    """
    The state which indicates that there are no limitations on device
    capabilities.
    """
    def __init__:
        # switch the pump on
        # cameron thinks the code to actually turn the pump off goes here

    def on_event(self, event):
        if event["TIME_OF_DAY"]
            return PumpOff()
            # event["STOVE_HOT"]
            # event["WT_GT_RT"]
            # event["SP_GT_WT"]

        return self

class PumpOnWoodStove(State):
    """
    The state which indicates that there are no limitations on device
    capabilities.
    """

    def on_event(self, event):
        if event == 'device_locked':
            return LockedState()

        return self

class PumpOnFloorValve(State):
    """
    The state which indicates that there are no limitations on device
    capabilities.
    """

    def on_event(self, event):
        if event == 'device_locked':
            return LockedState()

        return self

class Pump(object):
    """ 
    A simple state machine that mimics the functionality of a device from a 
    high level.
    """

    def __init__(self):
        """ Initialize the components. """

        # Start with a default state.
        self.state = PumpOff()

    def on_event(self, event):
        """
        This is the bread and butter of the state machine. Incoming events are
        delegated to the given states which then handle the event. The result is
        then assigned as the new state.
        """

        # The next state will be the result of the on_event function.
        self.state = self.state.on_event(event)


def process_loop():

    time.sleep(1)
#   print("Stan says we are in ",__name__)
    fp=0
    sp=0
    stove_hot=0
    GPIO.output(stove_valve,0)
    GPIO.output(pump,0)
    GPIO.output(floor_valve,0)
	currenthour = datetime.datetime.now().strftime("%H")
    

    # now cycle each relay every second in an infinite loop
    while True:
        
        wtt = read_temp(water_tank)
        spt = read_temp(solar_panel)
        wst = read_temp(wood_stove)
		ght = read_temp(room_temp)
        now = int(time.time())

        TIME_OF_DAY = int(datetime.datetime.now().strftime("%H"))>10 and int(datetime.datetime.now().strftime("%H"))<17
        STOVE_HOT = wst > 40
        WT_GT_RT = wtt > ght # water tank hotter than the room
        SP_GT_WT = spt > wtt # solar panel greater than water temp

        eventDict = {
            "TIME_OF_DAY": TIME_OF_DAY,
            "STOVE_HOT": STOVE_HOT,
            "WT_GT_RT": WT_GT_RT,
            "SP_GT_WT": SP_GT_WT,
        }
        
        Pump.on_event(eventDict)
        ## cameron says the file ends here 




        if(STOVE_HOT and stove_hot==0):
            # stove_hot=1
            GPIO.output(pump,1)
            GPIO.output(stove_valve,1)
            print('stove is hot: pump and stove valve active')
        else:
            if stove_hot==1:
                if(wst > wtt):
                    print('leave stove valve and pump on')    
                    
                else:
                    stove_hot=0
                    GPIO.output(pump,0)
                    GPIO.output(stove_valve,0)
                    print('pump on')
                    print('stove hot pump and valve active')
            
        # Loop to run the water to solar panels
        if TIME_OF_DAY and stove_hot==0:  #only allowed to run daylight h
            print('inside of daylight hours')
            
            if(spt>wtt+10):  #solar panel is 10c degrees hotter than tank
                GPIO.output(pump,1)
                print('pump on')
                sp=1
            else:
                if(sp==1 ):
                    if(spt>wtt+0):  #solar panel is 1 degrees hotter than tank
                        print('leave pump on')  
                    else:
                        GPIO.output(pump,0)
                        print('pump off')
                        sp=0
                else:
                    GPIO.output(pump,0)
                    print('pump off')
        else:
            if(stove_hot == 0):
                GPIO.output(pump,0)
                print('pump off')
            print('outside of daylight hours')
        # END loop for solar panel pump
        
        

        print('room temperature is ',read_temp(room_temp), 'or in fahernheit',read_temp(room_temp)*9/5+32)
        print('Water Tank Temperature is ',wtt,'or in fahernheit',wtt*9/5+32)
        print('top of solar panel is ',spt,'or in fahernheit',spt*9/5+32)
        print('the wood stove is ',wst,'or in fahernheit',wst*9/5+32)
        print(datetime.datetime.now().strftime("%H"))

		if(GPIO.input(pump)==1):
        		f = open('./monthly_results/grnhouse' + time.strftime('%B') + '.csv','a')
        		f.write(str(now) + ','+ str(ght) + ',' + str(wtt) + ',' + str(spt) + ',' + str(wst) + ',' + str(GPIO.input(pump)) + '\n') #Give your csv text here.
        		## Python will convert \n to os.linesep
        		f.close()

        		time.sleep(55)
		else:
			if(datetime.datetime.now().strftime("%H") > currenthour):
				currenthour = datetime.datetime.now().strftime("%H")
				f = open('./monthly_results/grnhouse' + time.strftime('%B') + '.csv','a')
        			f.write(str(now) + ','+ str(ght) + ',' + str(wtt) + ',' + str(spt) + ',' + str(wst) + ',' + str(GPIO.input(pump)) + '\n')  #Give your csv text here.
        			## Python will convert \n to os.linesep
        			f.close()
					
					
					
# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        process_loop()
    except KeyboardInterrupt:
        # tell the user what we're doing...
        # turn off all of the relays
        GPIO.output(stove_valve,0)
        GPIO.output(pump,0)
        GPIO.output(floor_valve,0)
        print("\nExiting application")
        
        print("all relays off ")
        # turn off all of the relays

        # exit the application
        sys.exit(0)

