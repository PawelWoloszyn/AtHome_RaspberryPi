-- CREATE TABLE relayjobs (id INT NOT NULL AUTO_INCREMENT, addDate DATETIME,
-- addDevice NVARCHAR(30),powerTreshold INT, startDatetime DATETIME,
-- stopDatetime DATETIME, executed BOOLEAN,isactive BOOLEAN,canceled BOOLEAN,
-- executionStart DATETIME, executionStop DATETIME,PRIMARY KEY(id));
-- --INDEX(active)
USE centralne;
DROP TABLE IF EXISTS telegramUsers;

CREATE TABLE telegramUsers (id INT NOT NULL AUTO_INCREMENT, addDate DATETIME DEFAULT NOW(),
telegramID NVARCHAR(30) NOT NULL, isAdmin BOOLEAN, name NVARCHAR(60), notificationMute BOOLEAN DEFAULT 0
,PRIMARY KEY(id,telegramID));

DROP TABLE IF EXISTS telegramCustomTempRead;

-- CREATE TABLE telegramCustomTempRead (id INT NOT NULL AUTO_INCREMENT, addDate DATETIME,
--  userID NVARCHAR(30) NOT NULL, executedDate DATETIME ,PRIMARY KEY(id,executedDate));

 DROP TABLE IF EXISTS telegramAlarmConfig;

CREATE TABLE telegramAlarmConfig (id INT NOT NULL AUTO_INCREMENT, addDate DATETIME DEFAULT NOW(),
dbUserID INT NOT NULL, isActive BOOLEAN DEFAULT 1,  sensor NVARCHAR(20) DEFAULT 'piec',
alarmCond NVARCHAR(1) NOT NULL DEFAULT '>', temperature INT NOT NULL,
condResetCount INT NOT NULL DEFAULT 0,timeFrom TIME,timeTo TIME,PRIMARY KEY(id,dbUserID));

 DROP TABLE IF EXISTS telegramNotifications;

CREATE TABLE telegramNotifications (id INT NOT NULL AUTO_INCREMENT, addDate DATETIME DEFAULT NOW(), alarmJobId INT NOT NULL,
userTelegramID NVARCHAR(30) NOT NULL, executedDate DATETIME , PRIMARY KEY(id), message NVARCHAR(200));
