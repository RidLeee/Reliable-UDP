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

# Create and bind a UDP socket for the client.
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_socket.bind(CLIENT_ADDR)

# Enable packet loss and packet mix simulations for error handling demonstration.
PACKET_LOSS = False
PACKET_MIX = False

# Buffers for sending and receiving messages.
snd_buf = queue.Queue()
rcv_buf = []

def main():
    """
    Main function to handle sending and receiving messages between client and server.
    Uses select for non-blocking I/O.
    """
    server_handler = Server()

    count = 0

    while True:

        sleep(0.1)
        # Process all messages in the send buffer.
        while snd_buf.qsize() != 0:
            message = snd_buf.get_nowait()
            packet = message.encode("utf-8")
            UDP_socket.sendto(packet, SERVER_ADDR)
            print("Sent: " + message.strip("\n"))

        # Wait for incoming data with a timeout of 1 second.
        ready = select.select([UDP_socket], [], [], 4)

        if ready[0]:
            try:
                rcv_packet, address = UDP_socket.recvfrom(500)

                if rcv_packet:
                    rcv_packet = rcv_packet.decode("utf-8")
                    rcv_buf.append(rcv_packet)  # Store received packet in buffer.
                    server_handler.lower_window()  # Simulate window size decrement.

                    #print("Received: " + rcv_packet)

                    # If the receive window is full, handle received packets.
                    if server_handler.check_window() == 0:
                        server_handler.recieve_packets()
                        count = 0

            except:
                exit("Connection Closed")
        
        elif len(rcv_buf) > 0:
            server_handler.recieve_packets()



class Server:
    """
    Simulates a server handling connection state, window size, and packet receipt.
    Implements a simplified TCP-like protocol server.
    """
    global rcv_buf
    global PACKET_MIX
    global PACKET_LOSS

    def __init__(self):
        """Initialize server state variables."""
        self.state = "listen"
        self.ack = 1
        self.seq = 1
        self.window = 1

    def recieve_packets(self):
        """
        Handle packets in the receive buffer based on the connection state.
        Implements simulated error control and packet handling.
        """
        global rcv_buf
        global PACKET_MIX
        global PACKET_LOSS

        # Commented section to simulate packet mixing and packet loss for error handling.
        if PACKET_MIX:
            random.shuffle(rcv_buf)
            rcv_buf = sort_by_seq_number(rcv_buf)

        if PACKET_LOSS:
            print("in here")
            random_loss = random.randint(0, 5)
            if random_loss < len(rcv_buf):
                rcv_buf.pop(random_loss)

        while len(rcv_buf) != 0:
            
            packet = rcv_buf.pop(0)

            split_packet = packet.split("|")

            print("Received: " + packet)

            if self.state == "listen" or packet == "SYN|SEQ:0|ACK:0":
                # Handle SYN packet to establish connection.
                self.state = "syn-received"
                self.send_syn_ack()

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
                        self.write_data(data)  # Write received data to file.

                        if len(rcv_buf) == 0:
                            self.send_ack()  # Acknowledge receipt.
                    else:
                        rcv_buf.clear()  # Clear buffer if sequence is incorrect.
                        self.send_ack()

                else:  # Handle FIN packet to close connection.

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
                        self.send_ack()


    def check_window(self):
        """Return the current window size."""
        return self.window

    def lower_window(self):
        """Decrease the window size."""
        self.window -= 1

    def send_syn(self):
        """Send a SYN packet to complete connection."""
        syn_packet = "SYN|SEQ:0|ACK:0"
        snd_buf.put(syn_packet)
        self.state = "syn_sent"

    def write_data(self, data):
        """Write received data to a file."""
        with open("output.txt", "a") as file:
            file.write(data)

    def get_state(self):
        """Return the current connection state."""
        return self.state
    
    def send_syn_ack(self):
        """Send the SYN/ACK packet for connection initialization"""
        snd_buf.put("SYN|SEQ:0|ACK:1")

    def send_ack(self):
        """Send an ACK packet for received data."""
        self.window = 4
        snd_buf.put("SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))

    def send_fin_ack(self):
        """Send a FIN-ACK packet to close connection."""
        snd_buf.put("FIN|SEQ:" + str(self.seq) + "|" + "ACK:" + str(self.ack))

class client:
    """
    Implements a simplified TCP-like protocol client.
    """

    def __init__(self):
        """Initialize client state variables."""
        self.state = "closed"
        self.ack = 1
        self.seq = 1

def sort_by_seq_number(packets):
    """Sort packets by their sequence number."""
    def extract_seq(packet):
        for part in packet.split('|'):
            if part.startswith('SEQ:'):
                return int(part.split(':')[1])
        return 0  # Default if no SEQ found.
    return sorted(packets, key=extract_seq)

if __name__ == "__main__":
    main()
