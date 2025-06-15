"""
Telemetry Sender for Azure IoT Device Application
Collects and formats telemetry data from Jetson Nano
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

from device_manager import DeviceManager
from config import Config


class TelemetrySender:
    """Handles telemetry data collection and formatting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.device_manager = DeviceManager()
        self.interval = self.config.telemetry_interval
        self._last_telemetry = None
        
    def set_interval(self, interval: int):
        """Set telemetry sending interval"""
        if interval > 0:
            self.interval = interval
            self.logger.info(f"Telemetry interval updated to {interval} seconds")
        else:
            self.logger.warning(f"Invalid telemetry interval: {interval}")
    
    async def collect_telemetry(self) -> Dict[str, Any]:
        """Collect comprehensive telemetry data"""
        telemetry = {
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': self.config.device_id,
            'device_type': self.config.device_type,
            'message_type': 'telemetry'
        }
        
        try:
            # Get system metrics
            system_metrics = self.device_manager.get_system_metrics()
            telemetry.update(system_metrics)
            
            # Add application-specific metrics
            app_metrics = self._get_application_metrics()
            telemetry['application'] = app_metrics
            
            # Add Jetson-specific metrics if available
            if self.device_manager.is_jetson:
                jetson_metrics = await self._get_jetson_telemetry()
                telemetry['jetson'] = jetson_metrics
            
            # Add network metrics
            network_metrics = await self._get_network_metrics()
            telemetry['network'] = network_metrics
            
            self._last_telemetry = telemetry
            
        except Exception as e:
            self.logger.error(f"Error collecting telemetry: {e}")
            # Return minimal telemetry on error
            telemetry = {
                'timestamp': datetime.utcnow().isoformat(),
                'device_id': self.config.device_id,
                'device_type': self.config.device_type,
                'message_type': 'telemetry',
                'error': str(e)
            }
        
        return telemetry
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        return {
            'uptime_seconds': self._get_application_uptime(),
            'telemetry_interval': self.interval,
            'auto_update_enabled': self.config.auto_update_enabled,
            'last_telemetry_size': len(json.dumps(self._last_telemetry)) if self._last_telemetry else 0
        }
    
    def _get_application_uptime(self) -> float:
        """Get application uptime in seconds"""
        # This is a simple implementation - you might want to track start time
        # in a more persistent way
        if not hasattr(self, '_start_time'):
            self._start_time = datetime.utcnow()
        
        return (datetime.utcnow() - self._start_time).total_seconds()
    
    async def _get_jetson_telemetry(self) -> Dict[str, Any]:
        """Get Jetson-specific telemetry data"""
        jetson_data = {}
        
        try:
            # Import jtop if available
            try:
                from jtop import jtop
                
                with jtop() as jetson:
                    if jetson.ok():
                        # GPU metrics
                        if self.config.gpu_metrics_enabled and hasattr(jetson, 'gpu'):
                            jetson_data['gpu'] = {
                                'usage_percent': jetson.gpu.get('GPU', 0),
                                'memory_used_mb': jetson.gpu.get('GPU Memory', 0),
                                'frequency_mhz': jetson.gpu.get('GPU Frequency', 0)
                            }
                        
                        # Power metrics
                        if hasattr(jetson, 'power'):
                            jetson_data['power'] = {
                                'total_watts': jetson.power.get('total', 0),
                                'cpu_watts': jetson.power.get('CPU', 0),
                                'gpu_watts': jetson.power.get('GPU', 0)
                            }
                        
                        # EMC (memory controller) metrics
                        if hasattr(jetson, 'emc'):
                            jetson_data['memory_controller'] = {
                                'usage_percent': jetson.emc.get('EMC', 0),
                                'frequency_mhz': jetson.emc.get('EMC Frequency', 0)
                            }
                        
                        # Fan metrics
                        if hasattr(jetson, 'fan'):
                            jetson_data['fan'] = {
                                'speed_percent': jetson.fan.get('Fan', 0)
                            }
                        
                        # Engine metrics (various processing units)
                        if hasattr(jetson, 'engine'):
                            jetson_data['engines'] = jetson.engine
                        
            except ImportError:
                self.logger.debug("jtop not available, skipping Jetson-specific metrics")
            except Exception as e:
                self.logger.error(f"Error getting jtop metrics: {e}")
            
            # Get additional temperature data
            temperatures = self.device_manager._get_temperatures()
            if temperatures:
                jetson_data['temperatures'] = temperatures
            
        except Exception as e:
            self.logger.error(f"Error collecting Jetson telemetry: {e}")
        
        return jetson_data
    
    async def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network-related metrics"""
        network_data = {}
        
        try:
            # Try to get network stats using psutil
            try:
                import psutil
                
                # Network I/O statistics
                net_io = psutil.net_io_counters()
                if net_io:
                    network_data['io'] = {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv,
                        'errin': net_io.errin,
                        'errout': net_io.errout,
                        'dropin': net_io.dropin,
                        'dropout': net_io.dropout
                    }
                
                # Network interface information
                net_if_addrs = psutil.net_if_addrs()
                interfaces = {}
                for interface_name, addrs in net_if_addrs.items():
                    interfaces[interface_name] = []
                    for addr in addrs:
                        interfaces[interface_name].append({
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                
                network_data['interfaces'] = interfaces
                
            except ImportError:
                self.logger.debug("psutil not available for network metrics")
            
            # Add connection status (simple ping test)
            network_data['connectivity'] = await self._test_connectivity()
            
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
        
        return network_data
    
    async def _test_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity"""
        connectivity = {
            'internet_available': False,
            'azure_reachable': False,
            'last_check': datetime.utcnow().isoformat()
        }
        
        try:
            # Test internet connectivity
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '3', '8.8.8.8',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            connectivity['internet_available'] = proc.returncode == 0
            
            # Test Azure connectivity
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '3', 'azure.microsoft.com',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            connectivity['azure_reachable'] = proc.returncode == 0
            
        except Exception as e:
            self.logger.debug(f"Connectivity test error: {e}")
        
        return connectivity
    
    def get_last_telemetry(self) -> Optional[Dict[str, Any]]:
        """Get the last collected telemetry data"""
        return self._last_telemetry
    
    def format_telemetry_for_display(self, telemetry: Dict[str, Any]) -> str:
        """Format telemetry data for human-readable display"""
        try:
            formatted = f"Telemetry Data ({telemetry.get('timestamp', 'Unknown time')}):\n"
            formatted += f"  Device: {telemetry.get('device_id', 'Unknown')} ({telemetry.get('device_type', 'Unknown type')})\n"
            
            if 'cpu_percent' in telemetry:
                formatted += f"  CPU Usage: {telemetry['cpu_percent']:.1f}%\n"
            
            if 'memory_percent' in telemetry:
                formatted += f"  Memory Usage: {telemetry['memory_percent']:.1f}%\n"
            
            if 'disk_percent' in telemetry:
                formatted += f"  Disk Usage: {telemetry['disk_percent']:.1f}%\n"
            
            if 'temperatures' in telemetry:
                temps = telemetry['temperatures']
                if temps:
                    temp_str = ", ".join([f"{k}: {v:.1f}°C" for k, v in temps.items()])
                    formatted += f"  Temperatures: {temp_str}\n"
            
            if 'jetson' in telemetry and telemetry['jetson']:
                jetson_data = telemetry['jetson']
                if 'gpu' in jetson_data:
                    gpu = jetson_data['gpu']
                    formatted += f"  GPU Usage: {gpu.get('usage_percent', 0):.1f}%\n"
                
                if 'power' in jetson_data:
                    power = jetson_data['power']
                    formatted += f"  Power Usage: {power.get('total_watts', 0):.1f}W\n"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting telemetry: {e}")
            return f"Error formatting telemetry: {str(e)}" 