# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)


# Receive packets from the sender w/ GBN protocol
def receive_gbn(sock):
    # Fill here
    return


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
    file_data = receive_snw(sock)
    print(file_data)
    file = open(filename, "wb")
    for i in range(len(file_data)):
        file.write(file_data[i])
    file.close()
    # Close the socket
    sock.close()
