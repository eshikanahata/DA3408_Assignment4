import time
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

name = "Salesforce/blip-image-captioning-base"
processor = BlipProcessor.from_pretrained(name)
model = BlipForConditionalGeneration.from_pretrained(name) 
model.eval()

img = Image.open("sample_data/test.jpg").convert("RGB")  
t = time.time()
inputs = processor(img, return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=30)
print(processor.decode(out[0], skip_special_tokens=True))
print(f"Inference: {time.time() - t:.2f}s")
