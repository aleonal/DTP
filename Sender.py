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

# Changed 'localhost' to IP address, since replies are not automatically translated back to
# localhost
RECEIVER_ADDR = ('127.0.0.1', 8080)
SENDER_ADDR = ('127.0.0.1', 9090)

SLEEP_INTERVAL = 0.05 # (In seconds)
TIMEOUT_INTERVAL = 0.5
WINDOW_SIZE = 4

# You can use some shared resources over the two threads
base = 0
mutex = _thread.allocate_lock()
timer = Timer(TIMEOUT_INTERVAL)
total_packets = 0
file_data = []

# Need to have two threads: one for sending and another for receiving ACKs

# Generate random payload of any length
def generate_payload(length=10):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))

    return result_str

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
  # start another thread to receive the ACKs from Receiver.py
        _thread.start_new_thread(receive_snw, (sock, packets[len(packets)-1],))
#loop to send packets starting at 0
        while base < len(packets)-1:
            # use mutex to prevent base from changing values by receive_snw mid-loop
            with mutex:
                #check to see if the timer has timed out.  this means ACK wasn't received
                # and the packet needs to be resent, and the timer restarted
              
                if timer.timeout():
                    timer.stop()
                    print("Packet timed out. Resending packet")
                    udt.send(packets[base], sock, RECEIVER_ADDR)
                    print("Sent packet: {}\n".format(base))
                    timer.start()
                    #nextseqnum = base  (leftover debugging code)
                # the else means the timer has not timed out, so 
                #check to see if a timer is NOT running
                # this means a packet is being sent for the first time
                # the time is started
                
                elif not timer.running():
                    udt.send(packets[base], sock, RECEIVER_ADDR)
                    print("Sent packet: {}\n".format(base))
                    timer.start()
                    # the following 3 lines are not needed because the only case left is that the timer is running. no action is needed while waiting for the ACK
                    #nextseqnum += 1 (leftover debugging code)                   
                #else: 
                #    print("packet is "+base)
                
         #after the loop exits, the file has been sent
        print("File sent succesfully")
        
        #now send a packet indicating that this is the last packet, with a sequence number of -1
        # continue sending it until receive_snw gets the ACK packet and updates base to the new value
        with mutex:
            if timer.running():
                timer.stop()
            timer.start()
            while not timer.timeout():
                if base != -1:
                    udt.send(packet.make(-1, b'FIN'), sock, RECEIVER_ADDR)
                    #time.sleep(TIMEOUT_INTERVAL)
                else:
                    return    
    except ConnectionResetError as e:
        mutex.release()
        print(e)

# Send using GBN protocol
def send_gbn(sock, filename):
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

        _thread.start_new_thread(receive_gbn, (sock,))

        while base < len(packets):
            with mutex:
                if timer.timeout() or not timer.running():
                    nextseqnum = base
                    timer.stop()

            if (nextseqnum < base + WINDOW_SIZE) and (nextseqnum < len(packets)):
                    udt.send(packets[nextseqnum], sock, RECEIVER_ADDR)
                    print("Sent packet: {}\n".format(nextseqnum))
                    
                    if nextseqnum == base:
                        timer.start()
                    
                    nextseqnum += 1
    except ConnectionError:
        print("Connection failed.")
        return

    # Move receiving thread to closing procedure
    with mutex:
        timer.start()

    while timer.running():
        udt.send(packet.make(-1, b'FIN'), sock, SENDER_ADDR)
        time.sleep(SLEEP_INTERVAL)
    
    with mutex:
        timer.start()

    # non-blocking signal 
    while timer.running():
        udt.send(packet.make(-1, b'FIN'), sock, RECEIVER_ADDR)

# Receive thread for stop-n-wait
def receive_snw(sock, pkt):
   
    global base
    global timer
    global mutex
    ackedpackets = 0
    #use try in case of connection error
    try:
        #get the sequence number and payload from the packet passed in as a parameter
        #this contains the final sequence number and payload data in that packet
        fseqnum, fpayload = packet.extract(pkt)
        
        #ackedpacket is counting the total ACKS from Receiver.py
        #this loop runs until an ACK is received that is one number higher
        #than previously received because there is one final packet sent
        #when the payload packets are done
        while ackedpackets < fseqnum+1:
            # unpack the ack packet received and increment ackpackets counter
            ack, addr = udt.recv(sock)
            ackedpackets+=1

            with mutex:
                #unpack the seqnum and payload and update base so send_snw
                #knows to send the next packet in the sequence
                seqnum, payload = packet.extract(ack)
                base = seqnum + 1
                #stop the timer because ACK was successfully reeived
                timer.stop()

    except ConnectionError as e:
        #mutex.release()
        print(e)

# Receive thread for GBN
def receive_gbn(sock):
    global base
    global timer
    global mutex

    try:
        while True:
            ack, addr = udt.recv(sock)
            with mutex:
                if addr == RECEIVER_ADDR or addr == SENDER_ADDR:
                    seqnum, payload = packet.extract(ack)

                    if addr == SENDER_ADDR and payload == b'FIN':
                        print("File sent successfully.\n\nClosing connection...\n")
                        timer.stop()
                        break
                    
                    if seqnum >= base and payload == b'ACK':
                        base = seqnum + 1
                        timer.stop()
    except ConnectionError as e:
        print(e)

    # Procedure to close thread and signal other process
    try:
        while True:
            waste = udt.recv(sock)
    except ConnectionError as e:
        with mutex:
            timer.stop()
    
    print("Connection closed successfully.") 

# Reads file at given directory as bytes
def read_file(filename):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except OSError as e:
        raise FileNotFoundError(e)

# Given a payload, it returns the payload as a stack of packets ready to send using a
# framed mechanism, with the first packet signaling the total amount of packets to be sent,
# excluding this header
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

# Main function
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Expected filename as command line argument')
        exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    
    filename = sys.argv[1]

    send_gbn(sock, filename)
    # send_snw(sock)
    
    sock.close()
