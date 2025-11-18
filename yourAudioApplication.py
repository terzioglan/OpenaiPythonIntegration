import sys, time
sys.path.append("../")
from config import realtimeConfig as realtimeConfiguration
from config import whisperConfig as whisperConfiguration
from lib.ServerClient import Client

RECORDINGS = [
    "./audioRecordings/goodbye-38072.mp3",
    "./audioRecordings/hello-46355.mp3",
    "./audioRecordings/thank-you-99932.mp3",
    "./audioRecordings/welcome-to-paradise-96902.mp3",
    "./audioRecordings/welcome-traveler-97167.mp3",
    ]

if __name__ == "__main__":
    realtimeLocalClient = Client(
        host='localhost',
        port=realtimeConfiguration.TCP_PORT,
        size=realtimeConfiguration.TCP_SIZE
        )
    whisperLocalClient = Client(
        host='localhost',
        port=whisperConfiguration.TCP_PORT,
        size=whisperConfiguration.TCP_SIZE
        )
    for recording in RECORDINGS:
        try:
            print(f"Processing: {recording}")
            audioFilePath = recording
            tic = time.time()
            whisperLocalClient.send(message = audioFilePath )
            transcription = whisperLocalClient.receive()["message"]
            
            print(f"User: {transcription}")
            realtimeLocalClient.send(message = transcription )
            response = realtimeLocalClient.receive()["message"]
            
            toc = time.time()
            print("Processing time: %.2fs" %(toc-tic))
            print(f"Response: {response['response']['output'][0]['content'][0]['text']}\n")
            time.sleep(1.0)
        except KeyboardInterrupt:
            break
    
    realtimeLocalClient.exit()
    whisperLocalClient.exit()
    sys.exit(0)
