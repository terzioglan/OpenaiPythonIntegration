import threading, time, sys
sys.path.append("../")
from lib.realtimeWebsocket import RealtimeAPI
from config import realtimeConfig as configuration
from lib.ServerClient import Server

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        config  = configuration,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()

    print("Establishing local TCP connection...")
    realtimeLocalServer = Server(
        host="localhost",
        port=configuration.TCP_PORT,
        size=configuration.TCP_SIZE
        )
    print("Done.")

    print("Initializing websocket session...")
    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)
    print("Done.")

    while True:
        try:
            data = realtimeLocalServer.receive()
            if data:
                print("Received request from local client.")
                print("Requesting response from realtime API.")
                realtimeWebsocket.requestResponse(data["message"])
                while(realtimeWebsocket.serverResponseQueue.empty()):
                    pass
                response = realtimeWebsocket.serverResponseQueue.get()
                print(f"Response received: {response}")
                print("Sending response to local client.")
                realtimeLocalServer.send( message = response )
            else:
                pass
        except KeyboardInterrupt:
            break

    realtimeWebsocket.stopWebsocket()
    websocketThread.join()
    print("Websocket stopped.")
    realtimeLocalServer.exit()
    sys.exit(0)
