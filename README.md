# Edge-Native Smart Monitor

## 啟動監控主程式

```bash
python -m app.main
```

此指令會讀取預設設定，串接 `CameraStream`、`MonitorSystem` 與其他元件，並在指定秒數內執行監控迴圈。

## 預覽攝影畫面

```bash
python -m app.camera_stream --source 0 --duration 15
```

此預覽工具會開啟名為「CameraStream Preview」的視窗，顯示即時或合成畫面。可依需求將 `--source` 改為 RTSP URL、影片檔案或其他 webcam index；`--duration 0`（或負值）則會讓視窗持續顯示，直到按下 `q`/`Esc`。
