"""
实时监控插件
提供实时性能监控和风险预警功能

功能:
- 实时性能监控和指标计算
- 异常检测和风险预警
- 系统状态检查和健康监测
- 报警通知和日志记录
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import logging

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IMonitor

# 插件配置模型
class RealtimeMonitorPluginConfig(BaseModel):
    """实时监控插件配置"""
    
    monitoring_interval: int = Field(60, description="监控间隔(秒)")
    anomaly_threshold: float = Field(3.0, description="异常检测阈值")
    max_alerts_per_hour: int = Field(10, description="每小时最大警报数量")
    enable_email_alerts: bool = Field(False, description="是否启用邮件警报")
    enable_sms_alerts: bool = Field(False, description="是否启用短信警报")
    log_level: str = Field("INFO", description="日志级别")
    
    @validator('monitoring_interval')
    def validate_monitoring_interval(cls, v):
        if v < 1:
            raise ValueError('Monitoring interval must be at least 1 second')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v


class RealtimeMonitorPlugin(BasePlugin, IMonitor):
    """实时监控插件实现"""
    
    def __init__(self):
        super().__init__(
            name="realtime_monitor",
            version="1.0.0",
            description="实时监控插件，提供系统监控和风险预警功能",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._metrics_history = []
        self._anomalies_detected = []
        self._alerts_sent = []
        self._logger = None
        self._last_monitor_time = None
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return RealtimeMonitorPluginConfig
    
    def _initialize(self) -> None:
        """初始化监控器"""
        # 设置日志
        self._setup_logging()
        
        self._metrics_history = []
        self._anomalies_detected = []
        self._alerts_sent = []
        self._last_monitor_time = datetime.now()
        
        self._logger.info("实时监控插件初始化完成")
    
    def _setup_logging(self) -> None:
        """设置日志系统"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        
        self._logger = logging.getLogger(f"ascend.monitor.{self.name}")
        self._logger.setLevel(log_level)
        
        # 如果没有处理器，添加一个
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def monitor_performance(self, metrics: Dict[str, Any], **kwargs) -> None:
        """监控性能指标
        
        Args:
            metrics: 性能指标
            **kwargs: 额外参数
        """
        try:
            current_time = datetime.now()
            
            # 检查监控间隔
            if self._last_monitor_time:
                time_diff = (current_time - self._last_monitor_time).total_seconds()
                if time_diff < self.config.get('monitoring_interval', 60):
                    return
            
            self._last_monitor_time = current_time
            
            # 记录指标
            metric_record = {
                'timestamp': current_time,
                'metrics': metrics.copy(),
                'system_status': self._get_system_status()
            }
            self._metrics_history.append(metric_record)
            
            # 保持历史记录大小
            max_history = 1000
            if len(self._metrics_history) > max_history:
                self._metrics_history = self._metrics_history[-max_history:]
            
            # 检测异常
            anomalies = self.detect_anomalies(metric_record)
            if anomalies:
                self._anomalies_detected.extend(anomalies)
                self._logger.warning(f"检测到 {len(anomalies)} 个异常")
                
                # 生成警报
                alerts = self.generate_alerts(anomalies)
                if alerts:
                    self._alerts_sent.extend(alerts)
                    self._logger.info(f"发送 {len(alerts)} 个警报")
            
            # 记录监控日志
            self._log_monitoring_data(metric_record, anomalies)
            
        except Exception as e:
            self._logger.error(f"性能监控失败: {e}")
    
    def detect_anomalies(self, data: Any, **kwargs) -> List[Dict[str, Any]]:
        """检测异常情况
        
        Args:
            data: 监控数据
            **kwargs: 额外参数
            
        Returns:
            异常情况列表
        """
        anomalies = []
        
        try:
            if not isinstance(data, dict) or 'metrics' not in data:
                return anomalies
            
            metrics = data['metrics']
            timestamp = data.get('timestamp', datetime.now())
            
            # 检查关键指标异常
            anomalies.extend(self._check_performance_anomalies(metrics, timestamp))
            
            # 检查系统状态异常
            anomalies.extend(self._check_system_anomalies(data.get('system_status', {}), timestamp))
            
            # 检查数据质量异常
            anomalies.extend(self._check_data_quality_anomalies(metrics, timestamp))
            
        except Exception as e:
            self._logger.error(f"异常检测失败: {e}")
        
        return anomalies
    
    def _check_performance_anomalies(self, metrics: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """检查性能异常"""
        anomalies = []
        threshold = self.config.get('anomaly_threshold', 3.0)
        
        # 检查收益率异常
        if 'daily_return' in metrics:
            return_val = metrics['daily_return']
            if abs(return_val) > 0.1:  # 单日涨跌幅超过10%
                anomalies.append({
                    'type': 'PERFORMANCE_ANOMALY',
                    'severity': 'HIGH' if abs(return_val) > 0.2 else 'MEDIUM',
                    'metric': 'daily_return',
                    'value': return_val,
                    'threshold': 0.1,
                    'timestamp': timestamp,
                    'description': f'异常日收益率: {return_val:.2%}'
                })
        
        # 检查波动率异常
        if 'volatility' in metrics:
            volatility = metrics['volatility']
            if volatility > 0.5:  # 年化波动率超过50%
                anomalies.append({
                    'type': 'VOLATILITY_ANOMALY',
                    'severity': 'HIGH',
                    'metric': 'volatility',
                    'value': volatility,
                    'threshold': 0.5,
                    'timestamp': timestamp,
                    'description': f'异常波动率: {volatility:.2%}'
                })
        
        # 检查回撤异常
        if 'max_drawdown' in metrics:
            drawdown = metrics['max_drawdown']
            if drawdown > 0.2:  # 回撤超过20%
                anomalies.append({
                    'type': 'DRAWDOWN_ANOMALY',
                    'severity': 'HIGH' if drawdown > 0.3 else 'MEDIUM',
                    'metric': 'max_drawdown',
                    'value': drawdown,
                    'threshold': 0.2,
                    'timestamp': timestamp,
                    'description': f'异常回撤: {drawdown:.2%}'
                })
        
        return anomalies
    
    def _check_system_anomalies(self, system_status: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """检查系统状态异常"""
        anomalies = []
        
        # 检查内存使用
        if 'memory_usage' in system_status and system_status['memory_usage'] > 0.9:
            anomalies.append({
                'type': 'SYSTEM_ANOMALY',
                'severity': 'HIGH',
                'metric': 'memory_usage',
                'value': system_status['memory_usage'],
                'threshold': 0.9,
                'timestamp': timestamp,
                'description': f'内存使用率过高: {system_status["memory_usage"]:.1%}'
            })
        
        # 检查CPU使用
        if 'cpu_usage' in system_status and system_status['cpu_usage'] > 0.8:
            anomalies.append({
                'type': 'SYSTEM_ANOMALY',
                'severity': 'MEDIUM',
                'metric': 'cpu_usage',
                'value': system_status['cpu_usage'],
                'threshold': 0.8,
                'timestamp': timestamp,
                'description': f'CPU使用率过高: {system_status["cpu_usage"]:.1%}'
            })
        
        return anomalies
    
    def _check_data_quality_anomalies(self, metrics: Dict[str, Any], timestamp: datetime) -> List[Dict[str, Any]]:
        """检查数据质量异常"""
        anomalies = []
        
        # 检查数据缺失
        if 'data_quality' in metrics and metrics['data_quality'] < 0.9:
            anomalies.append({
                'type': 'DATA_QUALITY_ANOMALY',
                'severity': 'MEDIUM',
                'metric': 'data_quality',
                'value': metrics['data_quality'],
                'threshold': 0.9,
                'timestamp': timestamp,
                'description': f'数据质量下降: {metrics["data_quality"]:.1%}'
            })
        
        # 检查数据延迟
        if 'data_latency' in metrics and metrics['data_latency'] > 60:  # 延迟超过60秒
            anomalies.append({
                'type': 'DATA_LATENCY_ANOMALY',
                'severity': 'MEDIUM',
                'metric': 'data_latency',
                'value': metrics['data_latency'],
                'threshold': 60,
                'timestamp': timestamp,
                'description': f'数据延迟过高: {metrics["data_latency"]}秒'
            })
        
        return anomalies
    
    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            import psutil
            return {
                'memory_usage': psutil.virtual_memory().percent / 100,
                'cpu_usage': psutil.cpu_percent() / 100,
                'disk_usage': psutil.disk_usage('/').percent / 100,
                'process_count': len(psutil.pids()),
                'boot_time': psutil.boot_time()
            }
        except ImportError:
            # 如果没有psutil，返回简化状态
            return {
                'memory_usage': 0.5,
                'cpu_usage': 0.3,
                'disk_usage': 0.6,
                'process_count': 0,
                'boot_time': 0
            }
    
    def generate_alerts(self, anomalies: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """生成警报
        
        Args:
            anomalies: 异常情况
            **kwargs: 额外参数
            
        Returns:
            警报列表
        """
        alerts = []
        max_alerts = self.config.get('max_alerts_per_hour', 10)
        
        # 检查警报频率限制
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        recent_alerts = [a for a in self._alerts_sent 
                        if a.get('timestamp', datetime.min) >= current_hour]
        
        if len(recent_alerts) >= max_alerts:
            self._logger.warning(f"已达到每小时警报限制: {len(recent_alerts)}/{max_alerts}")
            return alerts
        
        for anomaly in anomalies:
            if anomaly['severity'] in ['HIGH', 'CRITICAL']:
                alert = self._create_alert(anomaly)
                alerts.append(alert)
                
                # 检查是否达到限制
                if len(alerts) + len(recent_alerts) >= max_alerts:
                    self._logger.warning("达到警报限制，停止生成新警报")
                    break
        
        return alerts
    
    def _create_alert(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """创建警报"""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._alerts_sent)}"
        
        alert = {
            'alert_id': alert_id,
            'type': anomaly['type'],
            'severity': anomaly['severity'],
            'metric': anomaly['metric'],
            'value': anomaly['value'],
            'threshold': anomaly['threshold'],
            'timestamp': datetime.now(),
            'description': anomaly['description'],
            'status': 'NEW',
            'acknowledged': False,
            'action_required': anomaly['severity'] in ['HIGH', 'CRITICAL']
        }
        
        # 发送通知
        self._send_notification(alert)
        
        return alert
    
    def _send_notification(self, alert: Dict[str, Any]) -> None:
        """发送通知"""
        try:
            # 记录日志
            self._logger.warning(f"警报: {alert['description']} - 严重程度: {alert['severity']}")
            
            # 这里可以添加邮件、短信等通知方式
            if self.config.get('enable_email_alerts', False):
                self._send_email_alert(alert)
            
            if self.config.get('enable_sms_alerts', False):
                self._send_sms_alert(alert)
                
        except Exception as e:
            self._logger.error(f"通知发送失败: {e}")
    
    def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """发送邮件警报"""
        # 邮件发送实现占位
        pass
    
    def _send_sms_alert(self, alert: Dict[str, Any]) -> None:
        """发送短信警报"""
        # 短信发送实现占位
        pass
    
    def _log_monitoring_data(self, metric_record: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> None:
        """记录监控数据"""
        log_data = {
            'timestamp': metric_record['timestamp'],
            'metrics_count': len(metric_record['metrics']),
            'anomalies_count': len(anomalies),
            'system_status': metric_record.get('system_status', {})
        }
        
        if anomalies:
            self._logger.warning(f"监控数据: {log_data}")
        else:
            self._logger.info(f"监控数据: {log_data}")
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为监控组件
        registry.register_monitor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._metrics_history.clear()
        self._anomalies_detected.clear()
        self._alerts_sent.clear()
        self._last_monitor_time = None
        
        if self._logger:
            self._logger.info("实时监控插件清理完成")