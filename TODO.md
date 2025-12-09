# Edge-Native Smart Monitor 開發清單

## 步驟一：可執行骨架
- [x] 定義專案設定（路徑、前後錄影秒數、功能開關）以及 `CameraStream`、`RingBuffer`、`Detector`、`VideoRecorder`、`MonitorSystem` 等占位類別。
- [x] 在 `main.py` 中串接上述占位類別，建立最簡單的事件迴圈並可正常啟動與結束，先不做實際工作。

## 步驟二：攝影來源
- [x] 實作 `CameraStream` 支援 webcam/RTSP 讀取，若無硬體時可輸出產生的假影像。
- [x] 提供 start/stop 與 frame iterator API，好讓其他元件能即時取得畫面且 `main.py` 依然可運行。

## 步驟三：環形緩衝區
- [x] 建立以 deque 為基礎、含鎖的 `RingBuffer`，持續保存最近 N 秒畫面。
- [x] 在主迴圈中將 `CameraStream` 產生的畫面寫入緩衝區，確保即使錄影尚未完成也能取得歷史畫面。

## 步驟四：錄影模組
- [x] 完成 `VideoRecorder`，可將緩衝區畫面與即時畫面寫成磁碟片段（如 MP4/AVI），包含檔名、儲存路徑與保留策略。
- [x] 讓 `main.py` 能手動觸發錄影片段輸出，程式即可在需求時產生可播放檔案。

## 步驟五：偵測策略層
- [x] 定義 `Detector` 策略介面並實作永遠回傳 `False` 的 no-op 偵測器，為未來擴充做準備。
- [x] 讓 `MonitorSystem` 每幀輪詢偵測器並輸出事件結構，即使目前沒有實際判斷條件。

## 步驟六：監控協調層
- [ ] 充實 `MonitorSystem`：統合影像串流、緩衝、錄影觸發、設定（前後錄影秒數）、即時開關等邏輯。
- [ ] 提供可啟停監控的內部 API，使 `main.py` 能在未導入 FastAPI 前切換狀態。

## 步驟七：FastAPI 控制面
- [ ] 建立 FastAPI 端點，涵蓋 MJPEG 串流、監控/錄影開關、設定調整與狀態查詢。
- [ ] 讓 API 與監控迴圈（thread/task）並行執行，確保無需進階偵測器也能完整操作系統。
