# PromQL attribution (AI Code of Conduct)

| Panel | Ref | PromQL | Prompt used |
|---|---|---|---|
| App | A | `up{job="caption_app"}` | No AI used |
| Host | A | `up{job="node"}` | No AI used |
| Model | A | `caption_model_loaded` | No AI used |
| Uptime | A | `time() - caption_app_start_time_seconds` | What is the standard way to get process uptime in PromQL? |
| In-flight | A | `sum(caption_active_requests)` | No AI used |
| Alerts | A | `count(ALERTS{alertstate="firing"}) or vector(0)` | PromQL count firing alerts but return 0 instead of no data if empty |
| Throughput | A | `sum by (mode) (rate(caption_images_processed_total{status="success"}[1m])) * 60` | How to get a per-minute rate from a counter and sum it by mode? |
| Failed images | A | `sum by (mode) (rate(caption_images_processed_total{status="error"}[1m])) * 60` | Same as above but for status=error |
| Concurrency | A | `sum by (mode) (caption_active_requests)` | How to aggregate a gauge by a specific label? |
| Concurrency | B | `caption_bulk_pending_images` | No AI used |
| Images per client | A | `sum by (client_ip, session_id) (caption_client_images_total)` | PromQL group sum by multiple labels at once |
| Cumulative images | A | `sum by (mode) (caption_images_processed_total{status="success"})` | No AI used |
| Errors by type | A | `sum by (mode, error_type) (caption_errors_total)` | No AI used |
| Inference latency percentiles | A | `histogram_quantile(0.50, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | How do I calculate the median (p50) from a Prometheus histogram bucket? |
| Inference latency percentiles | B | `histogram_quantile(0.95, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | What is the syntax for p95 using histogram_quantile? |
| Inference latency percentiles | C | `histogram_quantile(0.99, sum by (le) (rate(caption_inference_duration_seconds_bucket[1m])))` | Same for p99 |
| Mean inference latency by mode | A | `sum by (mode) (rate(caption_inference_duration_seconds_sum[1m])) / sum by (mode) (rate(caption_inference_duration_seconds_count[1m]))` | How to calculate the average duration from a Prometheus summary sum and count? |
| End-to-end request p95 | A | `histogram_quantile(0.95, sum by (le, mode) (rate(caption_request_duration_seconds_bucket[5m])))` | How to calculate p95 latency grouped by mode? |
| Where time goes | A | `sum(rate(caption_preprocess_duration_seconds_sum[1m])) / sum(rate(caption_preprocess_duration_seconds_count[1m])) * 1000` | How to convert an average processing time from seconds to milliseconds? |
| Where time goes | B | `sum(rate(caption_inference_duration_seconds_sum[1m])) / sum(rate(caption_inference_duration_seconds_count[1m])) * 1000` | No AI used |
| Mean caption length | A | `sum by (mode) (rate(caption_text_length_chars_sum[1m])) / sum by (mode) (rate(caption_text_length_chars_count[1m]))` | Calculate average text length using sum and count metrics grouped by mode |
| Mean image size | A | `sum by (mode) (rate(caption_image_pixels_sum[1m])) / sum by (mode) (rate(caption_image_pixels_count[1m])) / 1e6` | How to convert an average pixel count into megapixels in PromQL? |
| Upload volume | A | `sum by (mode) (rate(caption_upload_bytes_total[1m]))` | No AI used |
| CPU vs bulk activity | A | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | What's the standard PromQL query to get overall CPU usage percentage from node_exporter? |
| CPU vs bulk activity | B | `caption_process_cpu_percent / scalar(count(count by (cpu) (node_cpu_seconds_total{mode="idle"})))` | How to normalize process CPU percent by total number of cores? |
| CPU vs bulk activity | C | `caption_active_requests{mode="bulk"}` | No AI used |
| Host memory used | A | `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` | Standard PromQL for host memory usage percentage |
| App memory | A | `caption_process_rss_bytes` | No AI used |
| App memory | B | `caption_model_memory_bytes` | No AI used |
| Disk I/O | A | `sum(rate(node_disk_read_bytes_total{device!~"loop.*"}[1m]))` | How to sum disk read rate but ignore loop devices? |
| Disk I/O | B | `sum(rate(node_disk_written_bytes_total{device!~"loop.*"}[1m]))` | Same but for disk write rate |
| Root disk used | A | `(1 - node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}) * 100` | PromQL to calculate root disk space used percentage ignoring tmpfs and overlays |
| Load average | A | `node_load1` | No AI used |
| Load average | B | `node_load5` | No AI used |