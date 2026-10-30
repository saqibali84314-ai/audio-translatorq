from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from groq import Groq
import yt_dlp, os, asyncio, edge_tts

app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.post("/translate")
async def translate(url: str, bitrate: str = "6k", speed: float = 1.0):
    try:
        ydl_opts = {'format': 'ba[ext=m4a]/ba[ext=webm]/ba', 'outtmpl': 'temp.m4a'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open("temp.m4a", "rb") as audio_file:
            translation = client.audio.translations.create(
                file=("temp.m4a", audio_file.read()),
                model="whisper-large-v3",
            )
        english_text = translation.text
        os.remove("temp.m4a")

        communicate = edge_tts.Communicate(english_text, "en-US-ChristopherNeural")
        await communicate.save("raw_speech.mp3")

        filter_str = f"-filter:a atempo={speed}" if speed != 1.0 else ""
        os.system(f"ffmpeg -y -i raw_speech.mp3 {filter_str} -c:a libopus -b:a {bitrate} -ac 1 output.opus")

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
def download():
    return FileResponse("output.opus", media_type="audio/opus", filename="translated.opus")
