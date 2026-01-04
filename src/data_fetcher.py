"""
台股數據獲取模組
從 yfinance 獲取台灣股票市場數據
"""
import yfinance as yf
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta


# 台灣重要股票代碼列表（加 .TW 後綴供 yfinance 使用）
TAIWAN_STOCKS = {
    '台積電': '2330.TW',
    '聯發科': '2454.TW',
    '鴻海': '2317.TW',
    '中華電': '2412.TW',
    '台塑': '1301.TW',
    '南亞': '1303.TW',
    '中鋼': '2002.TW',
    '富邦金': '2881.TW',
    '國泰金': '2882.TW',
    '兆豐金': '2886.TW',
    '第一金': '2892.TW',
    '玉山金': '2884.TW',
    '中信金': '2891.TW',
    '統一': '1216.TW',
    '台化': '1326.TW',
    '大立光': '3008.TW',
    '聯詠': '3034.TW',
    '瑞昱': '2379.TW',
    '廣達': '2382.TW',
    '仁寶': '2324.TW',
}


class DataFetcher:
    """台股數據獲取類別"""
    
    def __init__(self):
        """初始化數據獲取器"""
        self.stocks = TAIWAN_STOCKS
    
    def get_stock_data(self, 
                      symbol: str, 
                      period: str = '2y',
                      start: Optional[str] = None,
                      end: Optional[str] = None) -> pd.DataFrame:
        """
        獲取單一股票數據
        
        Args:
            symbol: 股票代碼（例如 '2330.TW'）
            period: 數據期間（'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'）
            start: 開始日期（格式：'YYYY-MM-DD'），如果提供則忽略 period
            end: 結束日期（格式：'YYYY-MM-DD'），如果提供則忽略 period
        
        Returns:
            包含 OHLCV 數據的 DataFrame
        """
        ticker = yf.Ticker(symbol)
        
        if start and end:
            data = ticker.history(start=start, end=end)
        else:
            data = ticker.history(period=period)
        
        # 標準化欄位名稱
        data.columns = [col.replace(' ', '') for col in data.columns]
        data = data.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        # 確保欄位名稱正確
        if 'Open' not in data.columns:
            data = data.rename(columns={data.columns[0]: 'Open'})
        
        return data[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    def get_multiple_stocks(self, 
                           symbols: Optional[List[str]] = None,
                           period: str = '2y',
                           start: Optional[str] = None,
                           end: Optional[str] = None) -> dict:
        """
        獲取多個股票數據
        
        Args:
            symbols: 股票代碼列表，如果為 None 則獲取所有預定義股票
            period: 數據期間
            start: 開始日期
            end: 結束日期
        
        Returns:
            字典，key 為股票代碼，value 為 DataFrame
        """
        if symbols is None:
            symbols = list(self.stocks.values())
        
        stock_data = {}
        for symbol in symbols:
            try:
                print(f"正在獲取 {symbol} 的數據...")
                data = self.get_stock_data(symbol, period=period, start=start, end=end)
                if not data.empty:
                    stock_data[symbol] = data
                    print(f"成功獲取 {symbol}，共 {len(data)} 筆數據")
                else:
                    print(f"警告：{symbol} 沒有數據")
            except Exception as e:
                print(f"錯誤：無法獲取 {symbol} 的數據 - {e}")
        
        return stock_data
    
    def get_stock_name(self, symbol: str) -> str:
        """
        根據股票代碼獲取股票名稱
        
        Args:
            symbol: 股票代碼（例如 '2330.TW'）
        
        Returns:
            股票名稱
        """
        for name, code in self.stocks.items():
            if code == symbol:
                return name
        return symbol
    
    def list_available_stocks(self) -> dict:
        """
        列出所有可用的股票
        
        Returns:
            股票名稱與代碼的字典
        """
        return self.stocks.copy()

