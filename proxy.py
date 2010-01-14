# Useful for:
# - Pretending to be the intermud-3 router.

import sys, stackless, socket, os

listen_address = ("127.0.0.1", 18080)
forward_address = ("204.209.44.3", 8080)

def listener(addr):
    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listenSocket.bind(addr)
    listenSocket.listen(5)

    while True:
        incomingSocket, clientAddress = listenSocket.accept()
        stackless.tasklet(forwarder)(incomingSocket, clientAddress)

def forwarder(incomingSocket, clientAddress):
    #outgoingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #outgoingSocket.connect(forward_address)

    #stackless.tasklet(writer)(incomingSocket, outgoingSocket)

    # reader.    
    print clientAddress, "connection"
    while True:
        s = incomingSocket.recv(4096)
        if s == "":
            break
        print clientAddress, "skipping", len(s), "bytes"

        #try:
        #    outgoingSocket.send(s)
        #except socket.error:
        #    break

    #outgoingSocket.close()
    incomingSocket.close()
    print clientAddress, "disconnection"

def writer(incomingSocket, outgoingSocket):
    while True:
        s = outgoingSocket.recv(4096)
        if s == "":
            break

        try:
            incomingSocket.send(s)
        except socket.error:
            break

    outgoingSocket.close()
    incomingSocket.close()    

if __name__ == "__main__":
    dirPath = sys.path[0]
    if not len(dirPath):
        raise RuntimeError("Expected to find the directory the script was executed in in sys.path[0], but did not.")

    # Add the "contrib" directory to the path.
    contribDirPath = os.path.join(dirPath, "contrib")
    if os.path.exists(contribDirPath):
        sys.path.append(contribDirPath)

    import stacklesssocket
    stacklesssocket.install()

    stackless.tasklet(listener)(listen_address)
    stackless.run()
