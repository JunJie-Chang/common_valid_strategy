"""
技術指標模組
定義並計算各種技術指標，用於回測驗證
"""
import pandas as pd
import pandas_ta as ta
from typing import Dict, Optional


class TechnicalIndicators:
    """技術指標計算類別"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化技術指標計算器
        
        Args:
            data: 包含 OHLCV 數據的 DataFrame，必須包含 'Open', 'High', 'Low', 'Close', 'Volume' 欄位
        """
        self.data = data.copy()
        if not all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            raise ValueError("數據必須包含 'Open', 'High', 'Low', 'Close', 'Volume' 欄位")
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """
        計算相對強弱指標 (RSI)
        
        Args:
            period: RSI 計算週期，預設為 14
        
        Returns:
            RSI 值序列
        """
        rsi = ta.rsi(self.data['Close'], length=period)
        return rsi
    
    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        計算 MACD 指標
        
        Args:
            fast: 快速 EMA 週期，預設為 12
            slow: 慢速 EMA 週期，預設為 26
            signal: 訊號線週期，預設為 9
        
        Returns:
            包含 MACD, Signal, Histogram 的 DataFrame
        """
        macd = ta.macd(self.data['Close'], fast=fast, slow=slow, signal=signal)
        return macd
    
    def calculate_moving_averages(self, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        計算移動平均線
        
        Args:
            periods: 移動平均線週期列表，預設為 [5, 10, 20, 60]
        
        Returns:
            包含各週期移動平均線的 DataFrame
        """
        ma_data = pd.DataFrame(index=self.data.index)
        for period in periods:
            ma_data[f'MA{period}'] = ta.sma(self.data['Close'], length=period)
        return ma_data
    
    def calculate_bollinger_bands(self, period: int = 20, std: float = 2) -> pd.DataFrame:
        """
        計算布林通道
        
        Args:
            period: 移動平均週期，預設為 20
            std: 標準差倍數，預設為 2
        
        Returns:
            包含上軌、中軌、下軌的 DataFrame，欄位名稱標準化為 BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        """
        bb = ta.bbands(self.data['Close'], length=period, std=std)
        if bb is not None and not bb.empty:
            # 標準化欄位名稱，確保策略能正確訪問
            bb_columns = bb.columns.tolist()
            bb_renamed = pd.DataFrame(index=bb.index)
            
            # pandas-ta 的 bbands 通常返回三個欄位：下軌、中軌、上軌
            # 欄位名稱格式可能是 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0'
            # 或其他變體，我們需要動態查找並標準化
            
            # 方法1: 查找包含 BBL/BBM/BBU 的欄位
            bbl_col = None
            bbm_col = None
            bbu_col = None
            
            for col in bb_columns:
                col_str = str(col).upper()
                if 'BBL' in col_str or ('LOWER' in col_str and 'BB' in col_str):
                    bbl_col = col
                elif 'BBM' in col_str or ('MID' in col_str and 'BB' in col_str):
                    bbm_col = col
                elif 'BBU' in col_str or ('UPPER' in col_str and 'BB' in col_str):
                    bbu_col = col
            
            # 方法2: 如果沒找到，按順序取前三個欄位（通常順序是下軌、中軌、上軌）
            if bbl_col is None and len(bb_columns) >= 1:
                bbl_col = bb_columns[0]
            if bbm_col is None and len(bb_columns) >= 2:
                bbm_col = bb_columns[1]
            if bbu_col is None and len(bb_columns) >= 3:
                bbu_col = bb_columns[2]
            
            # 標準化欄位名稱
            if bbl_col is not None:
                bb_renamed['BBL_20_2.0'] = bb[bbl_col]
            if bbm_col is not None:
                bb_renamed['BBM_20_2.0'] = bb[bbm_col]
            if bbu_col is not None:
                bb_renamed['BBU_20_2.0'] = bb[bbu_col]
            
            return bb_renamed
        return pd.DataFrame()
    
    def calculate_stochastic(self, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        計算隨機指標 (KD)
        
        Args:
            k_period: K 值週期，預設為 14
            d_period: D 值週期，預設為 3
        
        Returns:
            包含 K 值和 D 值的 DataFrame
        """
        stoch = ta.stoch(self.data['High'], self.data['Low'], self.data['Close'], 
                        k=k_period, d=d_period)
        return stoch
    
    def calculate_all_indicators(self) -> pd.DataFrame:
        """
        計算所有技術指標並合併到原始數據中
        
        Returns:
            包含所有技術指標的 DataFrame
        """
        result = self.data.copy()
        
        # RSI
        result['RSI'] = self.calculate_rsi()
        
        # MACD
        macd_data = self.calculate_macd()
        if macd_data is not None and not macd_data.empty:
            result = pd.concat([result, macd_data], axis=1)
        
        # 移動平均線
        ma_data = self.calculate_moving_averages()
        result = pd.concat([result, ma_data], axis=1)
        
        # 布林通道
        bb_data = self.calculate_bollinger_bands()
        if bb_data is not None and not bb_data.empty:
            # 確保必要的欄位存在
            required_bb_cols = ['BBL_20_2.0', 'BBU_20_2.0']
            if all(col in bb_data.columns for col in required_bb_cols):
                result = pd.concat([result, bb_data], axis=1)
            else:
                print(f"警告：布林通道計算結果缺少必要欄位，預期: {required_bb_cols}，實際: {list(bb_data.columns)}")
        
        # 隨機指標
        stoch_data = self.calculate_stochastic()
        if stoch_data is not None and not stoch_data.empty:
            result = pd.concat([result, stoch_data], axis=1)
        
        return result


# 定義要驗證的技術指標策略
INDICATOR_STRATEGIES = {
    'RSI': {
        'description': 'RSI 超買超賣策略',
        'buy_signal': lambda data: (data['RSI'] < 30) & (data['RSI'].shift(1) >= 30),
        'sell_signal': lambda data: (data['RSI'] > 70) & (data['RSI'].shift(1) <= 70),
    },
    'MACD': {
        'description': 'MACD 金叉死叉策略',
        'buy_signal': lambda data: (data['MACD_12_26_9'] > data['MACDs_12_26_9']) & \
                                   (data['MACD_12_26_9'].shift(1) <= data['MACDs_12_26_9'].shift(1)),
        'sell_signal': lambda data: (data['MACD_12_26_9'] < data['MACDs_12_26_9']) & \
                                    (data['MACD_12_26_9'].shift(1) >= data['MACDs_12_26_9'].shift(1)),
    },
    'MA_CROSS': {
        'description': '移動平均線交叉策略（5日線上穿20日線）',
        'buy_signal': lambda data: (data['MA5'] > data['MA20']) & \
                                   (data['MA5'].shift(1) <= data['MA20'].shift(1)),
        'sell_signal': lambda data: (data['MA5'] < data['MA20']) & \
                                    (data['MA5'].shift(1) >= data['MA20'].shift(1)),
    },
    'BOLLINGER': {
        'description': '布林通道策略（觸及下軌買入，觸及上軌賣出）',
        'buy_signal': lambda data: (data['BBL_20_2.0'].notna()) & (data['Close'] <= data['BBL_20_2.0']),
        'sell_signal': lambda data: (data['BBU_20_2.0'].notna()) & (data['Close'] >= data['BBU_20_2.0']),
    },
    'STOCHASTIC': {
        'description': 'KD 指標策略',
        'buy_signal': lambda data: (data['STOCHk_14_3_3'] < 20) & \
                                   (data['STOCHk_14_3_3'] > data['STOCHd_14_3_3']),
        'sell_signal': lambda data: (data['STOCHk_14_3_3'] > 80) & \
                                    (data['STOCHk_14_3_3'] < data['STOCHd_14_3_3']),
    },
}

