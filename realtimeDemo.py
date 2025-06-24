import threading, time, sys, base64, json
sys.path.append("../")
from lib.realtimeWebsocket import RealtimeAPI
from lib.whisperLocal import WhisperAPI, WhisperAPI_timestamped
from config import realtimeConfig as configuration
from config import whisperConfig as whisperConfiguration
from lib.utils import GptCostTracker
from lib.utils import pcm16_to_audiosegment

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
    
    # whisperApi = WhisperAPI(whisperModelPath=whisperConfiguration.WHISPER_MODEL_FILE,)
    whisperApi = WhisperAPI_timestamped(whisperModelPath=whisperConfiguration.WHISPER_MODEL_FILE,)
    
    while True:
        pcmSegments = []
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
                    if response['type'] == "response.audio.delta":
                        pcmSegments.append(base64.b64decode(response["delta"]))
            toc = time.time()
            print("Processing time: %.2fs" %(toc-tic))
            
            costTracker.computeCost(response=response['response'])
            
            if response["response"]["output"][0]["content"][0]["type"] == "text":
                print(response["response"]["output"][0]["content"][0]["text"],"\n")
            elif response["response"]["output"][0]["content"][0]["type"] == "audio":
                print(response["response"]["output"][0]["content"][0]["transcript"],"\n")
                audio_segments = [pcm16_to_audiosegment(chunk) for chunk in pcmSegments]
                final_audio = sum(audio_segments)
                final_audio.export("output.wav", format="wav")
                tic = time.time()
                transcription = whisperApi.transcribeAudioRawOut("output.wav")
                toc = time.time()
                print("Transcription time: %.2fs" %(toc-tic))
                with open("log.json",'a') as logFile:
                    json.dump(transcription, logFile, indent=4)
                    logFile.write('\n')
                    logFile.flush()

            else:
                print("unknown response type")

        except KeyboardInterrupt:
            break
    
    realtimeWebsocket.stopWebsocket()
    websocketThread.join()
    print("Websocket stopped.")
    sys.exit(0)
        