This project simulates a custom reliable data transfer protocol over UDP, demonstrating key TCP-like features such as connection management, packet sequencing, acknowledgments, and sliding window flow control. Using non-blocking I/O with the select module, the client sends fragmented data to the server, which reassembles it while handling packet loss and reordering. The implementation showcases how UDP, known for its speed but unreliability, can be adapted for reliable communication by employing these techniques.

The selectclient.py manages connection initiation, data fragmentation, and state transitions, while selectserver.py listens for packets, processes them according to a simplified TCP-like protocol, and writes the received data to an output file. Packet loss and mixing are configurable in selectserver.py by toggling the PACKET_LOSS and PACKET_MIX flags.
Instructions

    Place the data to be sent in an input.txt file.
    Run selectserver.py to start the server:

python selectserver.py

Run selectclient.py to start the client:

    python selectclient.py

    Check output.txt on the server side for the reconstructed data.

To simulate reliability challenges, enable or disable PACKET_LOSS and PACKET_MIX in selectserver.py by setting the flags to True or False.
