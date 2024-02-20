import socket
import sys
from time import strftime, gmtime, sleep
import os.path
import queue

server_addr = ("localhost",  int(sys.argv[1]))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.connect(server_addr)

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
            sock.send(packet)

        packet_raw = sock.recv(1024)

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

    def rcv_packet(self, packet):

        #print("Recieved Packet: " + packet.strip("\n"))

        packet_list = packet.split(" +=+ ")

        for packet in packet_list:

            #print(packet)

            packet_split = packet.split("|")

            rcv_flags = packet_split[0]
            rcv_seq = int(packet_split[1][4:])
            rcv_ack = int(packet_split[2][4:])
            rcv_dat = packet_split[3][4:]

            self.seq = rcv_ack
            self.ack = rcv_seq + len(rcv_dat)

            if self.state == "syn_sent":

                self.state = "connected"
                self.ack += 1
                self.send_http_req()

            elif self.state == "connected":

                if "dat" in rcv_flags:

                    self.data_rcv(rcv_dat)

                    #This part needs to be changed to adjust for packet loss

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


if __name__ == "__main__":
    main()
