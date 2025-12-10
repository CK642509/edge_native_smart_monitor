# Edge-Native Smart Monitor

## 啟動監控主程式

### 基本模式（命令行）

```bash
python -m app.main
```

此指令會讀取預設設定，串接 `CameraStream`、`MonitorSystem` 與其他元件，並在指定秒數內執行監控迴圈。

### FastAPI 模式（REST API + 網頁控制）

```bash
python -m app.main_api
```

此模式會啟動 FastAPI 伺服器，提供完整的 REST API 端點與 MJPEG 即時串流。監控迴圈與 API 伺服器會在獨立執行緒中並行運行。

**API 端點：**

- **API 文件（Swagger UI）**: http://127.0.0.1:8000/docs
- **即時影像串流（MJPEG）**: http://127.0.0.1:8000/stream/mjpeg

**主要 API 操作：**

```bash
# 查詢系統狀態
curl http://127.0.0.1:8000/status

# 啟用監控（偵測與自動錄影）
curl -X POST http://127.0.0.1:8000/monitoring/enable

# 停用監控（攝影機持續運行但不偵測）
curl -X POST http://127.0.0.1:8000/monitoring/disable

# 手動觸發錄影
curl -X POST http://127.0.0.1:8000/recording/trigger

# 查詢目前設定
curl http://127.0.0.1:8000/config

# 更新設定（例如：調整前後錄影秒數）
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"pre_event_seconds": 15.0, "post_event_seconds": 15.0}'
```

## 預覽攝影畫面

```bash
python -m app.camera_stream --source 0 --duration 15
```

此預覽工具會開啟名為「CameraStream Preview」的視窗，顯示即時或合成畫面。可依需求將 `--source` 改為 RTSP URL、影片檔案或其他 webcam index；`--duration 0`（或負值）則會讓視窗持續顯示，直到按下 `q`/`Esc`。
