"""
模拟交易器插件
提供模拟交易执行和仓位管理功能

功能:
- 模拟交易执行
- 仓位管理和控制
- 订单处理和状态跟踪
- 交易成本模拟
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import ITrader, IRiskController

# 插件配置模型
class SimTraderPluginConfig(BaseModel):
    """模拟交易器配置"""
    
    initial_capital: float = Field(1000000.0, description="初始资金")
    commission_rate: float = Field(0.0003, description="佣金费率")
    slippage_rate: float = Field(0.0001, description="滑点费率")
    max_position_per_stock: float = Field(0.2, description="单股票最大仓位比例")
    min_trade_amount: float = Field(1000.0, description="最小交易金额")
    trade_execution_delay: int = Field(0, description="交易执行延迟(秒)")
    enable_short_selling: bool = Field(False, description="是否允许卖空")
    
    @field_validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v <= 0:
            raise ValueError('Initial capital must be positive')
        return v
    
    @field_validator('commission_rate', 'slippage_rate')
    def validate_rates(cls, v):
        if v < 0:
            raise ValueError('Rates cannot be negative')
        return v
    
    @field_validator('max_position_per_stock')
    def validate_position_limit(cls, v):
        if not 0 < v <= 1:
            raise ValueError('Position limit must be between 0 and 1')
        return v


class SimTraderPlugin(BasePlugin, ITrader, IRiskController):
    """模拟交易器插件实现"""
    
    def __init__(self):
        super().__init__(
            name="sim_trader",
            version="1.0.0",
            description="模拟交易器插件，提供完整的交易执行和仓位管理",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._account = {}
        self._positions = {}
        self._order_history = []
        self._trade_history = []
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return SimTraderPluginConfig
    
    def _initialize(self) -> None:
        """初始化交易器"""
        self._account = {
            'cash': self.config.get('initial_capital', 1000000.0),
            'total_equity': self.config.get('initial_capital', 1000000.0),
            'available_cash': self.config.get('initial_capital', 1000000.0),
            'frozen_cash': 0.0,
            'update_time': datetime.now()
        }
        self._positions = {}
        self._order_history = []
        self._trade_history = []
    
    def execute_order(self, order: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行交易订单
        
        Args:
            order: 订单信息
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
        try:
            # 验证订单
            validation_result = self._validate_order(order)
            if not validation_result['valid']:
                return {
                    'status': 'REJECTED',
                    'reason': validation_result['reason'],
                    'order_id': order.get('order_id', str(uuid.uuid4()))
                }
            
            # 创建订单记录
            order_record = self._create_order_record(order)
            self._order_history.append(order_record)
            
            # 执行订单
            if order['action'] == 'BUY':
                execution_result = self._execute_buy_order(order)
            elif order['action'] == 'SELL':
                execution_result = self._execute_sell_order(order)
            else:
                return {
                    'status': 'REJECTED',
                    'reason': f"Invalid action: {order['action']}",
                    'order_id': order_record['order_id']
                }
            
            # 更新订单状态
            order_record.update(execution_result)
            order_record['status'] = 'FILLED' if execution_result['executed_quantity'] > 0 else 'CANCELLED'
            
            # 记录交易
            if execution_result['executed_quantity'] > 0:
                trade_record = self._create_trade_record(order_record, execution_result)
                self._trade_history.append(trade_record)
            
            return order_record
            
        except Exception as e:
            raise PluginError(f"Order execution failed: {e}")
    
    def _validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """验证订单"""
        required_fields = ['symbol', 'action', 'quantity', 'price']
        for field in required_fields:
            if field not in order:
                return {'valid': False, 'reason': f'Missing required field: {field}'}
        
        # 检查交易动作
        if order['action'] not in ['BUY', 'SELL']:
            return {'valid': False, 'reason': f"Invalid action: {order['action']}"}
        
        # 检查数量
        if order['quantity'] <= 0:
            return {'valid': False, 'reason': 'Quantity must be positive'}
        
        # 检查价格
        if order['price'] <= 0:
            return {'valid': False, 'reason': 'Price must be positive'}
        
        # 检查卖空权限
        if order['action'] == 'SELL' and order['symbol'] not in self._positions:
            if not self.config.get('enable_short_selling', False):
                return {'valid': False, 'reason': 'Short selling not allowed'}
        
        return {'valid': True, 'reason': 'OK'}
    
    def _create_order_record(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """创建订单记录"""
        return {
            'order_id': order.get('order_id', str(uuid.uuid4())),
            'symbol': order['symbol'],
            'action': order['action'],
            'quantity': order['quantity'],
            'price': order['price'],
            'order_type': order.get('order_type', 'LIMIT'),
            'status': 'PENDING',
            'create_time': datetime.now(),
            'update_time': datetime.now(),
            'strategy': order.get('strategy', 'unknown'),
            'reason': order.get('reason', '')
        }
    
    def _execute_buy_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """执行买入订单"""
        symbol = order['symbol']
        order_price = order['price']
        order_quantity = order['quantity']
        
        # 计算实际成交价格（考虑滑点）
        slippage = self.config.get('slippage_rate', 0.0001)
        execution_price = order_price * (1 + slippage)
        
        # 计算交易成本
        commission = self.config.get('commission_rate', 0.0003)
        total_cost = order_quantity * execution_price
        commission_cost = total_cost * commission
        
        # 检查资金是否足够
        available_cash = self._account['available_cash']
        if total_cost + commission_cost > available_cash:
            # 部分成交或取消
            max_affordable = available_cash / (execution_price * (1 + commission))
            executed_quantity = int(max_affordable)
            
            if executed_quantity <= 0:
                return {
                    'executed_quantity': 0,
                    'execution_price': 0,
                    'commission': 0,
                    'slippage': 0,
                    'reason': 'Insufficient funds'
                }
        else:
            executed_quantity = order_quantity
        
        # 计算实际成交金额
        executed_amount = executed_quantity * execution_price
        executed_commission = executed_amount * commission
        
        # 更新账户
        self._account['cash'] -= (executed_amount + executed_commission)
        self._account['available_cash'] = self._account['cash'] - self._account['frozen_cash']
        self._account['update_time'] = datetime.now()
        
        # 更新持仓
        if symbol in self._positions:
            position = self._positions[symbol]
            # 计算平均成本
            old_value = position['quantity'] * position['cost_price']
            new_quantity = position['quantity'] + executed_quantity
            new_cost_price = (old_value + executed_amount) / new_quantity
            
            position['quantity'] = new_quantity
            position['cost_price'] = new_cost_price
            position['market_value'] = new_quantity * execution_price
            position['update_time'] = datetime.now()
        else:
            self._positions[symbol] = {
                'symbol': symbol,
                'quantity': executed_quantity,
                'cost_price': execution_price,
                'market_value': executed_quantity * execution_price,
                'entry_price': execution_price,
                'entry_time': datetime.now(),
                'update_time': datetime.now()
            }
        
        # 更新总权益
        self._update_total_equity(execution_price)
        
        return {
            'executed_quantity': executed_quantity,
            'execution_price': execution_price,
            'commission': executed_commission,
            'slippage': slippage * executed_amount,
            'total_cost': executed_amount + executed_commission,
            'reason': 'Filled' if executed_quantity == order_quantity else 'Partial fill'
        }
    
    def _execute_sell_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """执行卖出订单"""
        symbol = order['symbol']
        order_price = order['price']
        order_quantity = order['quantity']
        
        # 检查持仓
        if symbol not in self._positions:
            if self.config.get('enable_short_selling', False):
                # 卖空逻辑
                return self._execute_short_sell(order)
            else:
                return {
                    'executed_quantity': 0,
                    'execution_price': 0,
                    'commission': 0,
                    'slippage': 0,
                    'reason': 'No position and short selling not allowed'
                }
        
        position = self._positions[symbol]
        available_quantity = position['quantity']
        
        # 计算实际成交数量
        executed_quantity = min(order_quantity, available_quantity)
        if executed_quantity <= 0:
            return {
                'executed_quantity': 0,
                'execution_price': 0,
                'commission': 0,
                'slippage': 0,
                'reason': 'No available position'
            }
        
        # 计算实际成交价格（考虑滑点）
        slippage = self.config.get('slippage_rate', 0.0001)
        execution_price = order_price * (1 - slippage)
        
        # 计算交易成本
        commission = self.config.get('commission_rate', 0.0003)
        total_revenue = executed_quantity * execution_price
        commission_cost = total_revenue * commission
        
        # 计算盈亏
        cost_basis = executed_quantity * position['cost_price']
        profit_loss = total_revenue - commission_cost - cost_basis
        
        # 更新账户
        self._account['cash'] += (total_revenue - commission_cost)
        self._account['available_cash'] = self._account['cash'] - self._account['frozen_cash']
        self._account['update_time'] = datetime.now()
        
        # 更新持仓
        position['quantity'] -= executed_quantity
        position['market_value'] = position['quantity'] * execution_price
        position['update_time'] = datetime.now()
        
        # 如果持仓为0，移除该持仓
        if position['quantity'] <= 0:
            del self._positions[symbol]
        
        # 更新总权益
        self._update_total_equity(execution_price)
        
        return {
            'executed_quantity': executed_quantity,
            'execution_price': execution_price,
            'commission': commission_cost,
            'slippage': slippage * total_revenue,
            'total_revenue': total_revenue - commission_cost,
            'profit_loss': profit_loss,
            'return_pct': profit_loss / cost_basis if cost_basis > 0 else 0,
            'reason': 'Filled' if executed_quantity == order_quantity else 'Partial fill'
        }
    
    def _execute_short_sell(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """执行卖空订单"""
        # 简化实现：卖空逻辑
        # 实际实现需要更复杂的保证金管理和风险控制
        return {
            'executed_quantity': 0,
            'execution_price': 0,
            'commission': 0,
            'slippage': 0,
            'reason': 'Short selling not implemented'
        }
    
    def _update_total_equity(self, current_price: float) -> None:
        """更新总权益"""
        positions_value = sum(pos['market_value'] for pos in self._positions.values())
        self._account['total_equity'] = self._account['cash'] + positions_value
    
    def _create_trade_record(self, order: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
        """创建交易记录"""
        return {
            'trade_id': str(uuid.uuid4()),
            'order_id': order['order_id'],
            'symbol': order['symbol'],
            'action': order['action'],
            'quantity': execution['executed_quantity'],
            'price': execution['execution_price'],
            'commission': execution['commission'],
            'slippage': execution.get('slippage', 0),
            'total_amount': execution.get('total_cost', 0) if order['action'] == 'BUY' else execution.get('total_revenue', 0),
            'profit_loss': execution.get('profit_loss', 0),
            'return_pct': execution.get('return_pct', 0),
            'trade_time': datetime.now(),
            'strategy': order.get('strategy', 'unknown')
        }
    
    def get_position(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """获取持仓信息"""
        if symbol in self._positions:
            position = self._positions[symbol].copy()
            position['unrealized_pnl'] = position['market_value'] - (position['quantity'] * position['cost_price'])
            position['unrealized_pnl_pct'] = position['unrealized_pnl'] / (position['quantity'] * position['cost_price']) if position['quantity'] * position['cost_price'] > 0 else 0
            return position
        else:
            return {
                'symbol': symbol,
                'quantity': 0,
                'cost_price': 0,
                'market_value': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_pct': 0
            }
    
    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        """获取账户信息"""
        account_info = self._account.copy()
        account_info['positions_count'] = len(self._positions)
        account_info['total_positions_value'] = sum(pos['market_value'] for pos in self._positions.values())
        account_info['cash_ratio'] = account_info['cash'] / account_info['total_equity'] if account_info['total_equity'] > 0 else 0
        return account_info
    
    def check_risk_limits(self, portfolio: Dict[str, Any], **kwargs) -> Dict[str, bool]:
        """检查风险限制"""
        # 简化实现
        return {
            'position_limit_ok': True,
            'liquidity_ok': True,
            'leverage_ok': True,
            'concentration_ok': True
        }
    
    def enforce_risk_rules(self, portfolio: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """执行风险规则"""
        # 简化实现
        return []
    
    def get_risk_status(self, **kwargs) -> Dict[str, Any]:
        """获取风险状态"""
        return {
            'status': 'NORMAL',
            'warnings': [],
            'limits': self.config.copy()
        }
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为交易执行组件
        registry.register_policy(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._account.clear()
        self._positions.clear()
        self._order_history.clear()
        self._trade_history.clear()