from whisper_live.client import Client
# client = TranscriptionClient("127.0.0.1", "9090", is_multilingual=False, lang="en", translate=False)
# client(streaming=True)

from fastapi import FastAPI, WebSocket, Depends
import audioop
import json
import logging


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

class WSClient:
    def __init__(self, host, port, is_multilingual=False, lang=None, translate=False):
        self.client = Client(host, port, is_multilingual, lang, translate)
        
    def __call__(self, audio=None):
        print("[INFO]: Waiting for server ready ...")
        while not Client.RECORDING:
            if Client.WAITING:
                self.client.close_websocket()
                return
            pass
        print("[INFO]: Server Ready!")

    async def websocket_endpoint(self, websocket: WebSocket):

        await websocket.accept()
        audio_bytes_buffer = bytearray()
        try:
            while True:
                message = await websocket.receive_text()
                packet = json.loads(message)
                # print (packet)
                if packet["event"] == "start":
                    print("Streaming is starting")
                elif packet["event"] == "stop":
                    print("Streaming has stopped")
                    break
                elif packet["event"] == "media":
                    audio = bytes.fromhex(packet["media"]["payload"])
                    audio = audioop.ulaw2lin(audio, 2)
                    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                    audio_bytes_buffer.extend(audio)
                    self.client.handle_stream(audio)

        except Exception as e:
            print(f"WebSocket closed unexpectedly: {e}")



def get_client():
    client = WSClient("127.0.0.1", "9090", is_multilingual=False, lang="en", translate=False)
    client()
    return client


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket, client: WSClient = Depends(get_client)):
    await client.websocket_endpoint(websocket)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


