import socket
from time import sleep
import queue
import select
import random

# Define the maximum fragment size for packet data.
FRAGMENT_SIZE = 2

# Define the server and client addresses.
SERVER_ADDR = ("localhost", 8000)
CLIENT_ADDR = ("localhost", 8001)

# Create and bind a UDP socket for the server.
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(SERVER_ADDR)

PACKET_LOSS = True

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

        sleep(0.1)

        while snd_buf.qsize() != 0:
            # Process all messages in the send buffer.
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, CLIENT_ADDR)
            print("Sent: " + message.strip("\n"))

        # Wait for incoming data with a timeout of 6 seconds, otherwise socket is disconnected.
        ready = select.select(([UDP_socket]), [], [], 5)

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
                cur_state = client_handler.get_state()
                if cur_state == "syn-sent":
                    client_handler.send_syn()
                elif cur_state == "connected" or "fin-wait":
                    client_handler.connected_timeout()
                    client_handler.send_data()


class Client:
    """
    Implements a simplified TCP-like protocol client.
    """

    def __init__(self):
        """Initialize client state variables."""
        self.state = "closed"
        self.ack = 1
        self.last_ack = 1
        self.seq = 1
        self.window = 1
        self.fragment = 2
        self.expected_seq = 1
        self.last_packet = None
        self.send_syn()


    def recieve_packet(self, packet):
        """
        Handle packets in the receive buffer based on the connection state.
        """
        global PACKET_LOSS

        if PACKET_LOSS and self.state == "connected":
            random_loss = random.randint(0, 1)
            if random_loss == 1:
                print("Lost Packet: " + packet)
                PACKET_LOSS = False
                return
        
        print("Received: " + packet)

        split_packet = packet.split("|")

        if self.state == "close":
            exit("Transfer Complete Connection Terminated")

        if self.state == "syn-sent":
            if packet == "SYN|SEQ:0|ACK:1": # This check is redundant since the server will only respond with a syn response.
                self.state = "connected"
                packet = packet[4:]
            else:
                self.send_syn() # Resend initial syn since it got lost
            
        if self.state == "connected":

            split_packet = packet.split("|")

            rcv_seq = int(split_packet[0][4:])
            rcv_ack = int(split_packet[1][4:])

            self.seq = rcv_ack
            self.ack = rcv_seq
            self.last_ack = rcv_ack

            if rcv_ack == 1 and rcv_seq == 0: 
                self.ack = 1

            self.send_data()

        elif self.state == "fin-wait":

            if split_packet[0] == "FIN":
                exit("Transfer Complete")

            else:
                self.state = "connected"
                self.send_data(packet)

        return True
    
    def send_data(self):
        
        self.window = 4
        
        while self.window != 0:

            if self.seq - 1 + self.fragment >= len(data):

                fin_data_to_send = data[self.seq-1:]
                fin_data_packet = "FIN|SEQ:" + str(self.seq) + "|ACK:" + str(self.ack) + "|" + fin_data_to_send
                snd_buf.put(fin_data_packet)
                self.state = "fin-wait"
                self.seq += len(fin_data_to_send)
                break

            else:

                data_to_send = data[self.seq-1:self.seq-1 + self.fragment]
                data_packet = "SEQ:" + str(self.seq) + "|ACK:" + str(self.ack) + "|" + data_to_send
                snd_buf.put(data_packet)
                self.seq += self.fragment
                self.window -= 1

    def connected_timeout(self):
        self.seq = self.last_ack

    def get_state(self):
        return self.state
    
    def send_syn(self):
        """Send a SYN packet to initiate connection."""
        syn_packet = "SYN|SEQ:0|ACK:0"
        snd_buf.put(syn_packet)
        self.state = "syn-sent"

if __name__ == "__main__":
    main()