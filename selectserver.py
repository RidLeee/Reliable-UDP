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

# Create and bind a UDP socket for the client.
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(CLIENT_ADDR)

# Enable packet loss and packet mix simulations for error handling demonstration.
PACKET_LOSS = True

# Buffers for sending and receiving messages.
snd_buf = queue.Queue()
rcv_buf = []

def main():
    """
    Main function to handle sending and receiving messages between client and server.
    Uses select for non-blocking I/O.
    """
    server_handler = Server()

    while True:

        sleep(0.25)
        # Process all messages in the send buffer.
        while snd_buf.qsize() != 0:
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, SERVER_ADDR)
            print("Sent: " + message.strip("\n"))

        ready = select.select([UDP_socket], [], [], 10)

        if ready[0]:  # if socket is ready
            rcv_packet, address = UDP_socket.recvfrom(500)

            if rcv_packet:
                rcv_packet = rcv_packet.decode("utf-8")
                server_handler.recieve_packet(rcv_packet)
        
        else:
            exit("Server Timeout")
        
class Server:
    """
    Simulates a server handling connection state, window size, and packet receipt.
    Implements a simplified TCP-like protocol server.
    """
    global rcv_buf

    def __init__(self):
        """Initialize server state variables."""
        self.state = "listen"
        self.ack = 1
        self.seq = 1
        self.expected_seq = 1
        self.rcved_seqs = []

    def recieve_packet(self, packet):

        global PACKET_LOSS

        random_loss = random.randint(0, 5)

        if random_loss == 1:
            return
        
        print("Received: " + packet)

        match self.state:
            case "listen":
                self.listen_rcv(packet)
            case "syn_received":
                self.syn_received_rcv(packet)
            case "connected":
                self.connected_rcv(packet)

    def listen_rcv(self, packet):

        if packet == "SYN:1|SEQ:0|ACK:0|FIN:0|DAT:0|":
            self.state = "syn_received"
            self.send_syn_ack()

    def syn_received_rcv(self, packet):

        if packet == "SYN:1|SEQ:0|ACK:1|FIN:0|DAT:0|":
            self.send_syn_ack()

    def connected_rcv(self, packet):

        split_packet = packet.split("|")

        rcv_seq = int(split_packet[1][4:])
        rcv_ack = int(split_packet[2][4:])

        syn_flag = int(split_packet[0][4:])
        fin_flag = int(split_packet[3][4:])
        dat_flag = int(split_packet[4][4:])

        if dat_flag:
            data = split_packet[5]

        if syn_flag:
            self.send_syn_ack()

        if rcv_seq == self.expected_seq:

            self.ack = rcv_seq + len(data)
            self.expected_seq += len(data)

            self.write_data(data)
            
            if fin_flag:
                self.send_fin_ack()
            else:
                self.send_ack()

    def send_syn_ack(self):

        syn_ack_packet = "SYN:1|SEQ:0|ACK:1|FIN:0|DAT:0|"
        snd_buf.put(syn_ack_packet)
        self.state = "connected"

    def send_ack(self):

        ack_packet = f"SYN:0|SEQ:{self.seq}|ACK:{self.ack}|FIN:0|DAT:0|"
        snd_buf.put(ack_packet)

    def send_fin_ack(self):

        fin_ack_packet = f"SYN:0|SEQ:{self.seq}|ACK:{self.ack}|FIN:1|DAT:0|"
        snd_buf.put(fin_ack_packet)

    def write_data(self, data):
        with open("output.txt", "a") as file:
            file.write(data)

if __name__ == "__main__":
    main()
