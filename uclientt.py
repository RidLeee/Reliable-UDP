import socket
import sys
from time import strftime, gmtime, sleep
import os.path
import queue

server_addr = ("localhost",  int(sys.argv[1]))

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

snd_buf = queue.Queue()

rcv_buf = queue.Queue()

def main():

    client_handler = client_self()

    while True:

        sleep(0.1)

        while snd_buf.qsize() > 0:

            message = snd_buf.get_nowait()
            print("Sending Packet: " + message.strip("\n"))
            packet = message.encode("utf-8")
            client.sendto(packet, server_addr)

        packet_raw = client.recv(1024)

        if packet_raw:
            rcv_buf.put(packet_raw)

        while rcv_buf.qsize() > 0:

            next_raw_packet = rcv_buf.get_nowait()
            next_packet = next_raw_packet.decode()
            client_handler.rcv_packet(next_packet)


class client_self:

     #GET /filename HTTP/1.0
    
    def __init__(self):
        self.state = "closed"
        self.seq = 0
        self.ack = 1
        self.window_size = 2
        self.request = "GET /test.txt HTTP/1.0"
        self.send_syn()
        self.window = []
        self.data = ""
        self.repeat = 0

    def rcv_packet(self, packet):

        print("Recieved Packet: " + packet.strip("\n"))

        packet_list = packet.split(" +=+ ")

        inorder_packet_list = order_packets(packet_list)

        for packet in inorder_packet_list:

            packet_split = packet.split("|")

            rcv_flags = packet_split[0]
            rcv_seq = int(packet_split[1][4:])
            rcv_ack = int(packet_split[2][4:])
            rcv_dat = packet_split[3][4:]

            if rcv_seq != self.ack and rcv_seq != 0:

                self.send_ack()
                continue

            self.seq = rcv_ack
            self.ack = rcv_seq + len(rcv_dat)

            #Checking if it's the HTTP response

            if self.state == "syn_sent":

                self.state = "connected"
                self.ack += 1
                self.send_http_req()

            elif self.state == "connected":

                if "dat" in rcv_flags:

                    if rcv_seq == 1:

                        print("HTTP Response: " + rcv_dat)
                        
                    else:

                        self.data_rcv(rcv_dat)

                        if packet == packet_list[-1]:

                            if "fin" in rcv_flags:
                                self.send_fin_ack()

                            else:
                                self.send_ack()
        
            elif self.state == "last_ack":

                f = open("output.txt", "w")
                f.write(self.data)
                f.close()


    def send_syn(self):

        syn_message = "syn|seq:0|ack:1|dat:"
        snd_buf.put(syn_message)
        self.state = "syn_sent"


    def send_ack(self):

        ack_message = "ack|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:"
        snd_buf.put(ack_message)

    def send_fin_ack(self):

        ack_message = "fin+ack|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:"
        snd_buf.put(ack_message)
        self.state = "last_ack"


    def send_http_req(self):

        dat_message = "dat+ack|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + self.request
        snd_buf.put(dat_message)


    def data_rcv(self, dat):

        self.data += dat
    

def order_packets(packet_list):

    sorted_packet_list = []
    seq_dict = {}
    seq_list = []

    for packet in packet_list:

        packet_split = packet.split("|")
        rcv_seq = int(packet_split[1][4:])
        seq_dict[rcv_seq] = packet
        seq_list.append(rcv_seq)

    seq_list.sort()

    for key in seq_list:
        min_packet = seq_dict[key]
        sorted_packet_list.append(min_packet)

    return(sorted_packet_list)
    

if __name__ == "__main__":
    main()
