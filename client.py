import socket
import sys
from time import strftime, gmtime
import os.path
import queue

server_addr = ("localhost",  int(sys.argv[1]))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_addr)

snd_buf = queue.Queue()

def main():

    client_handler = client_self()

    while True:

        while snd_buf.qsize() > 0:

            message = snd_buf.get_nowait()
            print("Sending Packet: " + message)
            packet = message.encode("utf-8")
            sock.send(packet)

        packet_raw = sock.recv(1024)

        if packet_raw:
            packet = packet_raw.decode()
            client_handler.rcv_packet(packet)

class client_self:
    
    def __init__(self):
        self.state = "closed"
        self.seq = 0
        self.ack = 0
        self.send_msg()

    def send_msg(self):

        if self.state == "closed":
            syn_message = "syn|seq:0|ack:0|dat:"
            snd_buf.put(syn_message)
            self.state = "syn_sent"

        if self.state == "connected":

            if self.seq == 1:

                ack_dat_message = "ack+dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:GET /test.txt HTTP/1.0"
                snd_buf.put(ack_dat_message)

            else:

                ack_dat_message = "ack|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:"

    def rcv_packet(self, packet):

        print("Recieved Packet: " + packet)

        packet_split = packet.split("|")

        rcv_flags = packet_split[0]
        rcv_seq = int(packet_split[1][4:])
        rcv_ack = int(packet_split[2][4:])
        rcv_dat = packet_split[3][4:]

        self.seq = rcv_ack
        self.ack = rcv_seq + len(rcv_dat)

        if rcv_flags == "syn+ack" and self.state == "syn_sent":
            self.state = "connected"
            self.send_msg()

if __name__ == "__main__":
    main()
