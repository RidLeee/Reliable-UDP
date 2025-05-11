import socket
from time import sleep
import queue
import select
import random

# Define the maximum fragment size for packet data.
FRAGMENT_SIZE = 2

# Define the server and client addresses.
SERVER_ADDR = ("localhost", 8002)
CLIENT_ADDR = ("localhost", 8001)

# Create and bind a UDP socket for the server.
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(SERVER_ADDR)

PACKET_LOSS = False

# Buffers for sending and receiving messages.
snd_buf = queue.Queue()
rcv_buf = []

file = open("input.txt", "r")
data = file.read()
file.close()

def main():
    """
    Main function to handle sending and receiving messages between client and server.
    Uses select for non-blocking I/O.
    """

    client_handler = Client()

    socket_disconnect = 0

    while True:

        sleep(0.25)

        while snd_buf.qsize() != 0:
            # Process all messages in the send buffer.
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, CLIENT_ADDR)
            print("Sent: " + message.strip("\n"))

        # Wait for incoming data with a timeout of 3 seconds, otherwise socket is disconnected.
        ready = select.select(([UDP_socket]), [], [], 2)

        if ready[0]:
            rcv_packet, address = UDP_socket.recvfrom(500)
            socket_disconnect = 0

            # Handle received packets.
            if rcv_packet:
                rcv_packet = rcv_packet.decode("utf-8")
                client_handler.recieve_packet(rcv_packet)

        else:
            if socket_disconnect == 3:
                exit("Connection Closed")

            else:
                socket_disconnect += 1
                client_handler.lost_packet()


class Client:
    """
    Implements a simplified TCP-like protocol client.
    """

    def __init__(self):
        """Initialize client state variables."""
        self.state = "closed"
        self.ack = 1
        self.seq = 1
        self.expected_acks = []
        self.window = 1
        self.fragment = 2
        self.send_syn()

    def recieve_packet(self, packet):

        print("Received: " + packet)

        match self.state:
            case "syn_sent":
                self.syn_sent_rcv(packet)
            case "connected":
                self.connected_rcv(packet)
            case "fin_wait":
                self.fin_wait_rcv(packet)
        return True
    
    def syn_sent_rcv(self, packet):

        if packet == "SYN:1|SEQ:0|ACK:1|FIN:0|DAT:0|":
            self.state = "connected"
            self.seq = 1
            self.ack = 1
            self.window = 4
            while self.window > 0:
                self.send_data()

    def connected_rcv(self, packet):

        split_packet = packet.split("|")

        self.window += 1

        rcv_seq = int(split_packet[1][4:])
        rcv_ack = int(split_packet[2][4:])

        syn_flag = int(split_packet[0][4:])
        fin_flag = int(split_packet[3][4:])

        if self.expected_acks[0] == rcv_ack: #Edge case here in case the fin packet is lost
            self.expected_acks.pop(0)
        
        else:
            self.seq = self.expected_acks[0] - self.fragment
            self.expected_acks = []
            self.window = 4

        while self.window > 0:
            self.send_data()
    
    def fin_wait_rcv(self, packet):

        self.window += 1

        split_packet = packet.split("|")

        rcv_seq = int(split_packet[1][4:])
        rcv_ack = int(split_packet[2][4:])

        syn_flag = int(split_packet[0][4:])
        fin_flag = int(split_packet[3][4:])

        if self.expected_acks[0] == rcv_ack and fin_flag: #Edge case here in case the fin packet is lost
            exit("========== Transfer Complete ============")
            self.expected_acks.pop(0)
        
        elif self.expected_acks[0] == rcv_ack:
            self.expected_acks.pop(0)

        else:
            self.window = 4
            self.seq = self.expected_acks[0] - self.fragment
            self.expected_acks = []
        
            while self.window > 0:
                self.send_data()


    def send_syn(self):

        syn_packet = "SYN:1|SEQ:0|ACK:0|FIN:0|DAT:0|"
        snd_buf.put(syn_packet)
        self.state = "syn_sent"

    def send_data(self):

        print("FJHDSJFHDSKJ")

        # If sending the final data packet

        if self.seq - 1 + self.fragment >= len(data):

            fin_data_to_send = data[self.seq-1:]
            fin_data_packet = f"SYN:0|SEQ:{self.seq}|ACK:{self.ack}|FIN:1|DAT:1|{fin_data_to_send}"
            snd_buf.put(fin_data_packet)
            self.seq += len(fin_data_to_send)
            self.state = "fin_wait"
            self.window -= 1

        # If not sending the final data packet
        else:

            data_to_send = data[self.seq-1:self.seq-1 + self.fragment]
            data_packet = f"SYN:0|SEQ:{self.seq}|ACK:{self.ack}|FIN:0|DAT:1|{data_to_send}"
            snd_buf.put(data_packet)
            self.seq += self.fragment
            self.window -= 1

        self.expected_acks.append(self.seq)

        print(self.expected_acks)
        

    def lost_packet(self):
        
        match self.state:
            case "syn_sent":
                self.send_syn()
            case "connected":
                self.seq = self.expected_acks[0] - self.fragment
                self.expected_acks = []
                self.window = 4
                while self.window > 0:
                    self.send_data()
        return True


if __name__ == "__main__":
    main()
