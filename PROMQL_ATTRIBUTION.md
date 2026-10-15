# PromQL attribution (AI Code of Conduct)

| Panel | Ref | PromQL | Prompt used |
|---|---|---|---|
| App | A | `up{job="caption_app"}` | PROMPT |
| Host | A | `up{job="node"}` | PROMPT |
| Model | A | `caption_model_loaded` | PROMPT |
| Uptime | A | `time() - caption_app_start_time_seconds` | PROMPT |
| In-flight | A | `sum(caption_active_requests)` | PROMPT |
| Alerts | A | `count(ALERTS{alertstate="firing"}) or vector(0)` | PROMPT |
| Throughput | A | `sum by (mode) (rate(caption_images_processed_total{status="success"}[1m])) * 60` | PROMPT |
| Failed images | A | `sum by (mode) (rate(caption_images_processed_total{status="error"}[1m])) * 60` | PROMPT |
| Concurrency | A | `sum by (mode) (caption_active_requests)` | PROMPT |
| Concurrency | B | `caption_bulk_pending_images` | PROMPT |
| Images per client | A | `sum by (client_ip, session_id) (caption_client_images_total)` | PROMPT |
| Cumulative images | A | `sum by (mode) (caption_images_processed_total{status="success"})` | PROMPT |
| Errors by type | A | `sum by (mode, error_type) (caption_errors_total)` | PROMPT |
| Inference latency percentiles | A | `histogram_quantile(0.50, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | PROMPT |
| Inference latency percentiles | B | `histogram_quantile(0.95, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | PROMPT |
| Inference latency percentiles | C | `histogram_quantile(0.99, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | PROMPT |
| Mean inference latency by mode | A | `sum by (mode) (rate(caption_inference_duration_seconds_sum[1m])) / sum by (mode) (rate(caption_inference_duration_seconds_count[1m]))` | PROMPT |
| End-to-end request p95 | A | `histogram_quantile(0.95, sum by (le, mode) (rate(caption_request_duration_seconds_bucket[5m])))` | PROMPT |
| Where time goes | A | `sum(rate(caption_preprocess_duration_seconds_sum[1m])) / sum(rate(caption_preprocess_duration_seconds_count[1m])) * 1000` | PROMPT |
| Where time goes | B | `sum(rate(caption_inference_duration_seconds_sum[1m])) / sum(rate(caption_inference_duration_seconds_count[1m])) * 1000` | PROMPT |
| Mean caption length | A | `sum by (mode) (rate(caption_text_length_chars_sum[1m])) / sum by (mode) (rate(caption_text_length_chars_count[1m]))` | PROMPT |
| Mean image size | A | `sum by (mode) (rate(caption_image_pixels_sum[1m])) / sum by (mode) (rate(caption_image_pixels_count[1m])) / 1e6` | PROMPT |
| Upload volume | A | `sum by (mode) (rate(caption_upload_bytes_total[1m]))` | PROMPT |
| CPU vs bulk activity | A | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | PROMPT |
| CPU vs bulk activity | B | `caption_process_cpu_percent / scalar(count(count by (cpu) (node_cpu_seconds_total{mode="idle"})))` | PROMPT |
| CPU vs bulk activity | C | `caption_active_requests{mode="bulk"}` | PROMPT |
| Host memory used | A | `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` | PROMPT |
| App memory | A | `caption_process_rss_bytes` | PROMPT |
| App memory | B | `caption_model_memory_bytes` | PROMPT |
| Disk I/O | A | `sum(rate(node_disk_read_bytes_total{device!~"loop.*"}[1m]))` | PROMPT |
| Disk I/O | B | `sum(rate(node_disk_written_bytes_total{device!~"loop.*"}[1m]))` | PROMPT |
| Root disk used | A | `(1 - node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}) * 100` | PROMPT |
| Load average | A | `node_load1` | PROMPT |
| Load average | B | `node_load5` | PROMPT |
