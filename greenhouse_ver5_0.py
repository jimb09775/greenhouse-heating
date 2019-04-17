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
        print('Processing current state:', str(self))

    def status(self, event):
        """
        Handle events that are delegated to this State.
        """
        pass

    def __repr__(self):
        """
        Leverages the __str__ method to describe the State.
        """
        return self.__str__()

    def __str__(self):
        """
        Returns the name of the State.
        """
        return self.__class__.__name__

# state transitions

class PumpOff(State):

    def __init__(self):
        print('Change of state ----', str(self))
        GPIO.output(stove_valve,0)
        GPIO.output(floor_valve,0)
        GPIO.output(pump,0)

    def status(self, event):
        print('Current state:', str(self))
        if event["TIME_OF_DAY"] and event["SP_GT_WT_OS"]:
            return PumpOnNoValves()
        if event["WT_GT_RT"]:
            return PumpOnFloorValve()
        return self


class PumpOnNoValves(State):

    def __init__(self):
        print('Change of state ----', str(self))
        GPIO.output(stove_valve,0)
        GPIO.output(floor_valve,1)
        GPIO.output(pump,1)
        print('Current state:', str(self), 'valve on', valve_on)
        self.time_to_kill_floor_valve = datetime.datetime.now() + datetime.timedelta(minutes = 1)

    def status(self, event):
        valve_on = datetime.datetime.now() < self.time_to_kill_floor_valve
        print('Current state:', str(self), 'valve on', valve_on)
        if valve_on:
            return self
        GPIO.output(floor_valve, 0)
        if not event["TIME_OF_DAY"] or not event["SP_GT_WT"]:
            return PumpOff()
        if event["STOVE_HOT"]:
            return PumpOnWoodStove()
        return self

class PumpOnWoodStove(State):
    
    def __init__(self):
        print('Change of state ----', str(self))
        GPIO.output(stove_valve,1)
        GPIO.output(floor_valve,0)
        GPIO.output(pump,1)

    def status(self, event):
        print('Current state:', str(self))
        if not event["STOVE_HOT"]:
            return PumpOff()
        return self

class PumpOnFloorValve(State):
    
    def __init__(self):
        print('Change of state ----', str(self))
        GPIO.output(stove_valve,0)
        GPIO.output(floor_valve,1)
        GPIO.output(pump,1)

    def status(self, event):
        print('Current state:', str(self))
        if not event["STOVE_HOT"]:
            return PumpOff()
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

    def status(self, event):
        """
        This is the bread and butter of the state machine. Incoming events are
        delegated to the given states which then handle the event. The result is
        then assigned as the new state.
        """

        # The next state will be the result of the status function.
        self.state = self.state.status(event)


def process_loop():

    time.sleep(1)
#   print("Stan says we are in ",__name__)
    fp=0
    sp=0
    stove_hot=0
    GPIO.output(stove_valve,0)
    GPIO.output(pump,0)
    GPIO.output(floor_valve,0)
    temp_offset = 12
    cold = 50

    mypump = Pump()

    # now cycle each relay every second in an infinite loop
    while True:
        
        wtt = read_temp(water_tank)
        spt = read_temp(solar_panel)
        wst = read_temp(wood_stove)
        ght = read_temp(room_temp)
        now = int(time.time())


        TIME_OF_DAY = int(datetime.datetime.now().strftime("%H"))>10 and int(datetime.datetime.now().strftime("%H"))<17
        STOVE_HOT = wst > cold
        WT_GT_RT = wtt > ght # water tank hotter than the room
        SP_GT_WT_OS = spt > wtt + temp_offset # solar panel greater than water temp plus offset
        SP_GT_WT = spt > wtt  # solar panel greater than water temp
        
        eventDict = {
            "TIME_OF_DAY": TIME_OF_DAY,
            "STOVE_HOT": STOVE_HOT,
            "WT_GT_RT": WT_GT_RT,
            "SP_GT_WT_OS": SP_GT_WT_OS,
            "SP_GT_WT": SP_GT_WT,
        }
        
        mypump.status(eventDict)

        
        print('room temperature is ',read_temp(room_temp), 'or in fahernheit',read_temp(room_temp)*9/5+32)
        print('Water Tank Temperature is ',wtt,'or in fahernheit',wtt*9/5+32)
        print('top of solar panel is ',spt,'or in fahernheit',spt*9/5+32)
        print('the wood stove is ',wst,'or in fahernheit',wst*9/5+32)
        print(datetime.datetime.now().strftime("%H"))

        if(GPIO.input(pump)==1):
        		f = open('./monthly_results/grnhse' + time.strftime('%B') + '.csv','a')
        		f.write(str(now) + ','+ str(ght) + ',' + str(wtt) + ',' + str(spt) + ',' + str(wst) + ',' + str(GPIO.input(pump)) + '\n') #Give your csv text here.
        		## Python will convert \n to os.linesep
        		f.close()

        		time.sleep(55)
        else:
        	if(datetime.datetime.now().minute == 0):
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

