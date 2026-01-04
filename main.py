"""
主程式：執行技術指標回測
"""
import pandas as pd
from src.data_fetcher import DataFetcher
from src.indicators import TechnicalIndicators
from src.backtester import Backtester
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')


def main():
    """主函數：執行完整的回測流程"""
    print("=" * 60)
    print("技術指標回測系統")
    print("=" * 60)
    print()
    
    # 1. 初始化數據獲取器
    print("步驟 1: 初始化數據獲取器...")
    fetcher = DataFetcher()
    print(f"可用股票數量: {len(fetcher.list_available_stocks())}")
    print()
    
    # 2. 獲取多個重要台股數據
    print("步驟 2: 獲取台股數據...")
    print("正在獲取以下重要台股數據:")
    for name, code in list(fetcher.list_available_stocks().items())[:10]:
        print(f"  - {name} ({code})")
    print()
    
    # 選擇要測試的股票（可以修改這個列表）
    test_stocks = [
        '2330.TW',  # 台積電
        '2454.TW',  # 聯發科
        '2317.TW',  # 鴻海
        '2412.TW',  # 中華電
        '2881.TW',  # 富邦金
        '2882.TW',  # 國泰金
    ]
    
    stock_data = fetcher.get_multiple_stocks(symbols=test_stocks, period='10y')
    print(f"\n成功獲取 {len(stock_data)} 檔股票的數據")
    print()
    
    # 3. 對每檔股票進行回測
    print("步驟 3: 執行技術指標回測...")
    print("=" * 60)
    
    all_results = {}
    
    for symbol, data in stock_data.items():
        stock_name = fetcher.get_stock_name(symbol)
        print(f"\n正在回測: {stock_name} ({symbol})")
        print("-" * 60)
        
        try:
            # 計算技術指標
            indicator_calc = TechnicalIndicators(data)
            data_with_indicators = indicator_calc.calculate_all_indicators()
            
            # 初始化回測引擎
            backtester = Backtester(initial_capital=1000000)
            
            # 回測所有策略
            metrics = backtester.backtest_all_strategies(data_with_indicators)
            
            # 顯示結果
            comparison_df = backtester.compare_strategies(metrics)
            if not comparison_df.empty:
                print(f"\n{stock_name} 策略績效比較:")
                print(comparison_df.to_string())
            
            # 儲存結果（包含數據日期範圍）
            data_start = data_with_indicators.index.min().strftime("%Y%m%d")
            data_end = data_with_indicators.index.max().strftime("%Y%m%d")
            all_results[symbol] = {
                'name': stock_name,
                'metrics': metrics,
                'comparison_df': comparison_df,
                'data': data_with_indicators,
                'date_range': f"{data_start}_to_{data_end}"
            }
            
        except Exception as e:
            print(f"錯誤：回測 {stock_name} 時發生問題 - {e}")
            continue
    
    # 4. 生成總結報告
    print("\n" + "=" * 60)
    print("回測總結報告")
    print("=" * 60)
    
    # 計算各策略的平均績效
    strategy_summary = {}
    for symbol, result in all_results.items():
        metrics = result['metrics']
        for strategy_name, metric in metrics.items():
            if metric is not None:
                if strategy_name not in strategy_summary:
                    strategy_summary[strategy_name] = {
                        'total_returns': [],
                        'sharpe_ratios': [],
                        'max_drawdowns': [],
                        'win_rates': [],
                    }
                strategy_summary[strategy_name]['total_returns'].append(metric['total_return'])
                strategy_summary[strategy_name]['sharpe_ratios'].append(metric['sharpe_ratio'])
                strategy_summary[strategy_name]['max_drawdowns'].append(metric['max_drawdown'])
                strategy_summary[strategy_name]['win_rates'].append(metric['win_rate'])
    
    # 顯示平均績效
    print("\n各策略平均績效（跨所有測試股票）:")
    print("-" * 60)
    summary_data = []
    for strategy_name, stats in strategy_summary.items():
        avg_return = sum(stats['total_returns']) / len(stats['total_returns'])
        avg_sharpe = sum(stats['sharpe_ratios']) / len(stats['sharpe_ratios'])
        avg_drawdown = sum(stats['max_drawdowns']) / len(stats['max_drawdowns'])
        avg_winrate = sum(stats['win_rates']) / len(stats['win_rates'])
        
        summary_data.append({
            '策略': strategy_name,
            '平均總報酬率 (%)': f"{avg_return:.2f}",
            '平均夏普比率': f"{avg_sharpe:.2f}",
            '平均最大回撤 (%)': f"{avg_drawdown:.2f}",
            '平均勝率 (%)': f"{avg_winrate:.2f}",
        })
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # 4.5. 顯示各策略表現最佳的前三名股票
    print("\n" + "=" * 60)
    print("各策略表現最佳前三名股票（依年化報酬率排序）")
    print("=" * 60)
    
    # 收集所有策略的股票績效數據
    strategy_stocks = {}
    for symbol, result in all_results.items():
        stock_name = result['name']
        metrics = result['metrics']
        for strategy_name, metric in metrics.items():
            if metric is not None:
                if strategy_name not in strategy_stocks:
                    strategy_stocks[strategy_name] = []
                strategy_stocks[strategy_name].append({
                    'symbol': symbol,
                    'name': stock_name,
                    'total_return': metric['total_return'],
                    'annualized_return': metric['annualized_return'],
                    'sharpe_ratio': metric['sharpe_ratio'],
                    'max_drawdown': metric['max_drawdown'],
                    'win_rate': metric['win_rate'],
                    'volatility': metric['volatility'],
                    'total_trades': metric['total_trades'],
                })
    
    # 對每個策略，找出前三名
    for strategy_name in sorted(strategy_stocks.keys()):
        stocks = strategy_stocks[strategy_name]
        # 依年化報酬率排序（降序）
        stocks_sorted = sorted(stocks, key=lambda x: x['annualized_return'], reverse=True)
        top3 = stocks_sorted[:3]
        
        print(f"\n【{strategy_name} 策略】")
        print("-" * 60)
        
        if len(top3) == 0:
            print("  無有效數據")
            continue
        
        for rank, stock in enumerate(top3, 1):
            print(f"\n第 {rank} 名: {stock['name']} ({stock['symbol']})")
            print(f"  年化報酬率: {stock['annualized_return']:.2f}%")
            print(f"  總報酬率:   {stock['total_return']:.2f}%")
            print(f"  夏普比率:   {stock['sharpe_ratio']:.2f}")
            print(f"  最大回撤:   {stock['max_drawdown']:.2f}%")
            print(f"  波動率:     {stock['volatility']:.2f}%")
            print(f"  勝率:       {stock['win_rate']:.2f}%")
            print(f"  交易次數:   {stock['total_trades']}")
    
    # 5. 輸出結果到 CSV
    print("\n" + "=" * 60)
    print("正在生成 CSV 報告...")
    print("=" * 60)
    
    # 創建詳細結果 DataFrame（每檔股票 x 每個策略）
    detailed_results = []
    for symbol, result in all_results.items():
        stock_name = result['name']
        metrics = result['metrics']
        for strategy_name, metric in metrics.items():
            if metric is not None:
                detailed_results.append({
                    '股票代碼': symbol,
                    '股票名稱': stock_name,
                    '策略': strategy_name,
                    '總報酬率 (%)': f"{metric['total_return']:.2f}",
                    '年化報酬率 (%)': f"{metric['annualized_return']:.2f}",
                    '波動率 (%)': f"{metric['volatility']:.2f}",
                    '夏普比率': f"{metric['sharpe_ratio']:.2f}",
                    '最大回撤 (%)': f"{metric['max_drawdown']:.2f}",
                    '勝率 (%)': f"{metric['win_rate']:.2f}",
                    '交易次數': metric['total_trades'],
                })
    
    detailed_df = pd.DataFrame(detailed_results)
    
    # 確保輸出目錄存在
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 獲取所有股票的日期範圍（用於詳細結果和總結結果）
    all_date_ranges = [result['date_range'] for result in all_results.values()]
    if all_date_ranges:
        # 使用所有股票中最早的開始日期和最晚的結束日期
        start_dates = [dr.split('_to_')[0] for dr in all_date_ranges]
        end_dates = [dr.split('_to_')[1] for dr in all_date_ranges]
        overall_start = min(start_dates)
        overall_end = max(end_dates)
        overall_date_range = f"{overall_start}_to_{overall_end}"
    else:
        overall_date_range = datetime.now().strftime("%Y%m%d")
    
    # 保存詳細結果（使用整體日期範圍）
    detailed_file = os.path.join(output_dir, f"backtest_detailed_{overall_date_range}.csv")
    detailed_df.to_csv(detailed_file, index=False, encoding='utf-8-sig')
    print(f"✓ 詳細結果已保存至: {detailed_file}")
    
    # 保存總結結果（使用整體日期範圍）
    summary_file = os.path.join(output_dir, f"backtest_summary_{overall_date_range}.csv")
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"✓ 總結結果已保存至: {summary_file}")
    
    # 創建每檔股票的個別結果檔案（使用該股票的日期範圍）
    for symbol, result in all_results.items():
        stock_name = result['name']
        stock_df = result.get('comparison_df', pd.DataFrame())
        date_range = result.get('date_range', datetime.now().strftime("%Y%m%d"))
        if not stock_df.empty:
            # 添加股票資訊
            stock_df = stock_df.copy()
            stock_df.insert(0, '股票代碼', symbol)
            stock_df.insert(1, '股票名稱', stock_name)
            # 使用格式：股票代號_開始日期_to_結束日期.csv
            stock_file = os.path.join(output_dir, f"{symbol}_{date_range}.csv")
            stock_df.to_csv(stock_file, index=False, encoding='utf-8-sig')
            print(f"✓ {stock_name} 結果已保存至: {stock_file}")
    
    print("\n回測完成！")
    print("=" * 60)
    print(f"所有結果已保存至 '{output_dir}' 目錄")
    print("=" * 60)


if __name__ == '__main__':
    main()

