import network
import socket
from time import sleep
from picozero import pico_temp_sensor

ssid = 'No Soup For U' #Your network name
password = 'Av0Cad0T0ast' #Your WiFi password

class ConnectWIFI:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        print("wifi")
        

    def connect(self):
        #Connect to WLAN
        #wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(ssid, password)
        while self.wlan.isconnected() == False:
            print('Waiting for connection...')
            text = ("Waiting to","connect to","WIFI")
            #oledWrite(text)

            sleep(1)
        ip = self.wlan.ifconfig()[0]
        print(f'Connected on {ip}')
        wstatus = self.wlan.status()
        print(wstatus)
        return ip

    def open_socket(self,ip):
        # Open a socket
        address = (ip, 80)
        connection = socket.socket()
        connection.bind(address)
        connection.listen(1)
        return connection

    def disconnect(self):
        #self.wlan = network.WLAN(network.STA_IF)
        self.wlan.disconnect()
        self.wlan.active(False)
        self.wlan.deinit()

    def webpage(self,temperature, reading):
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
                            <select name="brt">
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
        

        
    def serve(self,connection):
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
            if Data[0] == 'brt':
                
                brt = float(Data[1])
                print("brt after adjustment: ",brt)

                #pixels_fill(WHITE)
                #pixels_show(brt)
                #text = ("Current","Brightness:", str(brt))
                #oledWrite(text)
            elif request =='/update?':
                
                state = 'OFF'
            temperature = pico_temp_sensor.temp
            reading = "Brightness: {:.1f}".format(brt)
            html = self.webpage(temperature, reading)
            client.send(html)
            client.close()

