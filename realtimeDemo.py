import threading, time, sys
sys.path.append("../")
from lib.realtimeWebsocket import RealtimeAPI
from config import realtimeConfig as configuration
from lib.utils import GptCostTracker

if __name__ == "__main__":
    costTracker = GptCostTracker(model = configuration.MODEL)
    realtimeWebsocket = RealtimeAPI(
        config  = configuration,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()
    
    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            inputText = input("User:")
            if inputText == "exit":
                break
            tic = time.time()
            realtimeWebsocket.requestResponse(inputText)
            done = False
            while not done:
                try:
                    response = realtimeWebsocket.serverResponseQueue.get(timeout=1)
                except:
                    print("No response received yet, waiting...")
                else:
                    if response['type'] == "response.done":
                        done = True
            toc = time.time()
            print("Processing time: %.2fs" %(toc-tic))
            
            costTracker.computeCost(response=response['response'])
            
            if response["response"]["output"][0]["content"][0]["type"] == "text":
                print(response["response"]["output"][0]["content"][0]["text"],"\n")
            elif response["response"]["output"][0]["content"][0]["type"] == "audio":
                raise NotImplementedError("Audio response handling is not yet implemented.")
            else:
                print("unknown response type")

        except KeyboardInterrupt:
            break
    
    realtimeWebsocket.stopWebsocket()
    websocketThread.join()
    print("Websocket stopped.")
    sys.exit(0)
        