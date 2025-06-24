import json, queue, websocket, threading, time, sys
from lib.serverClient import Server
from config import realtimeConfig as configuration
# from lib.utils import GptCostTracker

class RealtimeAPI(object):
    def __init__(self, config):
        self.url = "wss://api.openai.com/v1/realtime?model="+config.MODEL
        self.headers = [
            "Authorization: " + config.API_KEY,
            "OpenAI-Beta: realtime=v1",
            "timestamp_granularities[]=word",
            "somepointless: ello"
        ]
        self.instructions = config.INSTRUCTIONS
        self.temperature = config.TEMPERATURE
        self.webSocket = None
        self.serverResponseQueue = queue.Queue()
        self.stopEvent = threading.Event()
        self.sessionCreated = False
        self.sessionUpdated = False
        self.modalities = config.MODALITIES

        # self.costTracker = GptCostTracker(model = config.MODEL)

        try:
            # self.logFile = open("log.json", "a", buffering=1)
            self.logFile = open("log.json", "w", buffering=1)
            self.logFile.write('// --- Log started ---\n')
            self.logFile.flush()
        except Exception as e:
            print(f"Error opening log file: {e}")

    def onOpen(self, webSocket):
        ''' This function is called once the websocket is opened. '''
        session_event = {
            "type": "session.update",
            "session": {
                "modalities": self.modalities,
                "instructions": self.instructions,
                "temperature": self.temperature
                # "timestamp_granularities": "word",
            }
        }
        self.webSocket.send(json.dumps(session_event))  # Send session event to realtime server

    def onMessage(self, webSocket, message):
        ''' This function is triggered when realtime server sends a response back. '''
        data = json.loads(message)
        json.dump(data, self.logFile, indent=4)
        self.logFile.write('\n')
        self.logFile.flush()
        if data['type'] == "response.done":
            self.serverResponseQueue.put(data)
        elif data['type'] == "response.audio.delta":
            self.serverResponseQueue.put(data)
        elif data['type'] == "session.created":
            self.sessionCreated = True
        elif data['type'] == "session.updated":
            self.sessionUpdated = True
            
    def runWebsocket(self):
        ''' Establish the websocket communication.'''
        self.webSocket = websocket.WebSocketApp(
                self.url,
                header=self.headers,
                on_open=self.onOpen,
                on_message=self.onMessage,
            )
        self.webSocket.run_forever()
    
    def stopWebsocket(self):
        if self.webSocket:
            self.webSocket.close()
        self.stopEvent.set()
        self.logFile.close()

    def requestResponse(self, input):
        ''' input text is sent to Realtime server, and the server is asked for a response'''                
        # Create the conversation item
        conversation_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": input
                    }
                ]
            }
        }
        # Trigger a response
        response_event = {
            "type": "response.create",
            "response": {
                "modalities": self.modalities,
            }
        }
        
        self.webSocket.send(json.dumps(conversation_event))
        self.webSocket.send(json.dumps(response_event))

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        model=configuration.MODEL,
        apiKey=configuration.API_KEY,
        instructions=configuration.INSTRUCTIONS,
        temperature=configuration.TEMPERATURE,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()

    realtimeLocalServer = Server(host="localhost", port=configuration.TCP_PORT, size=configuration.TCP_DATA_SIZE)

    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            data = realtimeLocalServer.receive(configuration.TCP_DATA_SIZE)
            realtimeWebsocket.requestResponse(data["message"])
            while(realtimeWebsocket.serverResponseQueue.empty()):
                pass
            realtimeLocalServer.send({"message":realtimeWebsocket.serverResponseQueue.get()})
        except KeyboardInterrupt:
            realtimeWebsocket.stopWebsocket()
            websocketThread.join()
            print("Websocket stopped.")
            realtimeLocalServer.exit()
            sys.exit(0)
        