from functools import wraps
import CREDENTIALS as keys
from telegram.ext import *
import logging
import databaseConnector as dc
import time
import os
import re
import DS18B20Handler

#initialize logger
if not os.path.exists("logs"):
    os.makedirs("logs")

myLogDirectory = "/home/pi/centralne/scripts/prod/logs"

logger = logging.getLogger("factory")
fh = logging.FileHandler(myLogDirectory + "/telegramHandler.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(funcName)s:%(lineno)d %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

logger.info("script started")

#global variables
userList = []
adminList = []

#function wrappers
def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in userList:
            logger.warning("Unauthorized user access denied for {}.".format(user_id))
            return
        #because after script restart Telegram will only lauch it's jobs after users
        #interaction it has to be monitored by checkTelegramDispatcher
        checkTelegramDispatcher(update, context)
        return func(update, context, *args, **kwargs)
    return wrapped

#error handlers
def errorHandler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

#functions

def validateAlarmData(update, context ,sensor, condition, temperature, timeFrom = None, timeTo = None):
    #check passed values
    if sensor.lower() not in ('piec','dwor','dwór'):
        update.message.reply_text('bledna nazwa czujnika')
        return
    if condition not in ('<','>'):
        update.message.reply_text('bledny warunek, dozwolone "<" lub ">"')
        return
    if not temperature.isnumeric():
        update.message.reply_text('bledna temperatura')
        return
    pattern = re.compile("^([0-1]?[0-9]|2?[0-4]):[0-5][0-9](:[0-5][0-9])?$")
    if timeFrom is not None and not pattern.match(timeFrom):
        update.message.reply_text('blednie podana godzina od')
        return
    if timeTo is not None and not pattern.match(timeTo):
        update.message.reply_text('blednie podana godzina do')
        return
    return(getAlarmInsertQuerry(update, context, sensor, condition, temperature, timeFrom, timeTo))

def getAlarmInsertQuerry(update, context, sensor, condition, temperature, timeFrom = None, timeTo = None):
    if timeTo is not None and timeFrom is not None:
        # update.effective_user.id
        return f"INSERT INTO centralne.telegramAlarmConfig (dbUserID,sensor,alarmCond,temperature,timeFrom,timeTo) VALUES((SELECT id FROM centralne.telegramUsers WHERE telegramID = '{getUserId(update, context)}' LIMIT 1),'{sensor}', '{condition.lower()}', {temperature}, '{timeFrom}', '{timeTo}');"
    else:
        return f"INSERT INTO centralne.telegramAlarmConfig (dbUserID,sensor,alarmCond,temperature,timeFrom,timeTo) VALUES((SELECT id FROM centralne.telegramUsers WHERE telegramID = '{getUserId(update, context)}' LIMIT 1),'{sensor}', '{condition.lower()}', {temperature}, '00:00:00', '23:59:59');"

def checkTelegramDispatcher(update,context):
    if not context.job_queue.get_jobs_by_name(getMyJobName(update, context)):
        logger.info(f"Job did not exist for user id:{getUserId(update,context)}, starting now...")
        context.job_queue.run_repeating(checkMyNotifications, 30, context=update.message.chat_id, name=getMyJobName(update, context))

def checkMyNotifications(context):
    # logger.debug("checking telegram list...")
    userId = str(context.job_queue.jobs()[0].name).replace("_job","")
    #get the jobs
    query = f"SELECT id, message FROM centralne.telegramNotifications WHERE executedDate IS NULL AND userTelegramID = '{userId}';"
    notifications = dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=True,logger=logger)

    dispatchedNotifications = []

    for notification in notifications:
        context.bot.send_message(chat_id=userId, text=notification[1])
        logger.info(f"Notification {notification[0]} was dispatched to user: {userId}")
        dispatchedNotifications.append(notification[0])
    #inform DB that notifications were already dispatched
    if dispatchedNotifications:
        dispatchedNotifications = str(dispatchedNotifications).replace("[","").replace("]","")
        query = f"UPDATE centralne.telegramNotifications SET executedDate = NOW() WHERE id IN ({str(dispatchedNotifications)});"
        logger.info(f"executing query:{query}")
        dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=False,logger=logger)


