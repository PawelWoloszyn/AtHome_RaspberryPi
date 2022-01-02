from w1thermsensor import W1ThermSensor, Sensor
#DEFINE DS18B20 sensors
outdoorSensor = W1ThermSensor(Sensor.DS18B20, "0417619afcff")
ovenSensor = W1ThermSensor(Sensor.DS18B20, "041761a251ff")

def getSensorReadings():
    # read the temperatures from DS18B20 here
    return outdoorSensor.get_temperature(), ovenSensor.get_temperature() + 5.0
