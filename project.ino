#include <Wire.h>

int objectDetected = 0;
int notificationLed = D6;
int activeLed = D4;
bool active = false;

void setup() {
    pinMode(notificationLed, OUTPUT);
    pinMode(activeLed, OUTPUT);

    Wire.begin(0x40); // Initalise argon device as a slave on address 40
    
    Wire.onReceive(signalDetected); // call signalDetected when the signal is recieved from the master device
}

// handles the data recieved from the raspberry pi
void signalDetected(int numOfBytes)
{
    char c = Wire.read(); // read the value from the RPI
    
    if (c == 1) // if an object was detected by RPI, blink the red led
    {
        objectDetected = 1;
        digitalWrite(notificationLed, HIGH);
        
    }
    else // Nothing detected by RPI
    {
        objectDetected = 0;
        digitalWrite(notificationLed, LOW);
    }
    
    if (c == 2) // active state is on
    {
        active = true;
    }
    else if (c == 3) // active state is off
    {
        active = false;
    }
}

// main logic of the program, loops indefinately
void loop() {
    if (objectDetected == 1) // publish the event for the IFFFT trigger when an object is detected every 10-15 seconds whilst detection is occuring
    {
        Particle.publish("objectDetected", "1", PRIVATE);
        objectDetected = 0;
    }
    
    if (active) // light up the blue led while he active state is on
    {
        digitalWrite(activeLed, HIGH);
    }
    else
    {
        digitalWrite(activeLed, LOW);
    }
    
    delay(100);
}