#naming functions
def getUserId(update, context):
    return str(update.effective_user.id)

def getMyJobName(update,context):
    return getUserId(update,context) + '_job'


#handlers

@restricted
def addTelegramAlarmConfig(update, context):
    result = None
    if len(context.args) == 5:
        result = validateAlarmData(update, context ,sensor=context.args[0], condition=context.args[1], temperature=context.args[2], timeFrom =context.args[3], timeTo =context.args[4])
    elif len(context.args) == 3:
        result = validateAlarmData(update, context ,sensor=context.args[0], condition=context.args[1], temperature=context.args[2])
    else:
        update.message.reply_text('podano zbyt malo argumentow')
    if result:
        logger.info(f"new query execution {result}")
        dc.executeQuerryInDB(sqlQuerry=result,isSelectQuery=False,logger=logger)
        update.message.reply_text('Dodano nowy alarm do listy')

@restricted
def getMyAlarmList(update, context):
    query = f"SELECT id, sensor, alarmCond, temperature, timeFrom, timeTo, isActive FROM centralne.telegramAlarmConfig WHERE dbUserID = (SELECT id FROM centralne.telegramUsers WHERE telegramID = {getUserId(update, context)});"
    alarmList = dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=True,logger=logger)
    #transform list to readable format
    readableAlarmList = []
    if alarmList:
        for row in alarmList:
            readableRecord = ''
            readableRecord += f'nr {row[0]}'
            readableRecord += f'\t{row[1]}'
            readableRecord += f' {row[2]}'
            readableRecord += f' {row[3]} stopni c,'
            readableRecord += f' godz od:{str(row[4])}'
            readableRecord += f' godz do:{str(row[5])}'
            status = "aktywny" if row[6] == 1 else "nieaktywny"
            readableRecord += f' {status}'
            readableAlarmList.append(readableRecord)
        myMessage = ""
        for rr in readableAlarmList:
            myMessage += rr + "\n"
        logger.debug(myMessage)
        update.message.reply_text(myMessage)
    else:
        update.message.reply_text("Nie masz żadnych alarmów")

@restricted
def removeAlarmJob(update, context):
    if len(context.args) ==1:
        if context.args[0].isnumeric():
            query = f"DELETE FROM centralne.telegramAlarmConfig WHERE dbUserID = (SELECT id FROM centralne.telegramUsers WHERE telegramID = {getUserId(update, context)}) AND id = {context.args[0]};"
            dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=False,logger=logger)
            update.message.reply_text(f"id {context.args[0]} zostało usunięte (jeżeli jesteś jego właścicielem) wpisz /al by się upewnić")
    else:
        update.message.reply_text("Podaj numer alarmu np. /rm 23")


@restricted
def pauseAlarmJob(update, context):
    if len(context.args) ==1:
        if context.args[0].isnumeric():
            query = f"UPDATE centralne.telegramAlarmConfig SET isActive = 0 WHERE dbUserID = (SELECT id FROM centralne.telegramUsers WHERE telegramID = {getUserId(update, context)}) AND id = {context.args[0]};"
            dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=False,logger=logger)
            update.message.reply_text(f"id {context.args[0]} zostało zapauzowane (jeżeli jesteś jego właścicielem) wpisz /al by się upewnić")
    else:
        update.message.reply_text("Podaj numer alarmu np. /pa 22")

@restricted
def resumeAlarmJob(update, context):
    if len(context.args) ==1:
        if context.args[0].isnumeric():
            query = f"UPDATE centralne.telegramAlarmConfig SET isActive = 1 WHERE dbUserID = (SELECT id FROM centralne.telegramUsers WHERE telegramID = {getUserId(update, context)}) AND id = {context.args[0]};"
            dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=False,logger=logger)
            update.message.reply_text(f"id {context.args[0]} zostało odpauzowane (jeżeli jesteś jego właścicielem) wpisz /al by się upewnić")
    else:
        update.message.reply_text("Podaj numer alarmu np. /ra 3")


