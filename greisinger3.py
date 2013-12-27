#! /usr/bin/env python

import sys, time
from serial import *
from os import path
#from subprocess import *


# plugget
# extrapixel 2008
# GPL License

ser = None
connectionOK = False
lastConnectionTry = 0
lastSensorRead = 0;

SERIAL_PORT = "/dev/cu.usbserial"

FILENAME_PH = "ph"
FILENAME_TEMP = "temperatur"
FILENAME_EXT = ".txt"
FILEPATH = "/Users/whiteboxes/Desktop/phlog/"

PH_QUESTION = chr(254) + chr(0) + chr(61);
TEMP_QUESTION = chr(253) + chr(0) + chr(2);
	
# errors vom GMH
ERROR_RANGE = -1	# Messbereichsunter- / -ueberschreitung
ERROR_CALC = -2		# Berechnung nicht moeglich
ERROR_SYSTEM = -3	# Systemfehler
ERROR_BATTERY = -4	# Batterie leer
ERROR_SENSOR = -5	# Sensor defekt
#kommunikations-errors
ERROR_NOANSWER = -6	# das geraet scheint verbunden, aber es gibt keine antwort
	
RECONNECT_EVERY = 5
COLLECT_EVERY = 60

def main():
	
	global connectionOK, lastConnectionTry, lastSensorRead
	lastConnectionTry = time.time() - RECONNECT_EVERY
	lastSensorRead = time.time() - COLLECT_EVERY
	

	# main loop
	while True:
	
		if (connectionOK):
		
			# pruefen, ob wir schon die sensor-daten abrufen muessen
			if (time.time()-lastSensorRead > COLLECT_EVERY):
				ph_messwert = getTempPH(PH_QUESTION)
				temp_messwert = getTempPH(TEMP_QUESTION)
				if ph_messwert:
					print "ph: " + str(ph_messwert)
				if temp_messwert:
					print "temp: " + str(temp_messwert)
				lastSensorRead = time.time()
				
				saveToFile(ph_messwert, temp_messwert)
				
		else:
			#es besteht noch keine verbindung
		
			# pruefen, ob wir schon wieder versuchen sollen, neu zu verbinden
			if (time.time()-lastConnectionTry > RECONNECT_EVERY):
				connectionOK = connect()

# speichert die uerbergebenen sensor-messdaten
# in das zugehoerige file. fuer jeden tag wird 
# ein neues file erstellt. 
def saveToFile(ph, temp):
	filenameDate = time.strftime("_%Y_%m_%d", time.localtime())
	logDate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
	
	#ph log file
	if ph:
		ph_file_path = path.join(FILEPATH, FILENAME_PH , FILENAME_PH + filenameDate + FILENAME_EXT)
		ph_file = open ( ph_file_path, 'a+' )
		ph_file.write ( logDate + ',' + str(ph) + '\n' )
		ph_file.close()
	
	# temperatur log file
	if temp:
		temp_file_path = path.join(FILEPATH, FILENAME_TEMP, FILENAME_TEMP + filenameDate + FILENAME_EXT)
		temp_file = open ( temp_file_path, 'a+' )
		temp_file.write ( logDate + ',' + str(temp) + '\n' )
		temp_file.close() 


			
				
# fragt einen sensor vom GSH ab
# der message-parameter ist ein string mit 3 bytes,
# gemaess der EasyBus-Schnittstellen definition
def getTempPH(message):
	global ser
	global connectionOK
	
	# emtpy buffer in case there's something...
	try:
		while ser.read():
			pass
	except SerialException as e:
		print "problem with serial: " + str(e)
		connectionOK = False
		return None
				
	try:
		ser.write(message)
	except SerialException:
		print "problem with serial: " + str(e)
		connectionOK = False
		return None
	
	#versuchen, die 6-byte antwort zu lesen
	decodedAnswer = None
	try:
		answer = ser.read(6)
		decodedAnswer = decodeAnswer(answer)
	except SerialException:
		print "problem with serial: " + str(e)
		connectionOK = False
		return None
		
	except Exception as e:
		print e
	
	
	return decodedAnswer

# decodiert die antwort-bytes in einen float-wert
# rueckgaben <0 sind fehler
def decodeAnswer(answer):
	answerList = list(answer)
	#print answerList
	if len(answerList)==6:
		#print str(answer)
		lowByte = ord(answerList[4])
		highByte = ord(answerList[3])
		#print lowByte
	
	

		gesperrterBereichMin = 0x3EB1
		gesperrterBereichMax = 0x3FFF
	
		codierteDaten = highByte^0xFF
		codierteDaten = codierteDaten << 8
		codierteDaten = codierteDaten | lowByte
		codierteDaten = codierteDaten & 0x3FFF
		dezimalpunkt = (highByte^0xFF)>>6
	
	
		if (codierteDaten>=gesperrterBereichMin and codierteDaten<=gesperrterBereichMax):
			print "error, kein gueltiger messwert!";
			return ERROR_RANGE
		else:
			codierteDaten = codierteDaten-0x0800; 

			messwert = -1.0;

			if (dezimalpunkt == 0):
				messwert = codierteDaten;
			elif (dezimalpunkt == 1):
				messwert = codierteDaten/10.0;
			elif (dezimalpunkt == 2):
				messwert = codierteDaten/100.0;
			elif (dezimalpunkt == 3):
				messwert = codierteDaten/1000.0;
			
			#print "! messwert: " + str(messwert);
		return messwert
	else:
		print "invalid answer. should be 6 bytes, but is " + str(len(answerList))

		

# versucht eine connection mit dem GMH3530 aufzubauen
# gibt true zurueck wenn ok, sonst false
def connect():
	global lastConnectionTry, ser
	lastConnectionTry = time.time()

	try:
		ser = Serial(
    	port= SERIAL_PORT,              #number of device, numbering starts at
                            #zero. if everything fails, the user
                            #can specify a device string, note
                            #that this isn't portable anymore
                            #if no port is specified an unconfigured
                            #an closed serial port object is created
    	baudrate=4800,          #baudrate
    	bytesize=EIGHTBITS,     #number of databits
    	parity=PARITY_NONE,     #enable parity checking
    	stopbits=STOPBITS_ONE,  #number of stopbits
    	timeout=3,           #set a timeout value, None for waiting forever
    	xonxoff=0,              #enable software flow control
    	rtscts=0,               #enable RTS/CTS flow control
    	dsrdtr=0,
    	interCharTimeout=None,
    	writeTimeout=2
		)
		#ser.setDTR(1);
		ser.setRTS(0);
		return True
		
	except SerialException as e:
		print "problem with serial: " + str(e)
		return False
		
	except Exception as e:
		print "problem connecting: " + str(e)
		return False

if __name__ == '__main__':
     main()