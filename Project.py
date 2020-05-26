import RPi.GPIO as GPIO
from smbus import SMBus
import time

GPIO.setmode(GPIO.BCM)

# set up the bus on address 40 on I2C channel 1
address = 0x40
bus = SMBus(1)

# define pins
Trigger = 17
Echo = 18
Buzzer = 14

# set up pins
GPIO.setup(Trigger, GPIO.OUT)
GPIO.setup(Echo, GPIO.IN)
GPIO.setup(Buzzer, GPIO.OUT)

GPIO.output(Buzzer, GPIO.LOW)

#################################################################################################
# Critical variables                                                                            #
# Change these values to alter the behaviour of the program to your needs                       #
                                                                                                #
INPUT_DISTANCE = 40 # Max distance in which object is no longer detected (cm)                   #
INPUT_ACTIVATE_TIME = 10 # How long it takes to activate the buzzer (seconds)                   #
INPUT_BUZZER_ACTIVE_TIME = 20 # How long the buzzer active state lasts for (seconds)           #
INPUT_BUZZER_EXTENSION_TIME = 5 # How long the buzzer sounds after object disappears (seconds) #                 
                                                                                                #
#################################################################################################



# initalise variables
timerStarted = False
buzzerExtraTime = False
buzzerActiveState = False
objectDetected = False
activeStateIsSet = True
buzzerActiveStateFinish = 0
notificationTimer = 0
currentDetected = 0
totalDetected = 0
buzzerStop = 0
distance = 0

# define functions

# this function reads the distance from the SR04 and returns it
def getDistance():
    # variable used to ensure that execution will enter while loops
    counter = 0
    # trigger the SRO4 
    GPIO.output(Trigger, GPIO.HIGH)
    time.sleep(0.0001)
    GPIO.output(Trigger, GPIO.LOW)
    
    # get the start time
    while GPIO.input(Echo) == False or counter == 0:
        startTime = time.time()
        counter += 1
    
    # get the finishing time
    while GPIO.input(Echo) == True or counter == 1:
        finishTime = time.time()
        counter += 1
        
    # calculate the distance
    totalTime = finishTime - startTime
    distance = (totalTime * 34300) / 2
    
    return distance

# main logic which runs the system forever unless a keyboard interrupt occurs or the device loses power
try:
    while True:
        # get the distance
        distance = getDistance()

        # Prevent distance from being below 0
        if distance < 0:
            distance = 0
                
        # distinguish whether an object is detected or not
        if distance < INPUT_DISTANCE and distance > 0:
            objectDetected = True
        else:
            objectDetected = False
        
        # send a trigger to the argon to trigger the IFFFT notification every 10-15 seconds while an object is at the door
        if objectDetected and notificationTimer <= 0:
            bus.write_byte(address, 1)
            notificationTimer = 100 
            print("Notification sent")
        else:
            bus.write_byte(address, 0)
            notificationTimer -= 1
        
        # create a timer which will activate when something is detected
        if not timerStarted and objectDetected:
            startDetectedTimer = time.time()
            timerStarted = True
            print("Timer Started")
            
        # allow the alert to be raised if the timer hasnt stopped
        if timerStarted and objectDetected:
            currentDetectedTimer = time.time()
            currentDetected = currentDetectedTimer - startDetectedTimer
            
        # if the timer is still going but has passed 30 seconds, raise the alarm
        if timerStarted and currentDetected > INPUT_ACTIVATE_TIME:
            GPIO.output(Buzzer, GPIO.HIGH)
            buzzerActiveState = True
            activeStateIsSet = False
            print("Buzzer Activated")

        
        # set the active state timer for 3 minutes
        if buzzerActiveState and not activeStateIsSet:
            buzzerActiveStateFinish = time.time() + INPUT_BUZZER_ACTIVE_TIME
            activeStateIsSet= True    

        # if the buzzer is triggered, it will activate upon any object being detected for 5 minutes
        if buzzerActiveState and objectDetected:
            GPIO.output(Buzzer, GPIO.HIGH)
            buzzerTimerStop = time.time()
            buzzerStop = buzzerTimerStop + INPUT_BUZZER_EXTENSION_TIME
            buzzerExtraTime = True
            bus.write_byte(address, 2)
            print("Active on")
            print("Active state finishes in " + str(buzzerActiveStateFinish - time.time()))
        
        # end the active state after 3 minutes seconds if no object is detected
        if (time.time() > buzzerActiveStateFinish) and buzzerActiveState and not objectDetected:
            timerStarted = False
            buzzerExtraTime = False
            buzzerActiveState = False
            objectDetected = False
            activeStateIsSet = True
            buzzerActiveStateFinish = 0
            currentDetected = 0
            totalDetected = 0
            buzzerStop = 0
            distance = 0
            GPIO.output(Buzzer, GPIO.LOW)
            bus.write_byte(address, 3)
            print("Active State off")
        
        # if an object is being detected as the active state finishes, increase the time by 30 seconds
        if (time.time() > buzzerActiveStateFinish) and buzzerActiveState and objectDetected:
            buzzerActiveStateFinish += 30
            print("Active State extended by 30 seconds")
            
        # stop the timer when the object is no longer detected and set up the buzzer extra time
        if timerStarted and not objectDetected:
            timerStarted = False
            buzzerTimerStop = time.time()
            buzzerStop = buzzerTimerStop + INPUT_BUZZER_EXTENSION_TIME
            buzzerExtraTime = True
            print("Timer Stopped")
        
        # keep the buzzer going for 10 seconds after an object is no longer detected
        if (time.time() > buzzerStop) and buzzerExtraTime:
            GPIO.output(Buzzer, GPIO.LOW)
            buzzerExtraTime = False
            print("Extra time off")
            
        time.sleep(0.1)
    
        
except KeyboardInterrupt:
    # turn off leds and clean up GPIO pins
    bus.write_byte(address, 0)
    bus.write_byte(address, 3)
    GPIO.cleanup()