@restricted
def silenceAllMyNotifications(update, context):
    if len(context.args) ==1 and context.args[0].lower() in ("on","off"):
        query =""
        if context.args[0].lower() == "on":
            query = f"UPDATE centralne.telegramUsers SET notificationMute = 1 WHERE telegramID =  {getUserId(update, context)};"
            update.message.reply_text(f"wyciszenie zmieniono na: ON")
        elif context.args[0].lower() == "off":
            query = f"UPDATE centralne.telegramUsers SET notificationMute = 0 WHERE telegramID = {getUserId(update, context)};"
            update.message.reply_text(f"wyciszenie zmieniono na: OFF")

        dc.executeQuerryInDB(sqlQuerry=query,isSelectQuery=False,logger=logger)
    else:
        update.message.reply_text("Błąd, użyj np. /silence on")

@restricted
def getCurrentTemperatures(update, context):
    temps = DS18B20Handler.getSensorReadings();
    logger.info(f"Temperatures were requestes by userid: {getUserId(update,context)}")
    update.message.reply_text("piec: {:.2f} dwor: {:.2f}".format(temps[1],temps[0]))

@restricted
def getArchivalTemperatures(update, context):
    temps = dc.executeQuerryInDB(sqlQuerry="SELECT ovenTmp, evtDate FROM centralne.temperatures ORDER BY id DESC LIMIT 10;",isSelectQuery=True,logger=logger)
    #reverse to get backward order
    temps = tuple(reversed(temps))
    retString = 'piec:\n'
    retString+=str(temps[0][1])
    retString+='\n'
    for row in temps:
        retString+=(f'{row[0]}\n')
    retString+=str(temps[len(temps)-1][1])
    retString+='\n'
    logger.debug(f"Your temps: {retString}")
    update.message.reply_text(retString)

@restricted
def commandHelp(update, context):
    COMMAND_LIST = "/t - obecne temperatury\n/ta - temperatury historyczne\n/ca - dodaj nowy alarm np. /ca piec > 90 08:00 22:00\n /rm - usuń alarm np. /rm 2\n/al - wyświetl listę alarmów\n/pa - wycisz pojedynczy alarm np. /pa 11 \n/ra - odpauzuj pojedynczy alarm np. /ra 11 \n/silence on - wycisz wszystkie swoje alarmy\n/silence off - wyłącz wyciszenie wszystkich swoich alarmów"
    update.message.reply_text(COMMAND_LIST)

if __name__ == '__main__':
    #get list of allowed user ids from database
    row = None
    while row is None:
        row = dc.executeQuerryInDB(sqlQuerry="SELECT telegramID, isAdmin FROM telegramUsers;",isSelectQuery=True,logger=logger)
        if row is None:
            logger.warning("Could not get list of users from DB, retrying in 5 seconds")
            time.sleep(5)

    logger.debug("content brought back: " + str(row))
    if row:
        for e in row:
            userList.append(e[0])
            if e[1] == 1:
                adminList.append(e[0])

    logger.debug("user list: " + str(userList))
    time.sleep(2)

    updater = Updater(keys.API_KEY , use_context= True)
    dp = updater.dispatcher

    #AVAILABLE COMMANDS
    dp.add_handler(CommandHandler("t", getCurrentTemperatures))
    dp.add_handler(CommandHandler("ta", getArchivalTemperatures))
    dp.add_handler(CommandHandler("ca", addTelegramAlarmConfig))
    dp.add_handler(CommandHandler("rm", removeAlarmJob))
    dp.add_handler(CommandHandler("al", getMyAlarmList))
    dp.add_handler(CommandHandler("pa", pauseAlarmJob))
    dp.add_handler(CommandHandler("ra", resumeAlarmJob))
    dp.add_handler(CommandHandler("silence", silenceAllMyNotifications))
    dp.add_handler(CommandHandler("start", commandHelp))

    dp.add_error_handler(errorHandler)
    updater.start_polling(2)
    updater.idle()


#KNOWN ISSUES
    #it's not possible to add alarms with negative temperature

    #After raspberry pi reboot/failure = script restart alarms will not work
    #until user makes interraction with bot, checkTelegramDispatcher was implemented
    #to miltigate this problem

    #db logging for removed alarms needs to be added

