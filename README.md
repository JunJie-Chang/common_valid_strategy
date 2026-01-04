# 技術指標回測系統

這是一個用於驗證傳統技術指標有效性的回測系統，專門針對台灣股票市場設計。

## 功能特色

### 1. 技術指標定義

系統包含以下技術指標的實作：

- **RSI (相對強弱指標)**: 超買超賣策略
- **MACD**: 金叉死叉策略
- **移動平均線交叉**: 5日線與20日線交叉策略
- **布林通道**: 觸及上下軌策略
- **KD 指標 (隨機指標)**: 超買超賣策略

### 2. 台股數據獲取

系統預設包含以下重要台股：

- 台積電 (2330.TW)
- 聯發科 (2454.TW)
- 鴻海 (2317.TW)
- 中華電 (2412.TW)
- 富邦金 (2881.TW)
- 國泰金 (2882.TW)
- 以及其他重要股票...

### 3. 回測引擎

- 計算策略總報酬率
- 計算年化報酬率
- 計算夏普比率
- 計算最大回撤
- 計算勝率
- 統計交易次數

## 安裝

1. 確保 Python 版本 >= 3.12

2. 安裝依賴套件：

```bash
pip install -e .
```

或使用 poetry（如果已安裝）：

```bash
poetry install
```

## 使用方法

### 基本使用

直接執行主程式：

```bash
python main.py
```

### 自訂測試股票

在 `main.py` 中修改 `test_stocks` 列表：

```python
test_stocks = [
    '2330.TW',  # 台積電
    '2454.TW',  # 聯發科
    # 添加更多股票代碼...
]
```

### 自訂數據期間

在 `main.py` 中修改數據獲取參數：

```python
stock_data = fetcher.get_multiple_stocks(
    symbols=test_stocks, 
    period='2y'  # 可改為 '1y', '5y' 等
)
```

### 程式化使用

```python
from src.data_fetcher import DataFetcher
from src.indicators import TechnicalIndicators
from src.backtester import Backtester

# 獲取數據
fetcher = DataFetcher()
data = fetcher.get_stock_data('2330.TW', period='2y')

# 計算技術指標
indicators = TechnicalIndicators(data)
data_with_indicators = indicators.calculate_all_indicators()

# 執行回測
backtester = Backtester()
metrics = backtester.backtest_all_strategies(data_with_indicators)

# 查看結果
comparison = backtester.compare_strategies(metrics)
print(comparison)
```

## 專案結構

```
common_valid_strategy/
├── src/
│   ├── __init__.py
│   ├── indicators.py          # 技術指標計算模組
│   ├── data_fetcher.py        # 台股數據獲取模組
│   └── backtester.py          # 回測引擎模組
├── main.py                     # 主程式
├── pyproject.toml             # 專案配置
└── README.md                  # 說明文件
```

## 依賴套件

- `pandas`: 數據處理
- `numpy`: 數值計算
- `yfinance`: 股票數據獲取
- `pandas-ta`: 技術指標計算
- `matplotlib`: 圖表繪製（未來擴展用）
- `seaborn`: 數據視覺化（未來擴展用）

## 注意事項

1. **數據來源**: 使用 yfinance 獲取台股數據，數據可能會有延遲
2. **交易成本**: 系統已考慮手續費（0.1425%）和交易稅（0.3%）
3. **回測限制**: 回測結果不代表未來表現，僅供參考
4. **數據品質**: 請確保網路連線正常以獲取最新數據

## 未來擴展

- [ ] 添加更多技術指標
- [ ] 視覺化回測結果
- [ ] 參數優化功能
- [ ] 組合策略回測
- [ ] 風險指標計算（VaR, CVaR 等）
- [ ] 即時數據更新

## 授權

本專案僅供學習和研究使用。

# common-indicators-validation
