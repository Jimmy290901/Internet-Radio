'''
Internet Radio Using IP Multicast
Group-22

Henil Shah           AU1940205
Shubham Jain         AU1940315
Kathan Joshi         AU1940067
Gaurav Bajaj         AU1940169
Devanshu Magiawala   AU1940190
'''

#importing modules
import socket
import pickle
from socketserver import UDPServer
import threading
import wave
import pyaudio
import time
import os

#defining the message structures
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


#Information about the stations
def stationList():
    temp = site_info()
    temp.site_name = "Naam mein kya rakha hai"
    temp.site_name_size = len(temp.site_name)
    temp.site_desc = "Sunte raho, chill marte raho"
    temp.site_desc_size = len(temp.site_desc)
    temp.radio_stn_count = 3
    temp.radio_stn_list = []

    temp1 = radio_stn_info()
    temp1.radio_stn_number = 1
    temp1.radio_stn_name = "English Songs Radio"
    temp1.radio_stn_name_size = len(temp1.radio_stn_name)
    temp1.multicast_address = "239.192.1.0"
    temp1.data_port = 5432
    temp1.info_port = 8001
    temp1.bit_rate = 250000

    temp2 = radio_stn_info()
    temp2.radio_stn_number = 2
    temp2.radio_stn_name = "Hindi Songs Radio"
    temp2.radio_stn_name_size = len(temp2.radio_stn_name)
    temp2.multicast_address = "239.192.1.1"
    temp2.data_port = 5433
    temp2.info_port = 8002
    temp2.bit_rate = 250000

    temp3 = radio_stn_info()
    temp3.radio_stn_number = 3
    temp3.radio_stn_name = "Gujarati Songs Radio"
    temp3.radio_stn_name_size = len(temp3.radio_stn_name)
    temp3.multicast_address = "239.192.1.2"
    temp3.data_port = 5434
    temp3.info_port = 8003
    temp3.bit_rate = 250000

    temp.radio_stn_list.append(temp1)
    temp.radio_stn_list.append(temp2)
    temp.radio_stn_list.append(temp3)
    return temp

#Defines a TCP socket 
def tcpConnect():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(('127.0.0.1', 5432))

    server_socket.listen(5)

    while True:
        print("Server waiting for connection")
        client_socket, addr = server_socket.accept()
        print("Client connected from ", addr)

        data = client_socket.recv(4096)
        new_data = pickle.loads(data)
        print("Requested: ", new_data.type)
        try:
            temp = stationList()
            client_socket.send(pickle.dumps(temp))
        except:
            print("Exited by the user")
        client_socket.close()
    server_socket.close()

#Function to transfer audio metadata through UDP over socket
def send_audio(filename, sock, data):
    BUFF_SIZE = 65536
    CHUNK = 10240
    wf = wave.open(filename)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()), 
                        channels=wf.getnchannels(), rate=wf.getframerate(), 
                        input=True, frames_per_buffer=CHUNK)
    sample_rate = wf.getframerate()
    count = 0
    while True:
        frame = wf.readframes(CHUNK)
        sock.sendto(frame, (data.multicast_address, data.data_port))
        time.sleep(0.8*CHUNK/sample_rate)
        if count > (wf.getnframes()/CHUNK):
            break
        count += 1

#Defines a UDP connection and transfers the data
def udpConnect(data):
    udp_socket = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 5)

    station = data.radio_stn_number
    
    if station == 1:
        while True:
            for file in os.listdir('./songs/english_songs'):
                filename=os.path.join('./songs/english_songs',file)
                print("Streaming "+ filename +" on ", data.radio_stn_name)
                send_audio(filename, udp_socket, data)

    if station == 2:
        while True:
            for file in os.listdir('./songs/hindi_songs'):
                filename=os.path.join('./songs/hindi_songs',file)
                print("Streaming "+ filename +" on ", data.radio_stn_name)
                send_audio(filename, udp_socket, data)

    if station == 3:
        while True:
            for file in os.listdir('./songs/gujarati_songs'):
                filename=os.path.join('./songs/gujarati_songs',file)
                print("Streaming "+ filename +" on ", data.radio_stn_name)
                send_audio(filename, udp_socket, data)
    
    udp_socket.close()

# Main function handling the threads and calling the functions
def main():
    x = threading.Thread(target=tcpConnect, args=())
    x.start()
    station_data = stationList()
    for i in range(0,3):
        y = threading.Thread(target=udpConnect, args=(station_data.radio_stn_list[i], ), group=None)
        y.start()
    x.join()

if __name__ == "__main__":
    main()