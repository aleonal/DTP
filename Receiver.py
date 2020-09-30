# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)

# Receive packets from the sender w/ GBN protocol
def receive_gbn(sock):
    previous = -1
    packets = []
    
    while True:
        p, addr = udt.recv(sock)
        seq_num, payload = packet.extract(p)

        print("Received packet: {}".format(seq_num))

        if seq_num == -1 and payload == b'FIN':
            break

        if seq_num == previous + 1:
            udt.send(packet.make(seq_num, b'ACK'), sock, addr)
            print("Acked packet: {}\n".format(seq_num))
            packets.append((seq_num, payload))
            previous += 1
        else:
            if len(packets) > 0:
                udt.send(packet.make(packets[-1][0], b'ACK'), sock, addr) 
                print("Re-acked packet: {}\n".format(packets[-1][0]))

    return packets


# Receive packets from the sender w/ SR protocol
def receive_sr(sock, windowsize):
    # Fill here
    return

# Receive packets from the sender w/ Stop-n-wait protocol
def receive_snw(sock):
   endStr = ''
   while endStr!='END':
       pkt, senderaddr = udt.recv(sock)
       seq, data = packet.extract(pkt)
       endStr = data.decode()
       print("From: ", senderaddr, ", Seq# ", seq, endStr)

# Main function
if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print('Expected filename as command line argument')
    #     exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(RECEIVER_ADDR)

    print("Waiting for data...")
    p = receive_gbn(sock)
    for b in p:
        print("{}\n\n".format(b))

    # filename = sys.argv[1]
    # receive_snw(sock)
    #sock.close()