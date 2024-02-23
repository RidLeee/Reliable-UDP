import select 
import socket
import sys
import queue
from time import strftime, gmtime
import re
import os.path

server_addr = ("localhost",  int(sys.argv[1]))

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server.bind(server_addr)

outputs = []

inputs = [server]

snd_buf = queue.Queue()

rcv_buf = queue.Queue()

def main():

    client_handler = server_self()
    
    while True:

        packet, client_addr = server.recvfrom(2048)
        if packet:
            client_handler.rcv_packet(client_addr, packet.decode("utf-8"))

        while snd_buf.qsize() > 0:
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            server.sendto(packet, client_addr)

        server.settimeout(2)


def handle_recv(client_handler):

    packet_raw, client_addr = server.recvfrom(1024)
    print(packet_raw)
    packet = packet_raw.decode("utf-8")
    client_handler.rcv_packet(client_addr, packet)

class server_self:

    def __init__(self):
        self.state = "closed"
        self.offset = 0
        self.file = ""
        self.data = ""
        self.HTTP_response = ""
        self.client_window = 4
        self.client_addr = ""

    def rcv_packet(self, client_addr, packet):
        
        self.client_addr = client_addr

        print("Recieved Packet: " + packet.strip("\n"))

        packet_split = packet.split("|")

        rcv_flags = packet_split[0]
        rcv_seq = int(packet_split[1][4:])
        rcv_ack = int(packet_split[2][4:])
        rcv_dat = packet_split[3][4:]

        #Right here is super important!! Need to check for proper ack and seq

        self.seq = rcv_ack
        self.ack = rcv_seq + len(rcv_dat)

        if rcv_flags == "syn":

            self.state = "syn_rcv"
            self.send_syn_ack()

        elif self.state == "syn_rcv":

            self.state = "connected"

        if self.state == "connected":

            #This part needs to be changed to adjust for packet loss

            if "dat" in rcv_flags:

                self.file_handle(rcv_dat)

                self.send_data(0, 20)
            
            elif "ack" in rcv_flags:

                start = self.seq - self.offset - 1
                end = self.seq - self.offset + 19

                self.send_data(start, end)
    
        elif self.state == "fin_wait_1":

            self.state = "fin_wait_2"
            self.send_final_ack()

    def send_syn_ack(self):

        syn_ack_message = "syn+ack|seq:0|ack:1|dat:"
        snd_buf.put(syn_ack_message)


    def send_ack(self):

        ack_message = "ack|seq:" + self.seq + "|ack:" + str(self.ack) + "|dat:"
        snd_buf.put(ack_message)


    def file_handle(self, rcv_dat):

        #Something about the valid file is bad

        # if rcv_dat[0:5] != "GET/ ": or rcv_dat[-9:] != " /HTTP 1.0":

        #     self.HTTP_response = "HTTP/1.0 400 Bad Request"

        # elif not os.path.exists(self.file):
    
        #     self.HTTP_response = "HTTP/1.0 404 Not Found"

        #else:

        self.HTTP_response = "HTTP/1.0 200 OK"

        self.file = rcv_dat[5:-9]

        f = open(self.file, 'r')
        self.data = f.read()
        f.close()

        self.offset = len(self.HTTP_response)


    def send_data(self, start, end):

        #Needs to be changed to adjust the window

        total_packet = ""

        #Sending the first packet including the HTTP request

        if start == 0:

            total_packet = "dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + self.HTTP_response + " +=+ "
            self.seq += len(self.HTTP_response)

            self.client_window -= 1

        while self.client_window > 0:

            #Sending regular data packets
        
            data = self.data[start:end]

            dat_message = "dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + data
            
            if self.client_window == 1:
                total_packet += dat_message + " +=+ "
            else:
                total_packet += dat_message + " +=+ "

            start += 20
            end += 20

            self.seq += len(data)

            self.client_window -= 1

            #Sending the final data packet

            if end >= len(self.data):

                data = self.data[start:]

                dat_message = "dat+fin|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + data
                self.seq += len(self.data)

                self.state = "fin_wait_1"

                total_packet += dat_message

                self.client_window -= 1

        if "fin" not in total_packet:
            total_packet = total_packet[:-5]

        snd_buf.put(total_packet)
        self.client_window = 4
    

    def send_final_ack(self):

        final_ack_message = "ack|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:"
        snd_buf.put(final_ack_message)
        self.state = "closed"

def time_stamp():

    time = strftime("%a %b %d %H:%M:%S PDT 2022:",)

    return time

if __name__ == "__main__":
    main()