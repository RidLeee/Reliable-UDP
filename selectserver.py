import socket
import sys
from time import strftime, gmtime, sleep
import os.path
import queue
import select

fragment_size = 2
server_addr = ("localhost", 8000)
client_addr = ("localhost", 8001)

UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(client_addr)

timeout = 2

snd_buf = queue.Queue()
rcv_buf = queue.Queue()

def main():

    server_handler = server()

    sleep(2)

    count = 3

    while True:

        sleep(0.1)

        while snd_buf.qsize() != 0:

            message = snd_buf.get_nowait()
            print("Sent: " + message.strip("\n"))
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, server_addr)

        ready = select.select(([UDP_socket]), [], [], timeout)

        if ready[0]:

            try: # MOVE THIS CODE INTO THE PACKET RECIEVE AND MAKE IT SO THAT THIS ONLY CHECKS IF THE WINDOW IS FULL OR NOT

                packet, address = UDP_socket.recvfrom(500)

                if packet:
                    print("Received: " + packet.decode("utf-8"))
                    rcv_buf.put(packet.decode("utf-8"))
                    server_handler.lower_window()

                    count = 3

                    if server_handler.check_window() == 0:
                        server_handler.recieve_packets()

            except socket.timeout:
                print("Connection Closed")
                exit()

        
        elif count == 0:
            if rcv_buf.qsize() > 0:
                server_handler.recieve_packets()
                count = 3
            else:
                exit("Connection Lost")
                
        else:
            count -= 1


class server:

    global rcv_buf

    def __init__(self):

        self.state = "listen"
        self.ack = 1
        self.seq = 1
        self.window = 1
        

    def recieve_packets(self):

        while rcv_buf.qsize() != 0:

            packet = rcv_buf.get_nowait()

            split_packet = packet.split("|")

            self.raise_window()

            if self.state == "listen":

                if packet == "SYN|SEQ:0|ACK:0":

                    self.state = "syn-received"
                    syn_ack_packet = "SYN|SEQ:0|ACK:1"
                    snd_buf.put(syn_ack_packet)

                    self.window = 4

            if self.state == "syn-received":

                split_packet.pop(0)

                rcv_seq = int(split_packet[0][4:])
                rcv_ack = int(split_packet[1][4:])

                self.seq = rcv_ack
                self.ack = rcv_seq + 1


                self.state = "connected"


            elif self.state == "connected":

                if split_packet[0] != "FIN":

                    rcv_seq = int(split_packet[0][4:])
                    rcv_ack = int(split_packet[1][4:])

                    data = split_packet[2]

                    self.seq = rcv_ack
                    self.ack = rcv_seq + len(data)

                    if rcv_buf.qsize() == 0:
                        self.send_ack()

                else:

                    rcv_seq = int(split_packet[1][4:])
                    rcv_ack = int(split_packet[2][4:])

                    data = split_packet[3]

                    self.seq = rcv_ack
                    self.ack = rcv_seq + len(data)

                    self.send_fin_ack()

                    self.state = "fin-wait-2"

            elif self.state == "fin-wait-2":
                exit("Closing server")
                    

    def check_window(self):

        return self.window
    
    def lower_window(self):

        self.window -= 1

    def raise_window(self):

        self.window += 1
    
    def send_syn(self):

        syn_packet = "SYN|SEQ:0|ACK:0"
        snd_buf.put(syn_packet)
        self.state = "syn_sent"

    def write_data(self, data):

        file = open("output.txt", "a")
        data = file.write(data)
        file.close()

    def get_state(self):

        return self.state
    
    def send_ack(self):

        snd_buf.put("SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))


    def send_fin_ack(self):

        snd_buf.put("FIN|SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))


if __name__ == "__main__":
    main()