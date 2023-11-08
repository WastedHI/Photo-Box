# Photobox Project V1, uses SK6812 RGBW chips, push button switch, and 128x64 OLED I2C display.

import array, time
from machine import Pin,I2C
import rp2
import network
import socket
from time import sleep
from ssd1306 import SSD1306_I2C
import framebuf,sys
from picozero import pico_temp_sensor



ssid = 'No Soup For U' #Your network name
password = 'Av0Cad0T0ast' #Your WiFi password

Pb_Switch = Pin(15,Pin.IN,Pin.PULL_DOWN)

i2c_dev = I2C(0,scl=Pin(1),sda=Pin(0),freq=400000)
oled = SSD1306_I2C(128, 64, i2c_dev)

# Configure the number of SK6812 LEDs and GPIO.
NUM_LEDS = 26
PIN_NUM = 28 # (GP)28 = Pin 34 on the PICO W
brightness = 0.8


brt = 0.4


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=32) #was 24
def sk6812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, sk6812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)

# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

##########################################################################
def pixels_show(brightness):
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 16) & 0xFF) * brightness)
        g = int(((c >> 24) & 0xFF) * brightness)
        b = int(((c >> 8) & 0xFF) * brightness)
        w = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<24) + (r<<16) + (b<<8) + w
    sm.put(dimmer_ar, 0) #8 to 0
    time.sleep_ms(10)

def pixels_set(i, color):
    ar[i] = (color[1]<<24) + (color[0]<<16) + (color[2]<<8) + color[3]

def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)


def Pb_Switch_INT(pin):         # PB_Switch Interrupt handler
    global Pb_Switch_State      # reference the global variable
    global brt
    print (brt)
    Pb_Switch.irq(handler=None) # Turn off the handler while it is executing
    
    
    if (Pb_Switch.value() == 1) and (Pb_Switch_State == 0):  # Pb_Switch is active (High) and Pb_Switch State is currently Low
    #if (Pb_Switch.value() == 1): # Pb_Switch is active (High)
        Pb_Switch_State = 1     # Update current state of switch
        
        brt = brt + 0.1
        if brt > 1.05:
            brt = 0.1
        print("brt after adjustment: ",brt)

        pixels_fill(WHITE)
        pixels_show(brt)
        text = ("Current","Brightness:", str(brt))
        oledWrite(text)
#        print("ON")             # Do required action here 
        
            
    elif (Pb_Switch.value() == 0) and (Pb_Switch_State == 1): # Pb_Switch is not-active (Low) and Pb_Switch State is currently High
    #elif (Pb_Switch.value() == 0): # Pb_Switch is not-active (Low)
        Pb_Switch_State = 0     # Update current state of switch
        #Warning_LED.value(0)    # Do required action here
        print("OFF \n")         # Do required action here

    Pb_Switch.irq(handler=Pb_Switch_INT)
    return(brt)
    
#Setup the Interrupt Request Handling for Pb_Switch change of state
Pb_Switch.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING, handler=Pb_Switch_INT)


#Preset the STATE variable for the Pb_Switch
Pb_Switch_State = Pb_Switch.value()
print("Pb_Switch State=", Pb_Switch_State)
    

BLACK = (0, 0, 0, 0)
GREEN = (0, 255, 0, 0)
WHITE = (0, 0, 0, 255)

def oledWrite(text):
    offset = 0
    oled.fill(0)
    for i in range(len(text)):
        oled.text(text[i],0,offset)
        offset = offset + 9

    oled.show()

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        text = ("Waiting to","connect to","WIFI")
        oledWrite(text)

        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

def disconnect():
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
    wlan.deinit()

def webpage(temperature,reading):
    #Template HTML
    html = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Photo Box</title>
                </head>
                <body>
                    <h2>Current Brightness</h2>
                    <p>{reading}</p>
                    
                    <form action="./setbrightness">
                        <p>Please select your desired brightness:</p>
                        <select name="nbrt">
                            <option value="0.5">0.5</option>
                            <option value="0.6">0.6</option>
                            <option value="0.7">0.7</option>
                            <option value="0.8">0.8</option>
                            <option value="0.9">0.9</option>
                            <option value="1.0">1.0</option>
                        </select>
                        <input type="submit" value="Submit" />
                    </form>
                    
                    <h2>Pico W Temp:</h2>
                    <p>Temperature is {temperature}</p>
                </body>
            </html>
            """
    return str(html)
    

    
def serve(connection):
    #Start a web server
    temperature = 0
    global brt
    loop = 0
    while True:
        client = connection.accept()[0]
        #print(str(client) + "\n\n")
        request = client.recv(1024)
        request = str(request)
        #print(request + "\n\n")
        loop = loop + 1
        print(loop)
        try:
            split1 = request.split()[1]
            print("split request : " + split1 + "\n\n")
            split2 = split1.split('?')[1]
            print("split request : " + split2 + "\n\n")
            Data = split2.split('=')
            print("Data: " + str(Data) + "\n\n")
            
        except IndexError:
            pass
        if Data[0] == 'nbrt':
            
            brt = float(Data[1])
            print("brt after adjustment: ",brt)

            pixels_fill(WHITE)
            pixels_show(brt)
            text = ("Current","Brightness:", str(brt))
            oledWrite(text)
        elif request =='/update?':
            
            state = 'OFF'
        temperature = pico_temp_sensor.temp
        reading = "Brightness: {:.1f}".format(brt)
        html = webpage(temperature, reading)
        client.send(html)
        client.close()


disconnect()
time.sleep(3)


ip = connect()
connection = open_socket(ip)

text = ("Photobox V1.0","Connected on:",ip, "")
oledWrite(text)



try:


    pixels_fill(WHITE)
    pixels_show(brt)
    
    
    while True:
        
        time.sleep(.25)
        serve(connection)



except KeyboardInterrupt:
    print("Interupted")
    pixels_fill(BLACK)
    pixels_show(.1)
    oled.fill(0)
    oled.show()
    disconnect()
    print("Disconnect WIFI")

    
