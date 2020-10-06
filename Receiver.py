# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)

# Receive packets from the sender w/ GBN protocol
def receive_gbn(sock):
    previous = -1
    payload_length = None
    packets = []
    addr_connection = None
    
    while True:
        if previous == payload_length:
            print("File transfer was successful, closing connection.")
        try:
            p, addr = udt.recv(sock)
            seq_num, payload = packet.extract(p)

            # If this is a new connection, save address and store expected payload length
            if addr_connection == None and seq_num == 0:
                payload_length = int(payload)
                addr_connection = addr

            # if packet received was from the expected sender...
            if addr == addr_connection:

                # if packet signals end of transmission, stop listening for packets
                if seq_num == -1 and payload == b'FIN':
                    print("Connection closed successfully")
                    break
                
                # if sequence number is what we're expecting, send an ack and append packet contents to packet stack
                if seq_num == previous + 1:
                    udt.send(packet.make(seq_num, b'ACK'), sock, addr)
                    packets.append((seq_num, payload))
                    previous += 1
                    print("Received packet: {}".format(seq_num))
                
                # retransmit ack for last-received packet
                else:
                    if len(packets) > 0:
                        udt.send(packet.make(packets[-1][0], b'ACK'), sock, addr) 
        
        except ConnectionError as e:
            print(e)
            return -1

    # because packet list contains sequence numbers, simply form a list 
    return list(dict(packets).values())[1:]

# Receive packets from the sender w/ SR protocol
def receive_sr(sock, windowsize):
    # Fill here
    return

# Receive packets from the sender w/ Stop-n-wait protocol
def receive_snw(sock):
    file_data = []
    seq_num = 0
    while seq_num > -1:
        p, addr = udt.recv(sock)
        seq_num, payload = packet.extract(p)

        print("Received packet: {}".format(seq_num))

        #if seq_num == -1:
        #    break

        udt.send(packet.make(seq_num, b'ACK'), sock, addr)
        print("Acked packet: {}\n".format(seq_num))
        if seq_num > len(file_data) - 1:
            file_data.append(payload)
                    
    return file_data

# Main function
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Expected filename as command line argument')
        exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(RECEIVER_ADDR)

    filename = sys.argv[1]
    # file_data = receive_snw(sock)
    file_data = receive_gbn(sock)

    if file_data == -1:
        print("Incomplete file received, exiting program.")
        sys.exit()

    file = open(filename, "wb")
    for i in range(len(file_data)):
        file.write(file_data[i])

    file.close()
    sock.close()