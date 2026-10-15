"""All Prometheus metric definitions for the captioning app.

Defined once at import time. Python caches imported modules, so Streamlit's
script reruns do NOT redefine these (that would raise "Duplicated timeseries").
"""
import time
from contextlib import contextmanager

import psutil
from prometheus_client import (Counter, Gauge, Histogram, Info, Summary,
                               start_http_server)

from prometheus_client import (Counter, Gauge, Histogram, Info, Summary,
                               start_http_server, disable_created_metrics)
disable_created_metrics()  
MODES = ("single", "bulk")

# ----------------------------- Counters -----------------------------
# NOTE: prometheus_client appends "_total" to Counter names automatically.
IMAGES_PROCESSED = Counter(
    "caption_images_processed", "Images captioned, by mode and outcome",
    ["mode", "status"])
REQUESTS = Counter(
    "caption_requests", "User requests received, with client metadata",
    ["mode", "client_ip", "session_id"])
CLIENT_IMAGES = Counter(
    "caption_client_images", "Images processed per client",
    ["client_ip", "session_id"])
ERRORS = Counter(
    "caption_errors", "Errors by mode and exception type",
    ["mode", "error_type"])
UPLOAD_BYTES = Counter(
    "caption_upload_bytes", "Bytes of image data received", ["mode"])
WORDS = Counter(
    "caption_generated_words", "Words generated across all captions", ["mode"])
ZIP_SKIPPED = Counter(
    "caption_zip_skipped_files", "Files skipped inside uploaded ZIPs", ["reason"])

# ------------------------------ Gauges ------------------------------
ACTIVE_REQUESTS = Gauge(
    "caption_active_requests", "Requests currently being processed", ["mode"])
BULK_PENDING = Gauge(
    "caption_bulk_pending_images", "Images still waiting in the current bulk batch")
BULK_PROGRESS = Gauge(
    "caption_bulk_progress_ratio", "Progress of current bulk batch (0 to 1)")
LAST_INFERENCE = Gauge(
    "caption_last_inference_seconds", "Duration of the most recent inference", ["mode"])
MODEL_LOADED = Gauge("caption_model_loaded", "1 if the model is loaded, else 0")
MODEL_LOAD_SECONDS = Gauge("caption_model_load_seconds", "Time taken to load the model")
MODEL_MEMORY_BYTES = Gauge(
    "caption_model_memory_bytes", "Memory taken by the model's parameters")
APP_START = Gauge("caption_app_start_time_seconds", "Unix time the app started")
APP_START.set_to_current_time()

# Evaluated at scrape time, so they are always fresh.
_proc = psutil.Process()
_proc.cpu_percent(interval=None)  # prime the counter; first call returns 0
PROCESS_RSS = Gauge("caption_process_rss_bytes", "Resident memory of the app process")
PROCESS_RSS.set_function(lambda: _proc.memory_info().rss)
PROCESS_CPU = Gauge(
    "caption_process_cpu_percent",
    "CPU use of the app process (100 = one full core, can exceed 100)")
PROCESS_CPU.set_function(lambda: _proc.cpu_percent(interval=None))

APP_INFO = Info("caption_app", "Static application metadata")

# ---------------------------- Histograms ----------------------------
INFERENCE_SECONDS = Histogram(
    "caption_inference_duration_seconds", "Model generate() time per image",
    ["mode"], buckets=(0.25, 0.5, 0.75, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.75, 2, 3, 5, 8, 13, 20))
REQUEST_SECONDS = Histogram(
    "caption_request_duration_seconds", "End-to-end time per user request",
    ["mode"], buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300, 600))
IMAGE_BYTES = Histogram(
    "caption_image_size_bytes", "Size of uploaded images",
    buckets=(1e4, 5e4, 1e5, 5e5, 1e6, 2e6, 5e6, 1e7))
BULK_BATCH_SIZE = Histogram(
    "caption_bulk_batch_size_images", "Images per bulk ZIP",
    buckets=(1, 2, 5, 10, 20, 50, 100))

# ----------------------------- Summaries ----------------------------
# Python's Summary exposes only <name>_count and <name>_sum (no quantiles).
PREPROCESS_SECONDS = Summary(
    "caption_preprocess_duration_seconds", "Image preprocessing time", ["mode"])
CAPTION_CHARS = Summary(
    "caption_text_length_chars", "Length of generated captions", ["mode"])
IMAGE_PIXELS = Summary(
    "caption_image_pixels", "Pixel count of input images", ["mode"])

# Pre-create label combinations so series exist (at 0) from startup.
# Without this, rate() and "no data" panels misbehave until first use.
for _m in MODES:
    INFERENCE_SECONDS.labels(mode=_m)
    REQUEST_SECONDS.labels(mode=_m)
    PREPROCESS_SECONDS.labels(mode=_m)
    CAPTION_CHARS.labels(mode=_m)
    IMAGE_PIXELS.labels(mode=_m)
    ACTIVE_REQUESTS.labels(mode=_m).set(0)
    LAST_INFERENCE.labels(mode=_m).set(0)
    UPLOAD_BYTES.labels(mode=_m)
    WORDS.labels(mode=_m)
    for _s in ("success", "error"):
        IMAGES_PROCESSED.labels(mode=_m, status=_s)
MODEL_LOADED.set(0)
BULK_PENDING.set(0)
BULK_PROGRESS.set(0)


@contextmanager
def track_request(mode, client_ip, session_id):
    """Wrap one user action (a single upload or a whole ZIP)."""
    REQUESTS.labels(mode=mode, client_ip=client_ip, session_id=session_id).inc()
    ACTIVE_REQUESTS.labels(mode=mode).inc()
    start = time.perf_counter()
    try:
        yield
    finally:
        REQUEST_SECONDS.labels(mode=mode).observe(time.perf_counter() - start)
        ACTIVE_REQUESTS.labels(mode=mode).dec()


_server_started = False


def start_metrics_server(port=8000):
    """Expose /metrics on a separate port. Safe to call more than once."""
    global _server_started
    if not _server_started:
        start_http_server(port)
        _server_started = True
