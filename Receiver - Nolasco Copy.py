# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)

file_data = []

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
    global file_data
    endStr = ''
    while endStr!='END':
        #while True: 
        pkt, senderaddr = udt.recv(sock)
        seq, data = packet.extract(pkt)
        if seq == len(file_data):
            if data.decode() != 'END':
                file_data.append(data)
        endStr = data.decode()
        print("From: ", senderaddr, ", Seq# ", seq, endStr)
        #send acknowledgment packet
        pkt = packet.make(seq, "ACK".encode())
        udt.send(pkt, sock, senderaddr)
       


# Main function
if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print('Expected filename as command line argument')
    #     exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(RECEIVER_ADDR)
    # filename = sys.argv[1]
    receive_snw(sock)
    print(file_data)
    file = open("CS5313\\Homework 2\\receiver_bio.txt", "wb")
    for i in range(len(file_data)):
         file.write(file_data[i])
    file.close()
    # Close the socket
    sock.close()