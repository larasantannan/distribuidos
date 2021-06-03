# Python3 program imitating a clock server

from functools import reduce
from dateutil import parser
import ntplib
from time import ctime
import threading
import datetime
import socket
import time


# datastructure used to store client address and clock data
client_data = {}
K = 1

# Return NTP in seconds
def getNTP():
    c = ntplib.NTPClient()
    response = c.request('time.google.com', version=3)
    return parser.parse(ctime(response.tx_time))


# client thread function used to send time at client side
def startSendingTime(listening_client):

    while True:
        # provide server with clock time at the client
        listening_client.send(str(getNTP()).encode())

        print("Recent time sent successfully", end = "\n\n")

        time.sleep(0.001)


# client thread function used to receive synchronized time
def startReceivingTime(listening_client):

    while True:
        # receive data from the server
        Synchronized_time = parser.parse(listening_client.recv(1024).decode())

        print("HELP", listening_client.getpeername())

        print("Synchronized time at the process 2 is: " + str(Synchronized_time), end = "\n\n")


def startRecieveingClockTime(connector, address):
    
    while True:
        clock_time_string = connector.recv(1024).decode()
        clock_time = parser.parse(clock_time_string)
        clock_time_diff = getNTP()- clock_time

        print("Client time before syncronize", clock_time, "\n")

        if clock_time_diff.total_seconds() > K:
            synchronizeAllClocks()
        
        client_data[address] = {
            "clock_time": clock_time,
            "time_difference": clock_time_diff,
            "connector": connector,
        }

        print("Client Data updated with: "+ str(address), end = "\n\n")
        time.sleep(0.001)


''' master thread function used to open portal for
	accepting clients over given port '''
def startConnecting(main_socket):

    # fetch clock time at slaves / clients
    while True:
        # accepting a client / slave clock client
        master_slave_connector, addr = main_socket.accept()
        slave_address = str(addr[0]) + ":" + str(addr[1])

        print(slave_address + " got connected successfully")

        current_thread = threading.Thread(
            target=startRecieveingClockTime,
            args = (master_slave_connector, slave_address, )
        )

        current_thread.start()

# subroutine function used to fetch average clock difference
def getAverageClockDiff():

    current_client_data = client_data.copy()
    
    time_difference_list = list(client['time_difference'] for client_addr, client in client_data.items())

    sum_of_clock_difference = sum(time_difference_list, datetime.timedelta(0, 0))

    average_clock_difference = sum_of_clock_difference / len(client_data)

    return average_clock_difference


''' master sync thread function used to generate
	cycles of clock synchronization in the network '''
def synchronizeAllClocks():

    while True:

        print("New synchroniztion cycle started.")
        print("Number of clients to be synchronized: " + str(len(client_data)))

        if len(client_data) > 0:

            average_clock_difference = getAverageClockDiff()

            for client_addr, client in client_data.items():
                try:
                    synchronized_time = getNTP() + average_clock_difference

                    print("Client new syncronized time ", synchronized_time)

                    client['connector'].send(str(synchronized_time).encode())
                
                except Exception as e:
                    print("Something went wrong while sending synchronized time through " + str(client_addr))

        else:
            print("No client data. Synchronization not applicable.")
        
        print("\n\n")

        time.sleep(0.001)

# function used to Synchronize client process time
def connectToProccess(port):

    listening_client = socket.socket()

    # connect to the clock server on local computer
    connection = listening_client.connect_ex(('127.0.0.1', port))

    while connection is not 0:
        connection = listening_client.connect_ex(('127.0.0.1', port))

    # start sending time to server
    print("Starting to receive time from server\n")
    send_time_thread = threading.Thread(target = startSendingTime, args = (listening_client, ))

    send_time_thread.start()

    # start recieving synchronized from server
    print("Starting to recieving synchronized time from server\n")

    receive_time_thread = threading.Thread(target = startReceivingTime, args = (listening_client, ))
    receive_time_thread.start()


# function used to initiate the Clock Server / Master Node
def initiateClockServer():

    main_socket = socket.socket()
    main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print("Socket at master node created successfully\n")

    main_socket.bind(('', 8081))

    # Start listening to requests
    main_socket.listen(10)
    print("Clock server started...\n")

    # start making connections
    print("Starting to make connections...\n")
    main_socket_thread = threading.Thread(target = startConnecting, args = (main_socket, ))
    main_socket_thread.start()

    # start synchroniztion
    print("Starting synchronization parallely...\n")
    sync_thread = threading.Thread(target = synchronizeAllClocks, args = ())
    sync_thread.start()

    connectToProccess(8080)
    connectToProccess(8082)
    connectToProccess(8083)


# Driver function
if __name__ == '__main__':

	# Trigger the Clock Server
	initiateClockServer()
