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

rcv_buf = queue.Queue()

inputs = ""

connection, client_address = sock.accept()

def main():

    server_handler = server_self()
    
    while True:

        packet_raw = connection.recv(1024)
        if packet_raw:
            rcv_buf.put(packet_raw)

        while rcv_buf.qsize() > 0:
            next_raw_packet = rcv_buf.get_nowait()
            next_packet = next_raw_packet.decode()
            server_handler.rcv_packet(next_packet)

        while snd_buf.qsize() > 0:

            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            print("Sending " + message.strip("\n"))
            connection.send(packet)


class server_self:

    def __init__(self):
        self.mss = 150
        self.state = "closed"
        self.file = ""
        self.dat = ""
        self.HTTP_response = ""
        self.dat_start = 0
        self.dat_end = 0

    def send_msg(self):

        if self.state == "syn_rcv":
            syn_ack_message = "syn+ack|seq:1|ack:1|dat:0"
            snd_buf.put(syn_ack_message)

        if self.state == "connected":

            data =  self.get_data(1,1)

            if len(data) < 1024:

                ack_dat_message = "ack+dat+fin|seq:" + str(self.seq) + "|ack:" + str(self.ack) +"|dat:" + data
                snd_buf.put(ack_dat_message)

                self.state = "fin_wait_1"

            else:

                ack_dat_message = "ack+dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) +"|dat:" + data
                snd_buf.put(ack_dat_message)

    def rcv_packet(self, packet):

        print("Recieved Packet: " + packet.strip("\n"))

        packet_split = packet.split("|")

        rcv_flags = packet_split[0]
        rcv_seq = int(packet_split[1][4:])
        rcv_ack = int(packet_split[2][4:])
        rcv_dat = packet_split[3][4:]

        self.seq = rcv_ack
        self.ack = rcv_seq + len(rcv_dat)

        if rcv_flags == "syn":

            self.state = "syn_rcv"
            self.send_syn_ack()

        elif self.state == "syn_rcv":

            self.state = "connected"

        if self.state == "connected":

            if "dat" in rcv_flags:

                self.file_handle(rcv_dat)
                self.send_HTTP_response()

            self.send_data(self.dat_start, self.dat_end)


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


    def send_HTTP_response(self):

        ack_message = "dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + self.HTTP_response
        snd_buf.put(ack_message)

        self.seq += len(self.HTTP_response)


    def send_data(self, start, end):

        data = self.data[start:end]

        ack_message = "dat|seq:" + str(self.seq) + "|ack:" + str(self.ack) + "|dat:" + self.data
        snd_buf.put(ack_message)

        self.seq += len(self.HTTP_response)

        self.dat_start += 150
        self.dat_end += 150

            
    def get_data(self, start, end):

        if end < len(self.data):
            return self.data[start:end]
        
        return self.data[start:len(self.data)]


def time_stamp():

    time = strftime("%a %b %d %H:%M:%S PDT 2022:",)

    return time

if __name__ == "__main__":
    main()
