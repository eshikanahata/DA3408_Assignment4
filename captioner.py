import platform
import time

import torch
import transformers
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

import metrics as m

MODEL_NAME = "Salesforce/blip-image-captioning-base"


def load_model():
    start = time.perf_counter()
    processor = BlipProcessor.from_pretrained(MODEL_NAME)
    model = BlipForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.eval()

    m.MODEL_LOAD_SECONDS.set(time.perf_counter() - start)
    m.MODEL_MEMORY_BYTES.set(
        sum(p.numel() * p.element_size() for p in model.parameters()))
    m.MODEL_LOADED.set(1)
    m.APP_INFO.info({
        "model": MODEL_NAME,
        "device": "cpu",
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": platform.python_version(),
    })
    return processor, model


def caption_image(processor, model, image: Image.Image, mode: str,
                  client_ip: str, session_id: str, size_bytes: int = 0) -> str:
    try:
        image = image.convert("RGB")
        m.IMAGE_PIXELS.labels(mode=mode).observe(image.width * image.height)
        if size_bytes:
            m.IMAGE_BYTES.observe(size_bytes)
            m.UPLOAD_BYTES.labels(mode=mode).inc(size_bytes)

        t0 = time.perf_counter()
        inputs = processor(image, return_tensors="pt")
        m.PREPROCESS_SECONDS.labels(mode=mode).observe(time.perf_counter() - t0)

        t1 = time.perf_counter()
        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=30)
        infer = time.perf_counter() - t1

        caption = processor.decode(out[0], skip_special_tokens=True)

        m.INFERENCE_SECONDS.labels(mode=mode).observe(infer)
        m.LAST_INFERENCE.labels(mode=mode).set(infer)
        m.CAPTION_CHARS.labels(mode=mode).observe(len(caption))
        m.WORDS.labels(mode=mode).inc(len(caption.split()))
        m.IMAGES_PROCESSED.labels(mode=mode, status="success").inc()
        m.CLIENT_IMAGES.labels(client_ip=client_ip, session_id=session_id).inc()
        return caption
    except Exception as e:
        m.IMAGES_PROCESSED.labels(mode=mode, status="error").inc()
        m.ERRORS.labels(mode=mode, error_type=type(e).__name__).inc()
        raise
