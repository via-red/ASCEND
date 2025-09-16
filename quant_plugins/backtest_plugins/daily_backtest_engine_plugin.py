
"""
日K线回测引擎插件
基于事件驱动的日K线回测框架

功能:
- 基于事件驱动的回测框架
- 完整的交易模拟
- 风险管理控制
- 详细的性能评估
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IBacktestEngine, IRiskManager

# 插件配置模型
class DailyBacktestEnginePluginConfig(BaseModel):
    """日K线回测引擎配置"""
    
    initial_capital: float = Field(1000000.0, description="初始资金")
    commission: float = Field(0.0003, description="交易佣金费率")
    slippage: float = Field(0.0001, description="滑点费率")
    max_position_per_stock: float = Field(0.2, description="单股票最大仓位比例")
    stop_loss: float = Field(0.1, description="止损比例")
    take_profit: float = Field(0.2, description="止盈比例")
    max_drawdown_limit: float = Field(0.3, description="最大回撤限制")
    enable_short_selling: bool = Field(False, description="是否允许卖空")
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v <= 0:
            raise ValueError('Initial capital must be positive')
        return v
    
    @validator('commission', 'slippage')
    def validate_fees(cls, v):
        if v < 0:
            raise ValueError('Fees cannot be negative')
        return v
    
    @validator('max_position_per_stock')
    def validate_position_limit(cls, v):
        if not 0 < v <= 1:
            raise ValueError('Position limit must be between 0 and 1')
        return v


class DailyBacktestEnginePlugin(BasePlugin, IBacktestEngine, IRiskManager):
    """日K线回测引擎插件实现"""
    
    def __init__(self):
        super().__init__(
            name="daily_backtest_engine",
            version="1.0.0",
            description="日K线回测引擎插件，支持完整的交易模拟和风险管理",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._current_portfolio = {}
        self._trade_history = []
        self._equity_curve = []
        self._current_date = None
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return DailyBacktestEnginePluginConfig
    
    def _initialize(self) -> None:
        """初始化回测引擎"""
        self._current_portfolio = {
            'cash': self.config.get('initial_capital', 1000000.0),
            'positions': {},
            'total_equity': self.config.get('initial_capital', 1000000.0),
            'daily_returns': []
        }
        self._trade_history = []
        self._equity_curve = []
        self._current_date = None
    
    def run_backtest(self, strategy: Any, data: Any, **kwargs) -> Dict[str, Any]:
        """运行回测
        
        Args:
            strategy: 策略实例
            data: 回测数据 (DataFrame)
            **kwargs: 额外参数
            
        Returns:
            回测结果
        """
        try:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("Data must be a pandas DataFrame")
            
            # 确保数据按日期排序
            if 'date' not in data.columns and 'trade_date' not in data.columns:
                raise ValueError("Data must contain date column")
            
            date_col = 'date' if 'date' in data.columns else 'trade_date'
            data = data.sort_values(date_col).reset_index(drop=True)
            
            print(f"🚀 开始回测，数据长度: {len(data)}")
            print(f"   初始资金: {self._current_portfolio['cash']:,.2f}")
            
            # 运行回测循环
            for idx, row in data.iterrows():
                current_date = row[date_col]
                self._current_date = current_date
                
                # 更新持仓市值
                self._update_portfolio_value(row)
                
                # 执行策略
                if hasattr(strategy, 'execute'):
                    signal = strategy.execute(row, portfolio=self._current_portfolio)
                    
                    # 处理交易信号
                    if signal and signal.get('signal') != 'HOLD':
                        self._process_trade_signal(signal, row)
                
                # 记录每日权益
                self._record_daily_equity()
                
                # 检查风险限制
                if not self._check_risk_limits():
                    print(f"⚠️  风险限制触发，停止回测")
                    break
            
            # 生成回测报告
            results = self.generate_report({})
            
            print(f"✅ 回测完成")
            print(f"   最终权益: {self._current_portfolio['total_equity']:,.2f}")
            print(f"   总交易次数: {len(self._trade_history)}")
            
            return results
            
        except Exception as e:
            raise PluginError(f"Backtest execution failed: {e}")
    
    def _update_portfolio_value(self, market_data: pd.Series) -> None:
        """更新持仓市值"""
        total_value = self._current_portfolio['cash']
        
        for symbol, position in self._current_portfolio['positions'].items():
            if symbol in market_data and 'close' in market_data:
                # 使用当前价格更新持仓价值
                current_price = market_data['close']
                position_value = position['quantity'] * current_price
                position['market_value'] = position_value
                position['current_price'] = current_price
                total_value += position_value
            else:
                # 如果没有价格数据，保持原值
                total_value += position.get('market_value', 0)
        
        self._current_portfolio['total_equity'] = total_value
    
    def _process_trade_signal(self, signal: Dict, market_data: pd.Series) -> None:
        """处理交易信号"""
        symbol = signal.get('symbol', 'unknown')
        signal_type = signal.get('signal')
        confidence = signal.get('confidence', 0.5)
        
        if symbol == 'unknown' or 'close' not in market_data:
            return
        
        current_price = market_data['close']
        portfolio = self._current_portfolio
        
        # 构建交易信息
        trade = {
            'symbol': symbol,
            'signal': signal_type,
            'confidence': confidence,
            'current_price': current_price,
            'timestamp': self._current_date,
            'portfolio_value': portfolio['total_equity']
        }
        
        # 验证交易
        if not self.validate_trade(trade, portfolio):
            return
        
        # 执行交易
        if signal_type == 'BUY':
            self._execute_buy_trade(trade, portfolio)
        elif signal_type == 'SELL':
            self._execute_sell_trade(trade, portfolio)
        
        # 记录交易历史
        self._trade_history.append(trade)
    
    def _execute_buy_trade(self, trade: Dict, portfolio: Dict) -> None:
        """执行买入交易"""
        symbol = trade['symbol']
        current_price = trade['current_price']
        commission = self.config.get('commission', 0.0003)
        slippage = self.config.get('slippage', 0.0001)
        
        # 计算实际成交价格（考虑滑点）
        execution_price = current_price * (1 + slippage)
        
        # 计算可购买数量
        position_limit = self.config.get('max_position_per_stock', 0.2)
        max_position_value = portfolio['total_equity'] * position_limit
        available_cash = portfolio['cash']
        
        # 计算购买数量
        max_shares = min(
            available_cash // (execution_price * (1 + commission)),
            max_position_value // execution_price
        )
        
        if max_shares <= 0:
            return
        
        # 执行购买
        cost = max_shares * execution_price
        commission_cost = cost * commission
        total_cost = cost + commission_cost
        
        # 更新持仓
        if symbol in portfolio['positions']:
            position = portfolio['positions'][symbol]
            old_value = position['quantity'] * position['cost_price']
            new_quantity = position['quantity'] + max_shares
            new_cost_price = (old_value + cost) / new_quantity
            
            position['quantity'] = new_quantity
            position['cost_price'] = new_cost_price
            position['market_value'] = new_quantity * execution_price
        else:
            portfolio['positions'][symbol] = {
                'quantity': max_shares,
                'cost_price': execution_price,
                'market_value': max_shares * execution_price,
                'entry_date': self._current_date
            }
        
        # 更新现金
        portfolio['cash'] -= total_cost
        
        # 更新交易信息
        trade.update({
            'action': 'BUY',
            'quantity': max_shares,
            'price': execution_price,
            'commission': commission_cost,
            'total_cost': total_cost
        })
    
    def _execute_sell_trade(self, trade: Dict, portfolio: Dict) -> None:
        """执行卖出交易"""
        symbol = trade['symbol']
        current_price = trade['current_price']
        commission = self.config.get('commission', 0.0003)
        slippage = self.config.get('slippage', 0.0001)
        
        if symbol not in portfolio['positions']:
            return
        
        # 计算实际成交价格（考虑滑点）
        execution_price = current_price * (1 - slippage)
        
        position = portfolio['positions'][symbol]
        quantity = position['quantity']
        
        # 计算收益
        revenue = quantity * execution_price
        commission_cost = revenue * commission
        net_revenue = revenue - commission_cost
        
        # 计算盈亏
        cost_basis = quantity * position['cost_price']
        profit_loss = net_revenue - cost_basis
        
        # 更新现金和移除持仓
        portfolio['cash'] += net_revenue
        del portfolio['positions'][symbol]
        
        # 更新交易信息
        trade.update({
            'action': 'SELL',
            'quantity': quantity,
            'price': execution_price,
            'commission': commission_cost,
            'revenue': revenue,
            'net_revenue': net_revenue,
            'profit_loss': profit_loss,
            'return_pct': profit_loss / cost_basis if cost_basis > 0 else 0
        })
    
    def _record_daily_equity(self) -> None:
        """记录每日权益"""
        self._equity_curve.append({
            'date': self._current_date,
            'equity': self._current_portfolio['total_equity'],
            'cash': self._current_portfolio['cash'],
            'positions_value': self._current_portfolio['total_equity'] - self._current_portfolio['cash']
        })
        
        # 计算每日收益率
        if len(self._equity_curve) > 1:
            prev_equity = self._equity_curve[-2]['equity']
            current_equity = self._current_portfolio['total_equity']
            daily_return = (current_equity / prev_equity) - 1
            self._current_portfolio['daily_returns'].append(daily_return)
    
    def _check_risk_limits(self) -> bool:
        """检查风险限制"""
        # 检查最大回撤
        max_drawdown = self.calculate_max_drawdown()
        max_drawdown_limit = self.config.get('max_drawdown_limit', 0.3)
        
        if max_drawdown > max_drawdown_limit:
            print(f"⚠️  最大回撤 {max_drawdown:.1%} 超过限制 {max_drawdown_limit:.1%}")
            return False
        
        return True
    
    def validate_trade(self, trade: Dict, portfolio: Dict, **kwargs) -> bool:
        """验证交易是否合规"""
        symbol = trade['symbol']
        signal_type = trade['signal']
        
        # 检查是否允许卖空
        if signal_type == 'SELL' and symbol not in portfolio['positions']:
            if not self.config.get('enable_short_selling', False):
                return False
        
        # 检查仓位限制
        if signal_type == 'BUY':
            position_limit = self.config.get('max_position_per_stock', 0.2)
            current_positions_value = sum(
                pos['market_value'] for pos in portfolio['positions'].values()
            )
            new_position_value = trade.get('quantity', 0) * trade['current_price']
            
            if (current_positions_value + new_position_value) > portfolio['total_equity'] * position_limit:
                return False
        
        return True
    
    def get_risk_limits(self) -> Dict[str, float]:
        """获取风险限制"""
        return {
            'max_position_per_stock': self.config.get('max_position_per_stock', 0.2),
            'stop_loss': self.config.get('stop_loss', 0.1),
            'take_profit': self.config.get('take_profit', 0.2),
            'max_drawdown_limit': self.config.get('max_drawdown_limit', 0.3)
        }
    
    def calculate_risk_metrics(self, portfolio: Dict, **kwargs) -> Dict[str, float]:
        """计算风险指标"""
        equity_curve = pd.Series([x['equity'] for x in self._equity_curve])
        
        return {
            'max_drawdown': self.calculate_max_drawdown(),
            'volatility': self.calculate_volatility(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio()
        }
    
    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self._equity_curve:
            return 0.0
        
        equities = [x['equity'] for x in self._equity_curve]
        peak = equities[0]
        max_drawdown = 0.0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def calculate_volatility(self) -> float:
        """计算波动率"""
        returns = self._current_portfolio.get('daily_returns', [])
        if len(returns) < 2:
            return 0.0
        return np.std(returns) * np.sqrt(252)  # 年化波动率
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        returns = self._current_portfolio.get('daily_returns', [])
        if len(returns) < 2:
            return 0.0
        
        excess_returns = [r - risk_free_rate/252 for r in returns]
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """计算索提诺比率"""
        returns = self._current_portfolio.get('daily_returns', [])
        if len(returns) < 2:
            return 0.0
        
        excess_returns = [r - risk_free_rate/252 for r in returns]
        negative_returns = [r for r in excess_returns if r < 0]
        
        if not negative_returns:
            return 0.0
        
        sortino = np.mean(excess_returns) / np.std(negative_returns) * np.sqrt(252)
        return sortino
    
    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成回测报告"""
        equity_curve = pd.Series(
            [x['equity'] for x in self._equity_curve],
            index=[x['date'] for x in self._equity_curve]
        )
        
        initial_equity = self.config.get('initial_capital', 1000000.0)
        final_equity = self._current_portfolio['total_equity']
        total_return = (final_equity / initial_equity) - 1
        
        return {
            'performance': {
                'initial_equity': initial_equity,
                'final_equity': final_equity,
                'total_return': total_return,
                'annualized_return': self._calculate_annualized_return(total_return),
                'max_drawdown': self.calculate_max_drawdown(),
                'sharpe_ratio': self.calculate_sharpe_ratio(),
                'sortino_ratio': self.calculate_sortino_ratio(),
                'volatility': self.calculate_volatility()
            },
            'trades': {
                'total_trades': len(self._trade_history),
                'winning_trades': len([t for t in self._trade_history if t.get('profit_loss', 0) > 0]),
                'losing_trades': len([t for t in self._trade_history if t.get('profit_loss', 0) < 0]),
                'win_rate': len([t for t in self._trade_history if t.get('profit_loss', 0) > 0]) / len(self._trade_history) if self._trade_history else 0
            },
            'equity_curve': equity_curve,
            'trade_history': self._trade_history,
            'portfolio': self._current_portfolio
        }
    
    def _calculate_annualized_return(self, total_return: float) -> float:
        """计算年化收益率"""
        if not self._equity_curve or len(self._equity_curve) < 2:
            return 0.0
        
        days = len(self._equity_curve)
        years = days / 252  # 交易日年化
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
    
    def get_backtest_parameters(self) -> Dict[str, Any]:
        """获取回测参数"""
        return self.config.copy()
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为回测引擎组件
        registry.register_environment(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._current_portfolio.clear()
        self._trade_history.clear()
        self._equity_curve.clear()
        self._current_date = None