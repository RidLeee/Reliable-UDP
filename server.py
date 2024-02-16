import socket
import sys
from time import strftime, gmtime
import os.path
import queue

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', int(sys.argv[1]))

sock.bind(server_address)

sock.listen(1)

snd_buf = queue.Queue()

sock.listen(1)

inputs = ""

connection, client_address = sock.accept()

def main():

    server_handler = server_self()
    
    while True:

        packet_raw = connection.recv(1024)

        if packet_raw:
            packet = packet_raw.decode()
            server_handler.rcv_packet(packet)

        while snd_buf.qsize() > 0:

            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            print("Sending " + message)
            connection.send(packet)

class server_self:

    def __init__(self):
        self.state = "closed"
        self.file = ""
        self.dat = ""

    def send_msg(self):

        if self.state == "syn_rcv":
            syn_ack_message = "syn+ack|seq:0|ack:1|dat:0"
            snd_buf.put(syn_ack_message)

        if self.state == "connected":
            print("connected")

    def rcv_packet(self, packet):

        print("Recieved Packet: " + packet)

        packet_split = packet.split("|")

        rcv_flags = packet_split[0]
        rcv_seq = int(packet_split[1][4:])
        rcv_ack = int(packet_split[2][4:])
        rcv_dat = packet_split[3][4:]

        self.seq = rcv_ack
        self.ack = rcv_seq + len(rcv_dat)

        if rcv_flags == "syn":
            self.state = "syn_rcv"
            self.send_msg()
    
        if rcv_flags == "ack+dat":
            self.file = rcv_dat[9:-6]
            print(self.file)
            self.dat = file_response(self.file)

            self.send_msg()

def file_response(file):

    if os.path.exists(file):

        return "HTTP/1.0 200 OK"
    
    return "HTTP/1.0 404 Not Found"

def time_stamp():

    time = strftime("%a %b %d %H:%M:%S PDT 2022:",)

    return time

if __name__ == "__main__":
    main()
