import asyncio
import websockets
import ffmpeg
import json

SOCKET_SERVER_URI = "ws://127.0.0.1:8080/stream"

print("Starting ffmpeg command")
# Convert the audio file to 8kHz and perform mu-law encoding
input_audio = ffmpeg.input("./jfk.wav")
output_audio = ffmpeg.output(
    input_audio, "pipe:", format="mulaw", acodec="pcm_mulaw", ar="8000"
)
out, _ = ffmpeg.run(output_audio, capture_stdout=True, capture_stderr=True)
print("Finished ffmpeg command")

# Convert the audio data to bytes
audio_bytes = out

async def client():
    global space_pressed
    try:
        # Connect to the specific server
        print("Attempting to connect to server")
        async with websockets.connect(SOCKET_SERVER_URI) as ws:
            print("Connected to server")

            await ws.send(
                json.dumps(
                    {"event": "connected", "protocol": "Call", "version": "1.0.0"}
                )
            )

            await ws.send(
                json.dumps(
                    {
                        "event": "start",
                        "sequenceNumber": "2",
                        "start": {
                            "streamSid": "MZ18ad3ab5a668481ce02b83e7395059f0",
                            "accountSid": "AC123",
                            "callSid": "CA123",
                            "tracks": ["inbound", "outbound"],
                            "customParameters": {
                                "FirstName": "Jane",
                                "LastName": "Doe",
                                "RemoteParty": "Bob",
                            },
                            "mediaFormat": {
                                "encoding": "audio/x-mulaw",
                                "sampleRate": 8000,
                                "channels": 1,
                            },
                        },
                        "streamSid": "MZ18ad3ab5a668481ce02b83e7395059f0",
                    }
                )
            )
            # Loop playback on the audio file forever until the script is killed
            # Send the audio data as WebSocket messages
            for i in range(0, len(audio_bytes), 1024):
                # We are creating a message in the same format that Twilio uses.
                # The payload is the audio data encoded in base64.
                message = {
                    "event": "media",
                    "sequenceNumber": str(i // 1024 + 1),
                    "media": {
                        "track": "outbound",
                        "chunk": str(i // 1024 + 1),
                        "timestamp": str(i // 1024 * 125),
                        "payload": audio_bytes[i : i + 1024].hex(),
                    },
                    "streamSid": "MZ18ad3ab5a668481ce02b83e7395059f0",
                }
                # This sends the message over the WebSocket connection.
                await ws.send(json.dumps(message))
                # print("Message sent")
            await ws.send(
                json.dumps(
                    {
                        "event": "stop",
                        "streamSid": "MZ18ad3ab5a668481ce02b83e7395059f0",
                    }
                )
            )
            await ws.close()
    except Exception as e:
        print(f"Exception occurred: {e.__class__}")
        print(e)


asyncio.get_event_loop().run_until_complete(client())
