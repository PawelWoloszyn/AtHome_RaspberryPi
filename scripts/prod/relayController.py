import RPi.GPIO as GPIO
import requests
import xml.etree.ElementTree as ET
import datetime
import time
import os
import logging
import databaseConnector as dc


#setup GPIO pins
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(11, GPIO.OUT)
RELAY_ON = False
RELAY_OFF = True
GPIO_PIN_NUMBER = 11
GPIO.output(GPIO_PIN_NUMBER,RELAY_OFF)

#script sleeping time for every cycle in seconds
SLEEPING_TIME = 60

#create log directory
myLogDirectory = "/home/pi/centralne/scripts/prod/logs"
if not os.path.exists(myLogDirectory):
    os.makedirs(myLogDirectory)

#initialize logger
logger = logging.getLogger('factory')
fh = logging.FileHandler(myLogDirectory + '/relayController.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(funcName)s:%(lineno)d %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
#LOGGER DEBUG LEVEL!!!
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

logger.info("script was started")

fakemeasurement = '<root><Device Name="StecaGrid 3600" NominalPower="3680" Type="Inverter" Serial="751787CE006329160015" BusAddress="1" NetBiosName="INV006329160015" IpAddress="192.168.1.152" DateTime="2021-04-01T22:38:43"><Measurements><Measurement Value="238.9" Unit="V" Type="AC_Voltage"/><Measurement Unit="A" Type="AC_Current"/><Measurement Value="3000" Unit="W" Type="AC_Power"/><Measurement Value="50.088" Unit="Hz" Type="AC_Frequency"/><Measurement Value="0.1" Unit="V" Type="DC_Voltage"/><Measurement Unit="A" Type="DC_Current"/><Measurement Unit="°C" Type="Temp"/><Measurement Unit="W" Type="GridPower"/><Measurement Value="100.0" Unit="%" Type="Derating"/></Measurements></Device></root>'

class DbRecord:
  def __init__(self,id, powerTreshold, startDatetime,stopDatetime,isactive,executed):
      self.id = id
      self.powerTreshold = powerTreshold
      self.startDatetime = startDatetime
      self.stopDatetime = stopDatetime
      self.isactive = isactive
      self.executed = executed

def getData():
    r = requests.get('http://192.168.1.152/measurements.xml')
    if (r.status_code == 200):
        return r.text
    return None

def getPowerProduction(xmlString):
    root = ET.fromstring(xmlString)
    searchedElement = root[0][0][2]
    if searchedElement.attrib['Type'] == "AC_Power":
        if searchedElement.get("Value") is None:
            # there is not power attribute so the power production is currently 0
            logger.debug("The power is 0")
            return 0
        else:
            # There is some power production, check if it is sufficient
            return float(searchedElement.get("Value"))
    return None

def turnRelaysON():
    logger.debug("Relay is turned ON")
    GPIO.output(GPIO_PIN_NUMBER,RELAY_ON)

def turnRelaysOFF():
    logger.debug("Relay is turned OFF")
    GPIO.output(GPIO_PIN_NUMBER,RELAY_OFF)

def updateRelayState(operationResult):
    if operationResult:
        turnRelaysON()
    else:
        turnRelaysOFF()

###MYSQL
def updateAsExecuted(id):
    query = "UPDATE relayjobs_new SET executed = 1, executionStop = NOW() WHERE id = " + str(id)
    dc.executeQuerryInDB(query,False,logger)

def updateAsActive(id):
    query = "UPDATE relayjobs_new SET isactive = 1, executionStart = NOW() WHERE id = " + str(id)
    dc.executeQuerryInDB(query,False,logger)

def updateWorkingTime(id):
    query = "UPDATE relayjobs_new SET workingTime = workingTime +" + str(SLEEPING_TIME) + " WHERE ID = " + str(id)
    dc.executeQuerryInDB(query,False,logger)

def getJobList():
    query = "SELECT id,powerTreshold,startDatetime,stopDatetime,isactive,executed FROM relayjobs_new WHERE executed IS NULL AND canceled IS NULL"
    return dc.executeQuerryInDB(query,True,logger)

if __name__ == '__main__':
    while True:
        eventList = []
        logger.debug("beginning of while loop")
        fetchResult = getJobList()
        for row in fetchResult:
            eventList.append(DbRecord(int(row[0]), int(row[1]), row[2], row[3], bool(row[4]), bool(row[5])))

        #logger.debug("all items from eventlist:")
        if eventList:
            for item in eventList:
                logger.debug(item.startDatetime)

        operationResult = False #<-- this variable will determine state of GPIO pin, the last change in the list will affect what is gonna happen
        turnOnOperationId = None #This variable tells which job ID turned the operation to True

        powerProdValue = None

        if eventList:
            for item in eventList:
                #first check the times...
                currentMillis = datetime.datetime.now().timestamp() * 1000
                startMillis = item.startDatetime.timestamp() * 1000
                stopMillis = item.stopDatetime.timestamp() * 1000
                #check only jobs that fit preset timestamp
                if startMillis < currentMillis < stopMillis:
                    logger.debug("We have work to do for record id:" + str(item.id))
                    #job where there is no power treshold
                    if item.powerTreshold == -1:
                        #there is no rule for power, the relays should be ON
                        if not item.isactive:
                            logger.info("Activating the relays without power treshold rule job ID: " + str(item.id))
                            updateAsActive(item.id)
                        operationResult = True
                    #job with power treshold
                    elif item.powerTreshold > -1:
                        if powerProdValue is None:
                            #get the power readings
                            powerProdValue = getPowerProduction(getData())
                        if (powerProdValue is not None) and (item.powerTreshold <= powerProdValue):
                            if not item.isactive:
                                updateAsActive(item.id)
                                logger.info("Activating the relays with power treshold rule = " + str(item.powerTreshold) +" job ID: " + str(item.id))
                            logger.debug("Power treshold was exceeded, turning on relays")
                            operationResult = True
                        elif (powerProdValue is not None) and (item.powerTreshold > powerProdValue):
                            logger.debug("Power treshold was NOT exceeded, turning off relays")
                            operationResult = False
                        else:
                            #notify the logger that something went wrong...
                            logger.error("Something went wrong while getting the power values for job ID: "+ str(item.id))

                # CHECK IF THERE ARE RECORDS WHICH FINISHED AND THEREFORE SHALL BE CLOSED
                if currentMillis > stopMillis:
                    if not item.executed:
                        logger.info("The relays shall be turned off because command execution time finished for id:" + str(item.id))
                        updateAsExecuted(item.id)
                        operationResult = False
                turnOnOperationId = item.id
                #if event list is empty check if the GPIO is off same if it is not empty but there are no tasks
        else:
            logger.debug("eventlist is empty")
            #make sure that relay is off...
        updateRelayState(operationResult)
        #update working time for job that caused turning heater ON
        if(operationResult):
            updateWorkingTime(turnOnOperationId)
        logger.debug("=================================Putting script to sleep")
        time.sleep(SLEEPING_TIME)
