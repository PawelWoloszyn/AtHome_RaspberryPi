
USE centralne;
DROP TRIGGER IF EXISTS check_alarms;

CREATE TRIGGER check_alarms AFTER INSERT ON temperatures FOR EACH ROW
CALL checkAlarmJobs();
