# Voz IA gratuita y local: Chatterbox Multilingual (Resemble AI, licencia MIT), español.
# Timbre de referencia: voz es_ES "davefx" (dataset CC0), con prosodia natural y control de energía.
# Se ejecuta en su propio entorno (pide torch 2.6):
#   python -m venv cbenv && cbenv/bin/pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
#   cbenv/bin/pip install chatterbox-tts
#   cbenv/bin/python voice_chatterbox.py [s00 s03 ...]   -> voice/raw/<id>.wav
#   python3 voice.py   (con TTS_ENGINE=files) procesa, mide y alinea con Whisper
import os, sys, torch, torchaudio
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, plain
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

REF = os.environ.get("CB_REF", os.path.join(HERE, "voice", "ref_davefx.wav"))
EXAG = float(os.environ.get("CB_EXAG", 0.7))       # energía / expresividad
SEED = int(os.environ.get("CB_SEED", 7))
OUT = os.path.join(HERE, "voice", "raw"); os.makedirs(OUT, exist_ok=True)
torch.set_num_threads(os.cpu_count())
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
only = sys.argv[1:]
for sid, txt, _s, _p in SEGMENTS:
    if only and sid not in only: continue
    torch.manual_seed(SEED)
    wav = m.generate(plain(txt), language_id="es", audio_prompt_path=REF,
                     exaggeration=EXAG, cfg_weight=0.4, temperature=0.75)
    torchaudio.save(os.path.join(OUT, f"{sid}.wav"), wav, m.sr)
    print(sid, round(wav.shape[-1] / m.sr, 2), flush=True)
