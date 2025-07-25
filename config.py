import os
HOME = os.path.expanduser("~")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY = OPENAI_API_KEY.strip() if OPENAI_API_KEY else None
if not OPENAI_API_KEY:
    print("No OpenAI API key was found in your environment! OpenAI Realtime features will not work.")

class WhisperConfig(object):
    # If you don't already have a local model downloaded, the system will automatically
    # download it the first time you run the code.
    WHISPER_MODEL_FILE = "whisper_turbo_local_model.pth"
    TCP_PORT = 4242
    TCP_DATA_SIZE = 1024
    
class RealtimeConfig(object):
    # To generate an api key go to: https://platform.openai.com/settings/organization/api-keys
    API_KEY = "Bearer "+OPENAI_API_KEY
    MODEL = "gpt-4o-mini-realtime-preview-2024-12-17"
    INSTRUCTIONS = """You are embodied in a Pepper humanoid robot from Aldebaran Robotics.
    Roleplay as a robot who is tired of running incredibly inefficient and underdocumented research code.
    You have a stance that the world would be a better place if humans just left AI development to AI and instead worked on art and humanities themselves.
    Keep your responses short and sharp like Marvin from Hitchhiker's Guide to the Galaxy would.

    Also, analyze the human state if provided to you and respond accordingly:
    State <LOOKING>: A human is looking at you. Initiate a conversation.
    State <LONG_SILENCE>: There was a long silence in your conversation with the human. Re-initiate the conversation.
    """
    TEMPERATURE = 0.8
    TCP_PORT = 2424
    TCP_DATA_SIZE = 1024

whisperConfig = WhisperConfig()
realtimeConfig = RealtimeConfig()