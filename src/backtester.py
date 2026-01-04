"""
回測引擎核心模組
執行技術指標策略的回測並計算績效指標
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime
from .indicators import TechnicalIndicators, INDICATOR_STRATEGIES


class Backtester:
    """回測引擎類別"""
    
    def __init__(self, 
                 initial_capital: float = 1000000,
                 commission: float = 0.001425,
                 tax: float = 0.003):
        """
        初始化回測引擎
        
        Args:
            initial_capital: 初始資金，預設為 100 萬
            commission: 手續費率，預設為 0.1425%（台股一般手續費）
            tax: 交易稅率，預設為 0.3%（台股賣出時收取）
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.tax = tax
    
    def calculate_returns(self, 
                         data: pd.DataFrame,
                         buy_signal: Callable,
                         sell_signal: Callable) -> pd.DataFrame:
        """
        計算策略回報
        
        Args:
            data: 包含價格和技術指標的 DataFrame
            buy_signal: 買入訊號函數
            sell_signal: 賣出訊號函數
        
        Returns:
            包含交易記錄和回報的 DataFrame
        """
        result = data.copy()
        result['Position'] = 0  # 0: 無持倉, 1: 持有多頭
        result['Buy_Signal'] = False
        result['Sell_Signal'] = False
        result['Returns'] = 0.0
        result['Cumulative_Returns'] = 0.0
        
        # 計算買賣訊號
        result['Buy_Signal'] = buy_signal(result)
        result['Sell_Signal'] = sell_signal(result)
        
        # 計算持倉狀態
        position = 0
        for i in range(len(result)):
            if result.iloc[i]['Buy_Signal'] and position == 0:
                position = 1
            elif result.iloc[i]['Sell_Signal'] and position == 1:
                position = 0
            result.iloc[i, result.columns.get_loc('Position')] = position
        
        # 計算回報
        result['Returns'] = result['Close'].pct_change() * result['Position'].shift(1)
        result['Cumulative_Returns'] = (1 + result['Returns']).cumprod() - 1
        
        return result
    
    def calculate_performance_metrics(self, 
                                     data: pd.DataFrame,
                                     strategy_name: str) -> Dict:
        """
        計算策略績效指標
        
        Args:
            data: 包含回報數據的 DataFrame
            strategy_name: 策略名稱
        
        Returns:
            包含各種績效指標的字典
        """
        returns = data['Returns'].dropna()
        cumulative_returns = data['Cumulative_Returns'].iloc[-1]
        
        if len(returns) == 0:
            return {
                'strategy': strategy_name,
                'total_return': 0.0,
                'annualized_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
            }
        
        # 總報酬率
        total_return = cumulative_returns
        
        # 年化報酬率（假設一年約 252 個交易日）
        trading_days = len(data)
        years = trading_days / 252
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 波動率（年化）
        volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率（假設無風險利率為 0）
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 勝率
        trades = returns[returns != 0]
        if len(trades) > 0:
            win_rate = (trades > 0).sum() / len(trades)
        else:
            win_rate = 0
        
        # 交易次數
        position_changes = data['Position'].diff().abs().sum() / 2
        total_trades = int(position_changes)
        
        return {
            'strategy': strategy_name,
            'total_return': total_return * 100,  # 轉換為百分比
            'annualized_return': annualized_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'total_trades': total_trades,
        }
    
    def backtest_strategy(self,
                         data: pd.DataFrame,
                         strategy_name: str) -> tuple:
        """
        回測單一策略
        
        Args:
            data: 包含價格和技術指標的 DataFrame
            strategy_name: 策略名稱（必須在 INDICATOR_STRATEGIES 中定義）
        
        Returns:
            (回測結果 DataFrame, 績效指標字典)
        """
        if strategy_name not in INDICATOR_STRATEGIES:
            raise ValueError(f"策略 '{strategy_name}' 未定義")
        
        strategy = INDICATOR_STRATEGIES[strategy_name]
        buy_signal = strategy['buy_signal']
        sell_signal = strategy['sell_signal']
        
        # 計算回報
        result = self.calculate_returns(data, buy_signal, sell_signal)
        
        # 計算績效指標
        metrics = self.calculate_performance_metrics(result, strategy_name)
        
        return result, metrics
    
    def backtest_all_strategies(self, data: pd.DataFrame) -> Dict:
        """
        回測所有策略
        
        Args:
            data: 包含價格和技術指標的 DataFrame
        
        Returns:
            包含所有策略績效指標的字典
        """
        all_metrics = {}
        
        for strategy_name in INDICATOR_STRATEGIES.keys():
            try:
                _, metrics = self.backtest_strategy(data, strategy_name)
                all_metrics[strategy_name] = metrics
            except Exception as e:
                print(f"回測策略 {strategy_name} 時發生錯誤: {e}")
                all_metrics[strategy_name] = None
        
        return all_metrics
    
    def compare_strategies(self, metrics_dict: Dict) -> pd.DataFrame:
        """
        比較多個策略的績效
        
        Args:
            metrics_dict: 包含多個策略績效指標的字典
        
        Returns:
            比較結果的 DataFrame
        """
        # 過濾掉 None 值
        valid_metrics = {k: v for k, v in metrics_dict.items() if v is not None}
        
        if not valid_metrics:
            return pd.DataFrame()
        
        df = pd.DataFrame(valid_metrics).T
        return df

