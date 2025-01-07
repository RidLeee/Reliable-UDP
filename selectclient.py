import socket
import sys
from time import strftime, gmtime, sleep
import os.path
import queue
import select

server_addr = ("localhost", 8000)
client_addr = ("localhost", 8001)

timeout = 10

file = open("input.txt", "r")
data = file.read()
file.close()

UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(server_addr)

snd_buf = queue.Queue()
rcv_buf = queue.Queue()

def main():

    count = 3

    UDP_socket.settimeout(timeout)
    
    client_handler = client()

    while True:

        sleep(0.1)

        while snd_buf.qsize() > 0:
            message = snd_buf.get_nowait()
            print("Sent: " + message.strip("\n"))
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, client_addr)

        ready = select.select(([UDP_socket]), [], [], timeout)

        if ready[0]:

            try:

                rcv_packet, address = UDP_socket.recvfrom(500)

                if rcv_packet:
                    print("Received: " + packet.decode("utf-8"))

                    count = 3

                    client_handler.recieve_packet(rcv_packet.decode("utf-8"))


            # try:
            #     rcv_packet, address = UDP_socket.recvfrom(2500)
            #     if rcv_packet:
            #         sleep(0.2)
            #         print("Received: " + rcv_packet.decode("utf-8"))
            #         client_handler.recieve_packet(rcv_packet.decode("utf-8"))

            except: 
                sleep(0.2)
                print("Connection Closed")
                exit()


class client:

    def __init__(self):
        self.state = "closed"
        self.ack = 1
        self.seq = 1
        self.window = 1
        self.fragment = 2
        self.send_syn()


    def recieve_packet(self, packet):

        split_packet = packet.split("|")

        if self.state == "close":
            exit("Transfer Complete Connection Terminated")

        if self.state == "syn-sent":

            if packet == "SYN|SEQ:0|ACK:1":

                self.state = "connected"

                packet = packet[4:]
            

        if self.state == "connected":

            self.window = 4

            split_packet = packet.split("|")

            rcv_seq = int(split_packet[0][4:])
            rcv_ack = int(split_packet[1][4:])

            self.seq = rcv_ack
            self.ack = rcv_seq

            if self.ack == 0: #SHOULD OPTIMIZE OUT
                self.ack = 1

            while self.window != 0:

                if self.seq >= len(data):

                    fin_data_to_send = data[self.seq-1:self.seq-1 + self.fragment]
                    data_packet = "FIN|SEQ:" + str(self.seq) + "|ACK:" + str(self.ack) + "|" + fin_data_to_send

                    snd_buf.put(data_packet)

                    self.state = "fin-wait"

                    break


                else:

                    data_to_send = data[self.seq-1:self.seq-1 + self.fragment]
                    data_packet = "SEQ:" + str(self.seq) + "|ACK:" + str(self.ack) + "|" + data_to_send

                    snd_buf.put(data_packet)

                    self.window -= 1

                    self.seq += self.fragment


        elif self.state == "fin-wait":
            exit("Transfer complete")

        return True
    

    def check_window(self):

        return self.window
    

    def raise_window(self):

        self.window += 1
    
    def send_syn(self):

        syn_packet = "SYN|SEQ:0|ACK:0"
        snd_buf.put(syn_packet)
        self.state = "syn-sent"


    def send_first_ack(self):

        snd_buf.put("SEQ:1|ACK:1")


    def send_ack(self):

        snd_buf.put("SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))

if __name__ == "__main__":
    main()