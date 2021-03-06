
import os
import datetime
from pytz import timezone
import time
import RPi.GPIO as io
import json,httplib
import threading
from threading import Thread

#io.cleanup()
io.setmode(io.BCM)
io.setwarnings(False)

pir_pin = 18
doorbell_pin = 23 
buzzer_pin = 21 
door_pin = 24 

doCapture = True
lastUpdated  = ""

io.setup(pir_pin, io.IN) # activate input
io.setup(doorbell_pin, io.IN, pull_up_down=io.PUD_UP) # activate input with PullUp, doorbell is off
io.setup(buzzer_pin,io.OUT)
io.setup(door_pin,io.OUT)

notifyLock = threading.Lock()

def notifyUser(imgName):
  notifyLock.acquire()
  global doCapture
  if not doCapture:
    return 
  try:
    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request('POST', '/1/files/visitor.jpg', open('../images/'+imgName+'.jpeg', 'rb').read(), {
         "X-Parse-Application-Id": "g6riYDc21ziBVBHWXxLbMot7KVBMg1kdFm9xqU27",
         "X-Parse-REST-API-Key": "2p6UlYYu1bFRBE3nHgHvLl22vhbOSyVH5BSDH8Tr",
         "Content-Type": "image/jpeg"
       })
    result = json.loads(connection.getresponse().read())


    picAddr = result.get("name")

    connection.request('POST', '/1/classes/Images', json.dumps({
           "name": imgName,
           "picture": {
       "name": picAddr,
      "__type": "File"
           }
        }), {
           "X-Parse-Application-Id": "g6riYDc21ziBVBHWXxLbMot7KVBMg1kdFm9xqU27",
          "X-Parse-REST-API-Key": "2p6UlYYu1bFRBE3nHgHvLl22vhbOSyVH5BSDH8Tr",
          "Content-Type": "application/json"
        })
    result = json.loads(connection.getresponse().read())
    connection.request('POST', '/1/functions/sendPush2Mbl', json.dumps({ }), {
         "X-Parse-Application-Id": "g6riYDc21ziBVBHWXxLbMot7KVBMg1kdFm9xqU27",
         "X-Parse-REST-API-Key": "2p6UlYYu1bFRBE3nHgHvLl22vhbOSyVH5BSDH8Tr",
         "Content-Type": "application/json"
       })
    result = json.loads(connection.getresponse().read())
    print "Notified...."
    doCapture = False
  finally:
    notifyLock.release()

def getCommand():
  global lastUpdated
  connection = httplib.HTTPSConnection('api.parse.com', 443)
  connection.connect()

  connection.request('GET', '/1/classes/Commands', '', {"X-Parse-Application-Id": "g6riYDc21ziBVBHWXxLbMot7KVBMg1kdFm9xqU27","X-Parse-REST-API-Key": "2p6UlYYu1bFRBE3nHgHvLl22vhbOSyVH5BSDH8Tr"})
  result = json.loads(connection.getresponse().read()).get("results")[0]  
  if result.get("updatedAt")==lastUpdated:
    return -1
  else:
    lastUpdated = result.get("updatedAt")
  
  if result.get("alarm"):
    return 1
  elif result.get("camera"):
    return 2
  elif result.get("door"):
    return 3


camLock = threading.Lock()
def captureVisitor(imgName):
  camLock.acquire()
  try:
    os.system("fswebcam -p YUYV -d /dev/video0 -r 720x480 ../images/%s.jpeg > /dev/null 2>&1" %imgName)
    print "Image Captured"
  finally:
    camLock.release()

def morsecode():
  for i in range(1,5):
    io.output(21,io.HIGH)
    time.sleep(1)
    io.output(21,io.LOW)
    time.sleep(1)

def opendoor():
  io.output(24,io.HIGH)
  time.sleep(5)
  io.output(24,io.LOW)

def executeCommand(cmd):
  if cmd==1:
    morsecode()
  elif cmd==2:
    print "User requested for an image capture...."
    imgName = datetime.datetime.now(timezone('US/Pacific')).strftime("%m-%d-%Y-%H:%M:%S")
    captureVisitor(imgName)
    global doCapture
    doCapture = True
    print "Notifying User...."
    notifyUser(imgName)
    time.sleep(5)
    doCapture = True
  elif cmd==3:
    opendoor()

def doorThread():
  global doCapture
  j=0
  while True:
      if not io.input(doorbell_pin) and doCapture:    # if doorbell is on
          j = j+1
          print "Doorbell pressed...",j
          imgName = datetime.datetime.now(timezone('US/Pacific')).strftime("%m-%d-%Y-%H:%M:%S")
          captureVisitor(imgName)
          print "Notifying User..."
          notifyUser(imgName)

def pirThread():
  global doCapture
  i=0
  inField = 0
  time.sleep(30)
  while True:
    if io.input(pir_pin):
      i = i+1
      print "Person Entered...",inField
      imgName = datetime.datetime.now(timezone('US/Pacific')).strftime("%m-%d-%Y-%H:%M:%S")
      captureVisitor(imgName)
      print "pir status",io.input(pir_pin)
      while io.input(pir_pin): 
        inField += 1
        print "in pir loop",inField
        time.sleep(1)
      print "Person went out of field....."
      if inField>1:
        print "Notifying User..."
        notifyUser(imgName)
      else:
        os.system("rm -f ../images/%s.jpeg" %imgName)
      
      doCapture = True

def listenForCommand():
  getCommand()
  while True:
    cmd = getCommand()
    if cmd>-1:
      executeCommand(cmd)
  
def main():
  thread1 = Thread(target = pirThread,args=[])
  thread2 = Thread(target = doorThread,args=[])
  thread3 = Thread(target = listenForCommand,args=[])
  
  thread1.start()
  thread2.start()
  thread3.start()

  thread1.join()
  thread2.join()
  thread3.join()

if __name__=='__main__':
  main()
