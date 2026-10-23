# CPU Image Captioning with Prometheus and Grafana observability

DA3408 Assignment 4. A CPU-only image-captioning app (Streamlit + BLIP) that is
fully instrumented with `prometheus_client`, scraped by Prometheus alongside
`node_exporter`, and visualised in a Grafana dashboard that follows the
"7 Commandments of Plotting".

Author: Eshika NAhata, DA24B004

## Architecture

```
Browser --> Streamlit app (:8501) --+--> /metrics (:8000) --+
                                    |                       +--> Prometheus (:9090) --> Grafana (:3000)
                  BLIP (CPU, torch) |   node_exporter (:9100)+
```

- `app.py`: Streamlit UI with **Single** (one image) and **Bulk** (ZIP of images) tabs.
- `captioner.py`: model loading and per-image inference, with the metrics recorded around it.
- `metrics.py`: every metric definition and the `/metrics` server (separate port, 8000).
- `prometheus.yml`: scrapes the app (`caption_app`), `node_exporter` (`node`) and Prometheus itself, every 5 s.
- `alerts.yml`: four alert rules (app down, high p95 latency, high host CPU, errors detected).
- `docker-compose.yml`: Prometheus and Grafana with host networking (Linux).
- `grafana/dashboard.json`: exported dashboard. `grafana/provisioning/`: fixed-uid Prometheus data source.
- `PROMQL_ATTRIBUTION.md`: every dashboard query with the AI prompt used (Code of Conduct).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # CPU-only PyTorch (extra index is in the file)

# 1. node_exporter, run natively (not in Docker) so it reports the real host
./node_exporter

# 2. the app. Open http://localhost:8501 once: the model loads and :8000 opens then.
streamlit run app.py --server.fileWatcherType none

# 3. Prometheus and Grafana
docker compose up -d
```

| Service | URL |
|---|---|
| Streamlit app | http://localhost:8501 |
| App metrics | http://localhost:8000/metrics |
| node_exporter | http://localhost:9100/metrics |
| Prometheus (targets, alerts) | http://localhost:9090 |
| Grafana (admin / admin) | http://localhost:3000 |

In Grafana: **Dashboards > New > Import > Upload JSON file** and choose
`grafana/dashboard.json`. The data source uid is `prometheus`, so no mapping is needed.

## Metrics

Counters (Prometheus adds `_total`):

| Metric | Labels | Purpose |
|---|---|---|
| `caption_images_processed_total` | `mode`, `status` | throughput and failure rate |
| `caption_requests_total` | `mode`, `client_ip`, `session_id` | per-client request tracking |
| `caption_client_images_total` | `client_ip`, `session_id` | images per client |
| `caption_errors_total` | `mode`, `error_type` | errors by exception type |
| `caption_upload_bytes_total` | `mode` | data volume received |
| `caption_generated_words_total` | `mode` | output volume |
| `caption_zip_skipped_files_total` | `reason` | unusable files inside ZIPs |

Gauges: `caption_active_requests{mode}`, `caption_bulk_pending_images`,
`caption_bulk_progress_ratio`, `caption_last_inference_seconds{mode}`,
`caption_model_loaded`, `caption_model_load_seconds`, `caption_model_memory_bytes`,
`caption_process_rss_bytes`, `caption_process_cpu_percent`,
`caption_app_start_time_seconds`, plus `caption_app_info` (Info).

Histograms: `caption_inference_duration_seconds{mode}`,
`caption_request_duration_seconds{mode}`, `caption_image_size_bytes`,
`caption_bulk_batch_size_images`.

Summaries (`_sum` and `_count`): `caption_preprocess_duration_seconds{mode}`,
`caption_text_length_chars{mode}`, `caption_image_pixels{mode}`.
Averages are computed in PromQL as `rate(_sum) / rate(_count)`.

## Dashboard

Reads top to bottom: **health** (up/down, model, uptime, in-flight, alerts), then
**throughput**, **latency**, **workload characteristics**, and finally
**system resources**, where host CPU and app CPU are drawn against a "bulk running"
indicator to show the correlation between application load and hardware use.

The 7 Commandments:
1. Colour-blind-safe Okabe-Ito palette (blue / orange / sky blue / purple / green).
2. Solid vs dashed vs dotted lines and the up/down symbols keep it readable in greyscale and print.
3. Every axis is named with its unit; x is time throughout.
4. Scale and unit are in each title (`linear` or `LOG10`).
5. Legends appear only when a panel has more than one series.
6. Each panel has a short title with a subtitle (`title · unit, scale`).
7. Each panel has a description (the **i** icon) that tells its story.

## Observations (my machine)

- Single-image inference is about 1 to 1.5 s on CPU.
- A 100-image ZIP takes roughly 2 minutes, about 55 to 60 images/min.
- During a bulk run host CPU rises from roughly 5 to 15% to about 55 to 60%, app CPU to about 48% of host capacity, and the app's resident memory roughly doubles. All return to baseline when the run ends.
- Mean inference time drifts up (about 1.05 s to 1.35 s) under sustained load, which CPU contention explains.

## Design notes

- **Streamlit reruns the script on each interaction.** Metrics live in `metrics.py` (imported once per process), and the model and metrics server start inside `st.cache_resource`, so nothing is registered twice.
- **Label series are pre-created at startup.** `rate()` ignores a series that first appears already at 1, so pre-creating them means the first observation is counted.
- **Cardinality.** `client_ip` and `session_id` create one series per client. Session IDs are truncated to 8 characters; in production these would not be labels.
- **The `/metrics` port opens when the first browser session loads the app**, because Streamlit runs the script on demand.

## AI usage (Code of Conduct)

PromQL for the dashboard and alert rules was written with AI assistance. The
prompts are recorded in `AI_DISCLOSURE.md` and as comments in `alerts.yml`.
I verified the metric logic by hand against raw `/metrics` output.
