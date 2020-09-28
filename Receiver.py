# receiver.py - The receiver in the reliable data transer protocol
import packet
import socket
import sys
import udt

RECEIVER_ADDR = ('localhost', 8080)

# Receive packets from the sender w/ GBN protocol
def receive_gbn(sock):
    expected = 0
    packets = {}
    
    while True:
        p, addr = udt.recv(sock)
        seq_num, payload = packet.extract(p)

        print("Expecting {}. Received {}".format(expected, seq_num))
        
        if seq_num == -1 and payload.decode() == 'FIN':
            break

        if seq_num == expected:
            udt.send(packet.make(expected, b'ACK'), sock, addr)
            print("ACKING {}".format(expected))
            packets[str(seq_num)] = payload
            expected += 1
        else:
            if str(seq_num) in packets:
                print("RE-ACKING {}".format(seq_num))
                udt.send(packet.make(seq_num, b'ACK'), sock, addr)

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