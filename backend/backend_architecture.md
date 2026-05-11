# 後端系統架構與檔案功能說明 (Backend Architecture)

## 根目錄設定檔
*   **`config.py`**: 後端環境變數與全域設定檔。儲存如 MySQL 資料庫連線字串 (URI)、LINE Channel Secret、LINE Access Token 等機密資訊與不同環境 (開發、正式) 的配置。
*   **`requirements.txt`**: Python 套件相依清單。列出專案執行需要安裝的套件 (如 Flask, SQLAlchemy, APScheduler, requests 等)，方便部署與環境重建。
*   **`run.py`**: 整個 Flask 應用的唯一啟動點。負責呼叫 `app/__init__.py` 中的工廠函式建立應用實例，並啟動開發伺服器。

## `app/` 核心應用目錄
*   **`__init__.py`**: Flask 工廠函式 (`create_app`) 所在位置。負責初始化 Flask 實例、載入設定、初始化擴充套件 (如資料庫 ORM、CORS)，並註冊各個 API 路由。

---

### 1. `app/models/` (資料庫模型層)
負責使用 SQLAlchemy ORM 定義資料庫表格的 Schema。這裡的檔案只做資料結構對應，不寫商業邏輯。
*   **`__init__.py`**: 模組宣告檔。
*   **`user.py`**: 定義使用者相關表格。包含 `users` (使用者主檔)、`favorites` (常用定點收藏)、`notifications` (預警推播設定) 等。
*   **`station.py`**: 定義空間與基礎設施表格。包含 `cities` (縣市)、`districts` (行政區)、`routes` (清運路線)、`stations` (實體停靠站點)。
*   **`schedule.py`**: 定義動態與時刻列表格。包含 `station_schedules` (站點收運日程) 及 `truck_locations` (高頻即時車輛動態)。

---

### 2. `app/api/` (路由層 / Controllers)
負責接收 HTTP 請求、驗證輸入參數，將任務交給 Services 處理後回傳 JSON。**服務生角色，不負責煮菜**。
*   **`__init__.py`**: 模組宣告檔。
*   **`routes.py`**: 處理垃圾車核心業務 API。例如：取得附近站點、搜尋特定路線、查詢垃圾車即時動態。
*   **`users.py`**: 處理使用者帳號 API。例如：使用者登入/註冊、CRUD 常用定點與推播偏好設定。
*   **`webhooks.py`**: 專門接收外部服務的事件推播。最主要用於接收 LINE Platform 發送的 Webhook 事件 (如使用者傳送文字、加入好友)。

---

### 3. `app/services/` (商業邏輯層)
負責處理核心運算與跨模組邏輯，讓 Controller 保持輕量。**大腦與廚師角色**。
*   **`__init__.py`**: 模組宣告檔。
*   **`geo_service.py`**: 封裝所有與空間運算有關的邏輯。包含計算 Bounding Box 邊界框、透過 Haversine 演算法計算經緯度距離與過濾鄰近站點。
*   **`line_service.py`**: 封裝所有呼叫 LINE API 的邏輯。包含組裝推播訊息格式、處理使用者綁定 (Account Link) 以及向外發送 API 請求。

---

### 4. `app/tasks/` (背景排程層)
透過排程器 (如 APScheduler) 獨立於 HTTP 請求之外執行的定時自動化任務。
*   **`__init__.py`**: 模組宣告檔。
*   **`data_sync.py`**: 負責資料同步作業。例如每 2 分鐘拉取新北市 Open Data 即時動態，清洗後更新寫入資料庫的 `truck_locations` 表格。
*   **`notifier.py`**: 時空判定與預警推播引擎。定時掃描資料庫中的即時車輛位置與使用者設定，判斷是否達到「快到站」條件，若是則觸發推播。

---

### 5. `app/utils/` (共用工具層)
全域共用的基礎功能函式庫 (打雜用)。
*   **`__init__.py`**: 模組宣告檔。
*   **`helpers.py`**: 提供雜項工具。例如：時間格式轉換、全域的例外錯誤處理器 (Error Handler)、或是用來驗證資料格式的輔助函式。
