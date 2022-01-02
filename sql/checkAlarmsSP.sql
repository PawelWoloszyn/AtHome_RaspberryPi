USE `centralne`;
DROP procedure IF EXISTS `checkAlarmJobs`;

USE `centralne`;
DROP procedure IF EXISTS `centralne`.`checkAlarmJobs`;
;

DELIMITER $$
USE `centralne`$$
CREATE DEFINER=`foo`@`localhost` PROCEDURE `checkAlarmJobs`()
BEGIN
-- VARIABLES 
DECLARE dbUserID INT;
DECLARE jobID INT;
DECLARE telegramID VARCHAR(30);
DECLARE temperature DECIMAL(8,2);
DECLARE sensor VARCHAR(30);
DECLARE alarmCond VARCHAR(2);
DECLARE condResetCount INT;

-- temperature values

DECLARE piecTemp DECIMAL;
DECLARE dworTemp DECIMAL;
DECLARE currentTemperature DECIMAL;


DECLARE done INT DEFAULT FALSE;

DECLARE temperatureAlarmList CURSOR FOR 
SELECT tusers.id AS dbUserID, aConfig.id AS jobID , tusers.telegramID, 
aConfig.temperature, aConfig.sensor, aConfig.alarmCond, aConfig.condResetCount
FROM telegramAlarmConfig as aConfig
INNER JOIN telegramUsers as tusers
ON tusers.id = aConfig.dbUserID
WHERE tusers.notificationMute != 1 AND aConfig.isActive = 1
AND aConfig.timeFrom <= CURTIME() AND aConfig.timeTo >= CURTIME();

DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

SET piecTemp = (SELECT ovenTmp FROM temperatures ORDER BY ID DESC LIMIT 1);
SET dworTemp= (SELECT outdoorTmp FROM temperatures ORDER BY ID DESC LIMIT 1);

OPEN temperatureAlarmList;

check_loop: LOOP
	FETCH temperatureAlarmList INTO dbUserID, jobID, telegramID, temperature ,sensor, alarmCond, condResetCount;
	IF done THEN
      LEAVE check_loop;
    END IF;
    
    IF sensor = 'piec' THEN
		SET currentTemperature = piecTemp;
	ELSEIF sensor = 'dwor' THEN
		SET currentTemperature = dworTemp;
    END IF;
    
	IF alarmCond = '>' AND currentTemperature > temperature AND condResetCount = 0 THEN
		-- add new notification
        INSERT INTO telegramNotifications(addDate,alarmJobId, userTelegramID,message)
        VALUES(NOW(),jobID,telegramID, 
        CONCAT('[ALARM] temperatura na: ', sensor, ' jest ', alarmCond, temperature, ' stopni'));
		-- set new condResetCount
		UPDATE telegramAlarmConfig SET condResetCount = 2 WHERE id = jobID;
	ELSEIF alarmCond = '<' AND currentTemperature < temperature AND condResetCount =0 THEN
		-- add new notification
        INSERT INTO telegramNotifications(addDate,alarmJobId, userTelegramID,message)
        VALUES(NOW(),jobID,telegramID, 
        CONCAT('[ALARM] temperatura na: ', sensor, ' jest ', alarmCond, temperature, ' stopni'));
		-- set new condResetCount
		UPDATE telegramAlarmConfig SET condResetCount = 2 WHERE id = jobID;
	ELSEIF condResetCount !=0 AND alarmCond = '<' AND currentTemperature > temperature THEN
		UPDATE telegramAlarmConfig SET condResetCount = condResetCount - 1 WHERE id = jobID;
    ELSEIF condResetCount !=0 AND alarmCond = '>' AND currentTemperature < temperature THEN
		UPDATE telegramAlarmConfig SET condResetCount = condResetCount - 1 WHERE id = jobID;
    END IF;
    
    -- UPDATE ALL currenclty INACTIVE alarms, SET their condResetCount to 0
    UPDATE telegramAlarmConfig SET condResetCount = 0 WHERE isActive = 0 OR
    timeFrom > CURTIME() OR timeTo < CURTIME();
    
END LOOP;
END$$

DELIMITER ;
;

