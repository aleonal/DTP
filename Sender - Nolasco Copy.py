import socket
import sys
import _thread
import time
import string
import packet
import udt
import random
from timer import Timer

# Some already defined paramters
PACKET_SIZE = 512
RECEIVER_ADDR = ('localhost', 8080)
SENDER_ADDR = ('localhost', 9090)
SLEEP_INTERVAL = 0.05 # (In seconds)
TIMEOUT_INTERVAL = 0.5
WINDOWS_SIZE = 4

#You can use some shared resources over the two threads
base = 0
mutex = _thread.allocate_lock()
timer = Timer(TIMEOUT_INTERVAL)
total_packets = 0
file_data = []

# Need to have two threads: one for sending and another for receiving ACKs

# Generate randome payload of any length
def generate_payload(length=10):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str 

# Reads file in working directory as bytes
def read_file(filename):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except OSError as e:
        raise FileNotFoundError(e)

# Given a payload, it returns the payload as a stack of packets ready to send using a
# framed mechanism
def package_payload(payload):
    # We split up the payload into packets with packet size, while keeping track of the
    # sequence number and the data to turn into a packet
    packets = []
    packet_data = b''
    seq_num = 0

    for i in range(len(payload)):
        packet_data = packet_data + payload[i:i+1]
        if len(packet_data) == PACKET_SIZE:
            packets.append(packet.make(seq_num, packet_data))
            packet_data = b''
            seq_num += 1
    if len(packet_data) > 0:
        packets.append(packet.make(seq_num, packet_data))
    
    return packets

# Send using Stop_n_wait protocol
def send_snw(sock):
    # Fill out the code here
    global base
    global timer
    global mutex
    try:
        try:
            payload = read_file(filename)
        except FileNotFoundError:
            print("File to send was not found. Data transfer terminated.")
            return

        packets = package_payload(payload)
        nextseqnum = 0

        _thread.start_new_thread(receive_snw, (sock, packets[len(packets)-1],))

        while base < len(packets)-1:
            with mutex:
                if timer.timeout():
                    timer.stop()
                    print("Packet timed out. Resending packet")
                    udt.send(packets[base], sock, RECEIVER_ADDR)
                    print("Sent packet: {}\n".format(base))
                    timer.start()
                    #nextseqnum = base
                    
                elif not timer.running():
                    udt.send(packets[base], sock, RECEIVER_ADDR)
                    print("Sent packet: {}\n".format(base))
                    timer.start()
                    #nextseqnum += 1                    
                #else:
                #    print("packet is "+base)
        print("File sent succesfully")
        while base != -1:
            udt.send(packet.make(-1, b'FIN'), sock, RECEIVER_ADDR)
            time.sleep(TIMEOUT_INTERVAL)
    except ConnectionResetError as e:
        mutex.release()
        print(e)

# Send using GBN protocol
def send_gbn(sock):
    return

# Receive thread from stop-n-wait
def receive_snw(sock, pkt):
    # Fill here to handle acks
    global base
    global timer
    global mutex
    ackedpackets = 0
    try:
        fseqnum, fpayload = packet.extract(pkt)
        while ackedpackets < fseqnum+1:
            ack, addr = udt.recv(sock)
            ackedpackets+=1

            with mutex:
                
                seqnum, payload = packet.extract(ack)
                base = seqnum + 1
                
                timer.stop()

    except ConnectionError as e:
        #mutex.release()
        print(e)

# Receive thread fro GBN
def receive_gbn(sock):
    # Fill here to handle acks
    return

# Main function
if __name__== '__main__':
    if len(sys.argv) != 2:
        print('Expected filename as command line argument')
        exit()    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    filename = sys.argv[1]
    send_snw(sock)
    sock.close()
