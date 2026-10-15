import os
from PIL import Image
import metrics as m
import captioner as c

m.start_metrics_server(8000)
processor, model = c.load_model()

path = "sample_data/test.jpg"
img = Image.open(path)
for _ in range(3):
    with m.track_request("single", "127.0.0.1", "testsess"):
        print(c.caption_image(processor, model, img, "single",
                              "127.0.0.1", "testsess", os.path.getsize(path)))

input("Metrics live at http://localhost:8000/metrics. Press Enter to quit.")
