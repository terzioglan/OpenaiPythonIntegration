import time, sys
sys.path.append("../")
from config import realtimeConfig as configuration
from lib.ServerClient import Client

if __name__ == "__main__":
    realtimeLocalClient = Client(
        host=configuration.TCP_HOST,
        port=configuration.TCP_PORT,
        size=configuration.TCP_SIZE
        )
    while True:
        try:
            inputText = input("User:")
            if inputText == "exit":
                break
            tic = time.time()
            realtimeLocalClient.send( message = inputText )
            response = realtimeLocalClient.receive()["message"]
            toc = time.time()
            
            print("Processing time: %.2fs" %(toc-tic))
            print(f"\nResponse:{response['response']['output'][0]['content'][0]['text']}")
        except KeyboardInterrupt:
            break
    sys.exit(0)
        