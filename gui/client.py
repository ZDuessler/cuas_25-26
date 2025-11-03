# Written by Geoffrey Stentiford
# This file has zero LLM output in it

from __future__ import annotations
import sys
import multiprocessing
from multiprocessing.sharedctypes import SynchronizedArray, Synchronized
from typing import Tuple, List

SOCKET = "/tmp/ac_bridge"

standalone: bool = False # True if client.py ran directly

# Shared with child process
dVals: SynchronizedArray[float] = multiprocessing.Array('d', 5)
rVals: SynchronizedArray[float] = multiprocessing.Array('d', 5)
mode: Synchronized[int] = multiprocessing.Value('i')
timestamp: Synchronized[float] = multiprocessing.Value('d')
state: SynchronizedArray[int] = multiprocessing.Array('i', 3)

state[0] = 0 # connection down
state[1] = 1 # spin

rogue: List[Tuple[float, float]] = list()
disco: List[Tuple[float, float]] = list()
timestamp.value = 0.0
last = 0.0

def internal_runner(dVals: SynchronizedArray[float], rVals: SynchronizedArray[float],
                    mode: Synchronized[int], state: SynchronizedArray[int],
                    timestamp: Synchronized[float], path: str):
    '''
    Runs in child process to wait for and parse incoming messagess
    '''
    import socket, json, time
    
    def conn_kill(conx: socket.socket):
        """
        Terminates a client instance
        """
        print("IPC UNIX socket connection closed")
        conx.shutdown(socket.SHUT_RDWR)
        conx.close()

    state[0] = 0 # connection down
    state[1] = 1 # module busy

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) # Open the socket
    connecting = True # True until successful connections
    while connecting:
        try:
            client.connect(path) # Attempt to connect
            connecting = False # Stop the loop
        except FileNotFoundError or ConnectionRefusedError:
                time.sleep(.25) # Wait before retry
    client.sendall(b"0") # Signal server that client is ready
    print(f"Connected on {path}")
    
    state[0] = 1 # connection up

    try:
        while state[1] == 1: # while spinning
            data = client.recv(1024) # Receive IPC message
            msg: Tuple[List[float], List[float], float, int] = tuple(json.loads(data)) # Parse (tuples are faster than lists)
            if standalone: # Print incoming data when in standalone mode
                print(msg)
            for i in range(5): # Loop through the five values
                dVals[i] = msg[0][i]
                rVals[i] = msg[1][i]
            timestamp.value = float(msg[2])
            mode.value = int(msg[3])
        conn_kill(client) # Kill client on intentional shutdown
    except KeyboardInterrupt:
        conn_kill(client) # Kill client on Ctrl+C
    except InterruptedError:
        conn_kill(client) # Kill client on signal
    finally:
        sys.exit(0)

def getVals():
    """
    Returns discovery and rogue coordinate pairs
    """
    global last
    if timestamp.value != last: # Bypass on no new value
        last = timestamp.value
        disco.append((dVals[0], dVals[1]))
        if rVals[0] != 0.0: # Rogue isn't always up
            rogue.append((rVals[0], rVals[1]))
    return disco, rogue

def clearVals():
    """
    Clears historical coordinaes
    """
    rogue.clear()
    disco.clear()

def getMode():
    """
    Gets mode of discovery drone
    """
    return mode.value

def getTimestamp():
    """
    Gets timestamp of most recent data
    """
    return timestamp.value

def isConnected():
    """
    Checks if client is connected to server
    """
    return True if state[0] == 1 else False

def stop():
    """
    Properly shuts down
    """
    unix_handler(None, None)

def unix_handler(sig, frame):
    '''
    Handles exit signals
    '''
    print("Terminating")
    state[1] = 0 # stop
    state[0] = 0 # connection down
    try:
        p1.terminate() # Ask nicely
    finally:
        try:
            p1.kill() # Force shutdown
        finally:
            p1.join() # Wait for shutdown
            p1.close() # Release resources
    sys.exit(0)

def start():
    """
    Start the IPC client
    """
    import signal
    global p1
    
    p1 = multiprocessing.Process(None, internal_runner, None,
                                 (dVals, rVals, mode, state, timestamp, SOCKET), daemon=True)

    signal.signal(signal.SIGINT, unix_handler) # Shut down on Ctrl+C
        
    p1.start() # Start child process
    
# Allows running this script directly for testing
if __name__ == "__main__":
    standalone = True
    start()
    p1.join()
