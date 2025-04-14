import socket
from time import sleep
import queue
import select

# Define the maximum fragment size for packet data.
FRAGMENT_SIZE = 2

# Define the server and client addresses.
SERVER_ADDR = ("localhost", 8000)
CLIENT_ADDR = ("localhost", 8001)

# Create and bind a UDP socket for the server.
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(SERVER_ADDR)

# PACKET_LOSS = True
# PACKET_MIX = True

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

    while True:

        sleep(0.1)

        while snd_buf.qsize() != 0:
            # Process all messages in the send buffer.
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, CLIENT_ADDR)
            print("Sent: " + message.strip("\n"))

        # Wait for incoming data with a timeout of 6 seconds, otherwise socket is disconnected.
        ready = select.select(([UDP_socket]), [], [], 6)

        if ready[0]:
            try:
                rcv_packet, address = UDP_socket.recvfrom(500)

                # Handle received packets.
                if rcv_packet:
                    rcv_packet = rcv_packet.decode("utf-8")
                    print("Received: " + rcv_packet)
                    client_handler.recieve_packet(rcv_packet)

            except socket.timeout:
                print("Connection Closed")
                exit()


class Client:
    """
    Implements a simplified TCP-like protocol client.
    """

    def __init__(self):
        """Initialize client state variables."""
        self.state = "closed"
        self.ack = 1
        self.seq = 1
        self.window = 1
        self.fragment = 2
        self.send_syn()


    def recieve_packet(self, packet):
        """
        Handle packets in the receive buffer based on the connection state.
        """

        split_packet = packet.split("|")

        if self.state == "close":
            exit("Transfer Complete Connection Terminated")

        if self.state == "syn-sent":

            if packet == "SYN|SEQ:0|ACK:1":

                self.state = "connected"

                packet = packet[4:]

            else:

                self.send_syn()
            
        if self.state == "connected":

            self.window = 4

            split_packet = packet.split("|")

            rcv_seq = int(split_packet[0][4:])
            rcv_ack = int(split_packet[1][4:])

            self.seq = rcv_ack
            self.ack = rcv_seq

            if rcv_ack == 1 and rcv_seq == 0:
                self.ack = 1

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

                    self.window -= 1

                    self.seq += self.fragment


        elif self.state == "fin-wait":

            if split_packet[0] == "FIN":
                exit("Transfer Complete")
            else:
                self.state = "connected"
                self.recieve_packet(packet)

        return True
    
    def check_window(self):
        """Return the current window size."""
        return self.window
    
    def raise_window(self):
        """Decrease the window size."""
        self.window += 1
    
    def send_syn(self):
        """Send a SYN packet to initiate connection."""
        syn_packet = "SYN|SEQ:0|ACK:0"
        snd_buf.put(syn_packet)
        self.state = "syn-sent"

    def send_first_ack(self):
        """Send first ACK packet for connection initialization"""
        snd_buf.put("SEQ:1|ACK:1")

if __name__ == "__main__":
    main()
