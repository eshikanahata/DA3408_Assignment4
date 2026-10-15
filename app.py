import io
import time
import uuid
import zipfile

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

import captioner as c
import metrics as m

st.set_page_config(page_title="CPU Image Captioning", layout="wide")

METRICS_PORT = 8000
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
MAX_ZIP_IMAGES = 100              
MAX_IMAGE_BYTES = 10 * 1024 * 1024  


@st.cache_resource(show_spinner="Loading model (first run only)...")
def init():
    m.start_metrics_server(METRICS_PORT)
    return c.load_model()


processor, model = init()

if "sid" not in st.session_state:
    st.session_state.sid = uuid.uuid4().hex[:8]  
SID = st.session_state.sid


def get_client_ip() -> str:
    try:
        ip = getattr(st.context, "ip_address", None)
        if ip:
            return ip.replace("::ffff:","")
        xff = st.context.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
    except Exception:
        pass
    return "unknown"


IP = get_client_ip()


def record_failure(mode: str, exc: Exception):
    m.IMAGES_PROCESSED.labels(mode=mode, status="error").inc()
    m.ERRORS.labels(mode=mode, error_type=type(exc).__name__).inc()

def run_single(file):
    data = file.getvalue()
    with m.track_request("single", IP, SID):
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except (UnidentifiedImageError, OSError) as e:
            record_failure("single", e)
            st.error(f"Could not read image: {e}")
            return None
        try:
            return c.caption_image(processor, model, img, "single",
                                   IP, SID, size_bytes=len(data))
        except Exception as e:  # already counted inside caption_image
            st.error(f"Captioning failed: {e}")
            return None


def run_bulk(zfile):
    rows = []
    with m.track_request("bulk", IP, SID):
        try:
            zf = zipfile.ZipFile(io.BytesIO(zfile.getvalue()))
        except zipfile.BadZipFile as e:
            record_failure("bulk", e)
            st.error("That is not a valid ZIP file.")
            return rows

        todo = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            base = info.filename.rsplit("/", 1)[-1]
            if info.filename.startswith("__MACOSX") or base.startswith("."):
                m.ZIP_SKIPPED.labels(reason="hidden").inc()
            elif not base.lower().endswith(IMAGE_EXTS):
                m.ZIP_SKIPPED.labels(reason="not_image").inc()
            elif info.file_size > MAX_IMAGE_BYTES:
                m.ZIP_SKIPPED.labels(reason="too_large").inc()
            else:
                todo.append(info)

        if len(todo) > MAX_ZIP_IMAGES:
            m.ZIP_SKIPPED.labels(reason="over_limit").inc(len(todo) - MAX_ZIP_IMAGES)
            todo = todo[:MAX_ZIP_IMAGES]

        total = len(todo)
        if total == 0:
            st.warning("No usable images found in the ZIP.")
            return rows

        m.BULK_BATCH_SIZE.observe(total)
        m.BULK_PENDING.set(total)
        m.BULK_PROGRESS.set(0)
        bar = st.progress(0.0, text=f"0 / {total}")
        try:
            for i, info in enumerate(todo, 1):
                data = zf.read(info)
                name = info.filename
                t0 = time.perf_counter()
                try:
                    img = Image.open(io.BytesIO(data))
                except (UnidentifiedImageError, OSError) as e:
                    record_failure("bulk", e)
                    rows.append({"file": name, "caption": "ERROR: unreadable", "seconds": 0})
                else:
                    try:
                        cap = c.caption_image(processor, model, img, "bulk",
                                              IP, SID, size_bytes=len(data))
                        rows.append({"file": name, "caption": cap,
                                     "seconds": round(time.perf_counter() - t0, 2)})
                    except Exception as e:  # already counted in caption_image
                        rows.append({"file": name, "caption": f"ERROR: {type(e).__name__}",
                                     "seconds": 0})
                m.BULK_PENDING.set(total - i)
                m.BULK_PROGRESS.set(i / total)
                bar.progress(i / total, text=f"{i} / {total}")
        finally:
            m.BULK_PENDING.set(0)
    return rows

st.title("CPU Image Captioning")
st.caption(f"Model: {c.MODEL_NAME} | metrics on port {METRICS_PORT} | session {SID}")

tab_single, tab_bulk = st.tabs(["Single image", "Bulk (ZIP)"])

with tab_single:
    up = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp", "bmp"],
                          key="single_up")
    if up:
        st.image(up, width=400)
        if st.button("Generate caption", key="single_btn"):
            with st.spinner("Running inference on CPU..."):
                cap = run_single(up)
            if cap:
                st.success(cap)

with tab_bulk:
    zup = st.file_uploader("Upload a ZIP of images", type=["zip"], key="bulk_up")
    if zup and st.button("Caption all images", key="bulk_btn"):
        st.session_state.bulk_rows = run_bulk(zup)
    rows = st.session_state.get("bulk_rows")
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False),
                           "captions.csv", "text/csv")
