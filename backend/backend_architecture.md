# 後端系統架構說明 (Backend Architecture - Updated)

本系統採用 **Flask** 作為核心框架，並透過 **Blueprint** 實現模組化設計。為了追求更高的執行效率與簡潔性，後端移除了 SQLAlchemy ORM，改採直接透過 **PyMySQL** 執行 SQL 指令的方式進行資料操作。

## 核心元件與目錄結構

### 1. 資料庫管理層 (`app/db.py`)
這是目前系統與資料庫溝通的核心。
*   **Connection Pooling**: 使用 `dbutils.pooled_db` 實作 `PooledDB` 連線池，有效管理資料庫連線，提升高併發環境下的效能。
*   **Direct SQL**: 提供 `get_db_connection()` 工具函式，讓各個層級能快速取得連線並執行原始 SQL 指令。

### 2. API 路由層 (`app/api/`)
使用 Flask Blueprint 將功能模組化，並定義不同的 URL 前綴：
*   **`routes.py` (Stations API)**: 處理垃圾車與站點相關查詢。例如，直接在 SQL 中利用 **Haversine 演算法** 實作地理空間檢索（找尋附近站點）。
*   **`users.py` (Users API)**: 處理使用者註冊與帳號管理。整合了 **LINE LIFF** 的流程，允許使用者透過 LINE 介面註冊並將 LINE ID 與系統帳號綁定。
*   **`webhooks.py` (LINE Webhook API)**: 專門接收來自 LINE Platform 的 Webhook 事件，作為與使用者即時互動的入口。

### 3. 業務邏輯服務層 (`app/services/`)
封裝複雜的運算與外部 API 整合邏輯，確保 Controller (API) 層保持輕量：
*   **`geo_service.py`**: 提供地理空間計算、範圍過濾等邏輯。
*   **`line_service.py`**: 封裝與 LINE Messaging API 的溝通細節（如發送訊息、處理 Account Link 等）。

### 4. 背景任務層 (`app/tasks/`)
利用 `APScheduler` 執行非同步的週期性作業，避免阻塞 API 請求：
*   **`data_sync.py`**: 定期從政府 Open Data 抓取最新資料並同步至資料庫。
*   **`notifier.py`**: 監控垃圾車位置變化，當滿足特定條件時，主動透過 LINE 發送通知給使用者。
*   **`newimport.py`**: 處理特定的資料匯入邏輯。

### 5. 工具與配置層
*   **`app/utils/`**: 提供系統通用的輔助函式（如 Error Handling, Formatters）。
*   **`config.py`**: 集中管理環境變數（資料庫憑證、LINE API Token、LIFF ID 等）。

## 技術棧 (Tech Stack)
*   **Language**: Python 3.x
*   **Framework**: Flask
*   **Database**: MySQL (透過 `PyMySQL` 連線)
*   **Connection Pool**: `DBUtils`
*   **Task Scheduler**: `APScheduler`
*   **Integration**: LINE Messaging API, LINE LIFF
