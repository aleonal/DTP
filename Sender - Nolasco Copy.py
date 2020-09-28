import socket
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

# Send using Stop_n_wait protocol
def send_snw(sock):
    # Fill out the code here
    global base
    global total_packets
    data = []
    seq = 0
    while (seq < 20):
        data.append(generate_payload(40).encode())
        seq = seq + 1
    seq = 0
    while (base < total_packets):
        with mutex:
            print ("base is",base)
        pkt = packet.make(base, file_data[base])
        print("Sending seq# ", base, "\n")
        udt.send(pkt, sock, RECEIVER_ADDR)
        time.sleep(TIMEOUT_INTERVAL)
    pkt = packet.make(base, "END".encode())
    while (base < 21):
        udt.send(pkt, sock, RECEIVER_ADDR)

# Send using GBN protocol
def send_gbn(sock):
    return

# Receive thread from stop-n-wait
def receive_snw(sock, pkt):
    # Fill here to handle acks
    global base
    global total_packets
    while (base < total_packets+1):
        print("starting udt recv\n")
        pkt, receiveraddr = udt.recv(sock)
        print("finished udt recv\n")
        seq, data = packet.extract(pkt)
        ackStr = data.decode()
        print("From: ", receiveraddr, ", Seq# ", seq, ackStr)
        with mutex:
            base = seq + 1
    return

# Receive thread fro GBN
def receive_gbn(sock):
    # Fill here to handle acks
    return



# Define a function for the thread
def print_time( threadName, delay):
   count = 0
   while count < 5:
      time.sleep(delay)
      count += 1
      print ("%s: %s" % ( threadName, time.ctime(time.time()) ))

# Main function
if __name__== '__main__':
        # if len(sys.argv) != 2:
    #     print('Expected filename as command line argument')
    #     exit()
    file = open("CS5313\\Homework 2\\bio.txt", "rb")

    byte = file.read(1)
    tempbytes = byte
    while byte:
        #print(tempbytes)
        byte = file.read(1)
        tempbytes = tempbytes + byte
        if len(tempbytes) == 512:
            file_data.append(tempbytes)
            total_packets = total_packets + 1
            print(tempbytes)
            tempbytes = b''
    if len(tempbytes) > 0:
        file_data.append(tempbytes)
        total_packets = total_packets + 1
        print(tempbytes)

    print("total packets = ",total_packets)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    # filename = sys.argv[1]
   

    # Create two threads as follows
    try:
        _thread.start_new_thread(send_snw, (sock, ))
    except:
        print ("Error: unable to start thread 1")

    try:
        _thread.start_new_thread(receive_snw, (sock, packet.make(0, "".encode()), ))
    except:
        print ("Error: unable to start thread 2")
    while (base < total_packets+1):
        pass
    
    sock.close()