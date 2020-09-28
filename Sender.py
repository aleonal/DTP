import socket
import sys
import _thread
import time
import string
import packet
import udt
import random
from timer import Timer

# Some already defined parameters
PACKET_SIZE = 512
RECEIVER_ADDR = ('localhost', 8080)
SENDER_ADDR = ('localhost', 9090)
SLEEP_INTERVAL = 0.05 # (In seconds)
TIMEOUT_INTERVAL = 0.5
WINDOW_SIZE = 4

# You can use some shared resources over the two threads
# base = 0
# mutex = _thread.allocate_lock()
# timer = Timer(TIMEOUT_INTERVAL)

# Need to have two threads: one for sending and another for receiving ACKs

# Generate random payload of any length
def generate_payload(length=10):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))

    return result_str


# Send using Stop_n_wait protocol
def send_snw(sock):
	# Fill out the code here
    seq = 0
    while(seq < 20):
        data = generate_payload(40).encode()
        pkt = packet.make(seq, data)
        print("Sending seq# ", seq, "\n")
        udt.send(pkt, sock, RECEIVER_ADDR)
        seq = seq+1
        time.sleep(TIMEOUT_INTERVAL)
    pkt = packet.make(seq, "END".encode())
    udt.send(pkt, sock, RECEIVER_ADDR)

# Send using GBN protocol
def send_gbn(sock):
    # [0, base-1] corresponds to packets already ACK'd
    # [base, nextseqnum-1] corresponds to packets sent, not ACK'd
    # [nextseqnum, base+N-1] corresponds to packets than can be sent immediately
    # [base + N, ->] corresponds to packets that can't be sent until packed @ base is ACK'd
    # [0, (2 ** k) - 1] corresponds to range of sequence numbers

    # We get payload as a byte array
    payload = read_file()

    if payload is None:
        raise FileNotFoundError("File not found in working directory!")
        return

    # We then convert payload into a stack of packets
    packet_stack = package_payload(payload)
    
    return

def read_file():
    #3,460 b?
    filename = input("Enter the filename of the document you wish to send: ")

    try:
        with open(filename, 'rb') as f:
            return f.read()
    except OSError as e:
        print(e)
        return None

def package_payload(payload):
    # We split up the payload into packets with packet size, while keeping track of the
    # sequence number and the data to turn into a packet
    packets = []
    packet_data = []
    seq_num = 1

    for i in range(len(payload)):
        if (i + 1) % PACKET_SIZE == 0:
            packets.append(packet.make(seq_num, bytes(packet_data)))
            packet_data = []
            seq_num = i + 1
        else:
            packet_data.append(payload[i])

    # Data may not be a multiple of packet size, therefore we must send remaining data 
    # into a packet with the stored sequence number
    if len(packet_data) > 0:
        packets.append(packet.make(seq_num, bytes(packet_data)))

    return packets

# Receive thread for stop-n-wait
def receive_snw(sock, pkt):
    # Fill here to handle acks
    return

# Receive thread for GBN
def receive_gbn(sock):
    # Fill here to handle acks
    return

# Main function
if __name__ == '__main__':
    # if len(sys.argv) != 2:
    #     print('Expected filename as command line argument')
    #     exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)

    send_gbn(sock)
    sock.close()

    # # filename = sys.argv[1]
    # send_snw(sock)
    # sock.close()


