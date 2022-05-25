'''
Internet Radio Using IP Multicast
Group-22

Henil Shah           AU1940205
Shubham Jain         AU1940315
Kathan Joshi         AU1940067
Gaurav Bajaj         AU1940169
Devanshu Magiawala   AU1940190
'''

#importing the libraries
from queue import Queue
import socket
import time
import pickle
import struct
import pyaudio
import threading


#Defining the message structures
class radio_stn_info_request:
    def __init__(self):
        self.type = 1

class radio_stn_info:
    def __init__(self):
        self.radio_stn_number = None
        self.radio_stn_name_size = None
        self.radio_stn_name = None
        self.multicast_address = None
        self.data_port = None
        self.info_port = None
        self.bit_rate = None

class site_info:
    def __init__(self):
        self.type = 10
        self.site_name_size = None
        self.site_name = None
        self.site_desc_size = None
        self.site_desc = None
        self.radio_stn_count = None
        self.radio_stn_list = None

#Defining global flags for audio player controls
pause_flag = None
change_stn_flag = None
terminate_flag = None

# Print Radio Station details
def printStations(rInfo: radio_stn_info):
    print("Station No: ", rInfo.radio_stn_number)
    print("Name Size: ", rInfo.radio_stn_name_size)
    print("Name: ", rInfo.radio_stn_name)
    print("Multicast Address: ", rInfo.multicast_address)
    print("Data Port: ", rInfo.data_port)
    print("Info Port: ", rInfo.info_port)
    print("Bit Rate: ", rInfo.bit_rate)

# Frames are received from server and storedin buffer
def getFrames(s, frameQ, BUFF_SIZE):
    while True:
        if terminate_flag or change_stn_flag:
            break
        if not pause_flag:     # Stop reception if user pressed pause
            newFrame = s.recv(BUFF_SIZE)
            frameQ.put(newFrame)

# Thread function to control - pause, resume, change station and terminate
def detect_keypress():
    global pause_flag
    global change_stn_flag
    global terminate_flag
    while True:
        keypressed = input().lower()
        if keypressed == "p":
            pause_flag = True
            print("Streaming Paused")
        if keypressed == "r":
            pause_flag = False
            print("Streaming Restarted")
        if keypressed == "c":
            change_stn_flag = True
            break
        if keypressed == "x":
            terminate_flag = True
            break
        

def stream_aud(s):
    BUFF_SIZE = 65536
    CHUNK = 10240
    
    frameQ = Queue(maxsize=5000)    # Queue to hold frames sent by the server
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio.get_format_from_width(2), channels=2, rate=44100, output=True, frames_per_buffer=CHUNK)
    
    #initializing player features to False
    global pause_flag 
    pause_flag = False
    global change_stn_flag 
    change_stn_flag = False
    global terminate_flag 
    terminate_flag = False
    
    # Thread to control the player features
    controls_thread = threading.Thread(target=detect_keypress, args=())
    controls_thread.start()

    # This thread receives and stores frames from the server
    thread1 = threading.Thread(target=getFrames, args=(s, frameQ, BUFF_SIZE))
    thread1.start()
    
    time.sleep(5)
    
    #condition for features
    while True:
        if pause_flag:
            pass
        if terminate_flag or change_stn_flag:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            break
        if pause_flag == False:
            recvdFrame = frameQ.get()    # Dequeue the frame and stream it.
            stream.write(recvdFrame)

#Following function establishes UDP connection with the selected station thread
def connectStation(stationIP, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    # Add client to the multicast group
    mcast_req = struct.pack("4sl", socket.inet_aton(stationIP), socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_req)
    stream_aud(s)
    s.close()
    if terminate_flag: 
        print("Terminating")
        exit()

#Search for user selected station and return its port and IP_address
def findRadioStn(radio_stn_list, x): 
    for radio_stn in radio_stn_list:
        if x == radio_stn.radio_stn_number:
            return [radio_stn.multicast_address, radio_stn.data_port]
    return None


#Following function establishes TCP connection with the server and fetches the individual stations info  
def getSiteInfo(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = "127.0.0.1"
    host_port = 5432
    server_addr = (host_ip, host_port)

    s.connect(server_addr)
    rinfo = radio_stn_info_request()    # Send info request to server
    print(rinfo.type)
    rinfo_dump = pickle.dumps(rinfo)
    s.send(rinfo_dump)
    sInfo_dump = s.recv(4096)
    sInfo = pickle.loads(sInfo_dump)

    # Printing site info received 
    print("Type: ", sInfo.type)
    print("Name Size: ", sInfo.site_name_size)
    print("Site Name: ", sInfo.site_name)
    print("Description Size: ", sInfo.site_desc_size)
    print("Description: ", sInfo.site_desc)
    print("Total Radio Stations: ", sInfo.radio_stn_count)
    print("Radio Station List: ")
    for i in range(sInfo.radio_stn_count):
        printStations(sInfo.radio_stn_list[i])
        print("")
    s.close()
    return sInfo

def main():
    while True:
        sInfo = getSiteInfo() #Fetching the individual station info by establishing TCP connect with the server
        x = int(input("Please enter the station number you want to connect: "))
        radio_stn = findRadioStn(sInfo.radio_stn_list, x)
        if radio_stn == None:
            print("Select a valid station please!")
        connectStation(radio_stn[0], radio_stn[1])  # Connect to station and stream its audio

if __name__ == "__main__":
    main()