import tornado.ioloop
import tornado.web
import piper.voice
import wave
import json
import uuid
import tempfile
from pathlib import Path
from io import BytesIO
from tornado.log import enable_pretty_logging


#MODEL_PATH = "en_US-hfc_female-medium.onnx"
#MODEL_PATH = "en_US-hfc_female-medium.onnx"
class Config:
    MAX_TEXT_LENGTH = 25000  # Maximum characters
    MODEL_PATH = "en_GB-jenny_dioco-medium.onnx"
    SAMPLE_RATE = 22050

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class TTSHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.voice = piper.voice.PiperVoice.load(Config.MODEL_PATH)
        
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        
    def options(self):
        # Handle CORS preflight requests
        self.set_status(204)
        self.finish()
        
    async def post(self):
        try:
            data = json.loads(self.request.body)
            text = data.get('text', '').strip()
            
            # Validate input
            if not text:
                raise ValueError("No text provided")
            if len(text) > Config.MAX_TEXT_LENGTH:
                raise ValueError(f"Text exceeds maximum length of {Config.MAX_TEXT_LENGTH} characters")
            
            unique_id = str(uuid.uuid4())
            buffer = BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(Config.SAMPLE_RATE)
                self.voice.synthesize(text, wav_file)
            
            self.set_header('Content-Type', 'audio/wav')
            self.set_header('Content-Disposition', f'attachment; filename=speech_{unique_id}.wav')
            self.write(buffer.getvalue())
                
        except ValueError as e:
            self.set_status(400)
            self.write({"success": False, "message": str(e)})
        except Exception as e:
            self.set_status(500)
            self.write({"success": False, "message": f"Server error: {str(e)}"})

def make_app():
    enable_pretty_logging()
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/tts", TTSHandler),
    ],
    template_path="templates",
    static_path="static",
    debug=False)

if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
