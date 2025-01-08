import socket
import sys
from time import strftime, gmtime, sleep
import os.path
import queue
import select
import random

FRAGMENT_SIZE = 2
SERVER_ADDR = ("localhost", 8000)
CLIENT_ADDR = ("localhost", 8001)

UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(CLIENT_ADDR)

PACKET_LOSS = True
PACKET_MIX = True

snd_buf = queue.Queue()
rcv_buf = []

def main():

    server_handler = server()

    while True:

        while snd_buf.qsize() != 0:

            message = snd_buf.get_nowait()
            print("Sent: " + message.strip("\n"))
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, SERVER_ADDR)

        ready = select.select([UDP_socket], [], [], 1)

        if ready[0]:

            try:

                packet, address = UDP_socket.recvfrom(500)

                if packet:
                    rcv_buf.append(packet.decode("utf-8"))
                    #print("Received: " + packet.decode("utf-8"))
                    server_handler.lower_window()

                    if server_handler.check_window() == 0:
                        server_handler.recieve_packets()

            except socket.timeout:
                print("Connection Closed")
                exit()
                
        elif len(rcv_buf) > 0:
            print("here")
            server_handler.recieve_packets()

        # Optional to keep server running for multiple requests but doesn't really demonstrate anything
        # else:
        #     server_handler.reset_server()


class server:

    global rcv_buf
    global PACKET_MIX
    global PACKET_LOSS

    def __init__(self):

        self.state = "listen"
        self.ack = 1
        self.seq = 1
        self.window = 1

    def reset_server(self):

        self.state = "listen"
        self.ack = 1
        self.seq = 1
        self.window = 1

    def recieve_packets(self):

        global rcv_buf
        global PACKET_LOSS

        ################################################# Error control simulation start
        if PACKET_MIX:

            random.shuffle(rcv_buf)

            rcv_buf = sort_by_seq_number(rcv_buf)

        if PACKET_LOSS and self.state == "connected":

                random_loss = random.randint(0, 5)

                if random_loss < len(rcv_buf):

                    rcv_buf.pop(random_loss)

        ############################################### End error control simulation

        for packet in rcv_buf:

            print("Received: " + packet)

        while len(rcv_buf) != 0:

            packet = rcv_buf.pop(0)

            split_packet = packet.split("|")

            if self.state == "listen":

                if packet == "SYN|SEQ:0|ACK:0":

                    self.state = "syn-received"
                    syn_ack_packet = "SYN|SEQ:0|ACK:1"
                    snd_buf.put(syn_ack_packet)

            if self.state == "syn-received":

                split_packet.pop(0)

                rcv_seq = int(split_packet[0][4:])
                rcv_ack = int(split_packet[1][4:])

                self.seq = rcv_ack
                self.ack = rcv_seq + 1

                self.state = "connected"

                self.window = 4

                break

            if self.state == "connected":

                if split_packet[0] != "FIN":

                    rcv_seq = int(split_packet[0][4:])
                    rcv_ack = int(split_packet[1][4:])
                    data = split_packet[2]

                    if rcv_seq == self.ack:

                        self.seq = rcv_ack
                        self.ack = rcv_seq + len(data)

                        self.write_data(data)

                        if len(rcv_buf) == 0:
                            self.send_ack()

                    else:

                        rcv_buf.clear()
                        self.window = 4
                        self.send_ack()

                else:

                    rcv_seq = int(split_packet[1][4:])
                    rcv_ack = int(split_packet[2][4:])
                    data = split_packet[3]

                    if rcv_seq == self.ack:

                        self.seq = rcv_ack
                        self.ack = rcv_seq + len(data)

                        self.write_data(data)

                        self.send_fin_ack()

                        self.state = "fin-wait-2"

                    else:

                        rcv_buf.clear()
                        self.window = 4
                        self.send_ack()
                
                
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

        #print(data)

        file = open("output.txt", "a")
        data = file.write(data)
        file.close()

    def get_state(self):

        return self.state
    
    def send_ack(self):

        snd_buf.put("SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))

    def send_fin_ack(self):

        snd_buf.put("FIN|SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))


def sort_by_seq_number(packets):
    """
    Sorts a list of packet strings by their sequence numbers.

    Args:
        packets (list): List of packet strings in the format 'SEQ:x|ACK:y|data'.

    Returns:
        list: Sorted list of packet strings based on sequence numbers.
    """
    def extract_seq(packet):
        """Helper function to extract the sequence number from a packet."""
        for part in packet.split('|'):
            if part.startswith('SEQ:'):
                return int(part.split(':')[1])
        return 0  # Default value in case SEQ is not found (should not happen with valid input)

    return sorted(packets, key=extract_seq)


if __name__ == "__main__":
    main()