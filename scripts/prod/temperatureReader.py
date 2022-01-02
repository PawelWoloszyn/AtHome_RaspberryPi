#!/usr/bin/python3
import time
import logging
import os
from datetime import datetime
import databaseConnector as dc
import DS18B20Handler

#create log directory
myLogDirectory = "/home/pi/centralne/scripts/prod/logs"
if not os.path.exists(myLogDirectory):
    os.makedirs(myLogDirectory)

#initialize logger
logger = logging.getLogger('factory')
fh = logging.FileHandler(myLogDirectory + '/temperatureReader.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(funcName)s:%(lineno)d %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("script was started")

if __name__ == '__main__':\
    #get refresh rate from DB
    row = None
    while row is None:
        row = dc.executeQuerryInDB(sqlQuerry="SELECT value FROM globalParameters WHERE name = \"tmpRefreshTime\" LIMIT 1",isSelectQuery=True,logger=logger)
        if row is None:
            logger.warning("Could not get the refresh time from DB, retrying in 5 seconds...")
            time.sleep(5)
    sleepTime = int(row[0][0])
    time.sleep(2)
    while True:
        currentOutdoorTemp, currentOvenTemp = DS18B20Handler.getSensorReadings()
        dc.executeQuerryInDB(sqlQuerry="INSERT INTO temperatures (evtDate, outdoorTmp, ovenTmp)  VALUES (NOW(), %.2f, %.2f)" % (currentOutdoorTemp, currentOvenTemp),isSelectQuery=False,logger=logger)
        now = datetime.now()
        logger.debug("Putting script to sleep for: %s seconds" % sleepTime)
        #put infinite loop to sleep
        time.sleep(sleepTime)
