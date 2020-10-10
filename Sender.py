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

    # The sending mechanism is within a try-catch block in order to
    # catch any connection that is closed unexpectedly or that fails.
    try:

        # We attempt to open up the file as our payload
        try:
            payload = read_file(filename)
        except FileNotFoundError:
            print("File to send was not found. Data transfer terminated.")
            return

        # The payload is turned into packets and the first sequence number
        # is initialized
        packets = package_payload(payload)
        nextseqnum = 0

        # The auxiliary thread is begun. It will listen for ACKs from the
        # recipient while this main thread sends the payload
        _thread.start_new_thread(receive_gbn, (sock,))

        # Main loop. While we have packets to send, it will attempt to send
        # packets. 
        while base < len(packets):

            # Check if the timer has begun or if it has timed out. If so,
            # set the next sequence number to be sent back to the base of
            # the transmission window and stop the timer
            with mutex:
                if timer.timeout() or not timer.running():
                    nextseqnum = base
                    timer.stop()

            # If the sending window is not full, we send a packet. If the
            # packet we're sending is at the base of the window, we start
            # the timer to calculate a timeout
            if (nextseqnum < base + WINDOW_SIZE) and (nextseqnum < len(packets)):
                    udt.send(packets[nextseqnum], sock, RECEIVER_ADDR)
                    print("Sent packet: {}".format(nextseqnum))
                    
                    if nextseqnum == base:
                        timer.start()
                    
                    nextseqnum += 1
    except ConnectionError:
        print("Connection failed.")
        return

    # Here, we begin the timer to be used by auxiliary thread to close the
    # upcoming loop
    with mutex:
        timer.start()

    # Signal auxiliary to stop listening for input from the recipient
    while timer.running():
        udt.send(packet.make(-1, b'FIN'), sock, SENDER_ADDR)
        time.sleep(SLEEP_INTERVAL)
    
    # We begin the timer again to know when the auxiliary thread finished
    # as a result of a closed connection
    with mutex:
        timer.start()

    # non-blocking loop that sends FIN packets to the recipient
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

    # We have to make sure the connection is active, so the receiving logic
    # of the sender is within this try-catch block
    try:
        while True:

            # We wait to receive a packet
            ack, addr = udt.recv(sock)

            # To avoid race conditions with the sending mechanism, we use the mutex
            with mutex:

                # If the address of the sender is from the recipient or ours,
                # extract the data
                if addr == RECEIVER_ADDR or addr == SENDER_ADDR:
                    seqnum, payload = packet.extract(ack)

                    # If the packet is from us and the payload is FIN,
                    # we signal the end of the receiving process to the main thread
                    # and exit the listening loop
                    if addr == SENDER_ADDR and payload == b'FIN':
                        print("File sent successfully.\nClosing connection...")
                        timer.stop()
                        break
                    
                    # If we receive an ACK for a packet in the window, move the
                    # base up to the packet following the ACK's sequence number
                    if seqnum >= base and payload == b'ACK':
                        base = seqnum + 1
                        timer.stop()
    except ConnectionError as e:
        print(e)

    # Here, we can assume we already sent the file and are waiting for the
    # client to close the connection. With a try-catch, we simply wait for the
    # exception to happen, stop the time to signal the sender, and print
    # that the connection was closed successfully
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
