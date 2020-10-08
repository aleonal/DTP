Jose Antoine Leon Cordero
Francisco Nolasco
CS 5313
Testing/Running Sender.send_snw, Sender.receive_snw, and Reciever.receive_snw

The stop and wait protocols are demonstrated in the 3 methods mentioned above.  They are located in the files Sender.py and Receive.py.  

1) Run Receiver.py from the command line or terminal.  You must pass in the name of the file that you want to store the received packets in.  An example of this is copied below:
C:\>"c:/...PATH.../python.exe" "c:/...PATH.../Receiver.py" "c:/...PATH.../receiver_bio.txt"
Nothing will be displayed until you run Sender.py in the next step

2) From a different command line or terminal on the same machine, run Sender.py and pass in the name of the file you wish to send.  An example of this is copied below:
C:\> "C:/...PATH.../python.exe" "c:/...PATH.../Sender.py"  "c:/...PATH.../bio.txt" 

Each terminal window will then display which packets have been received and which have been acknowledged.  When Receiver.py exits you can open the file you specified as the output file.