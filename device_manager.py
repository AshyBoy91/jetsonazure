"""
Device Manager for Jetson Nano specific operations
"""

import asyncio
import logging
import os
import platform
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from jtop import jtop
    JTOP_AVAILABLE = True
except ImportError:
    JTOP_AVAILABLE = False


class DeviceManager:
    """Manages device-specific operations for Jetson Nano"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_jetson = self._detect_jetson()
        
    def _detect_jetson(self) -> bool:
        """Detect if running on Jetson Nano"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                return 'jetson' in model.lower()
        except FileNotFoundError:
            return False
        except Exception as e:
            self.logger.warning(f"Could not detect Jetson hardware: {e}")
            return False
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information"""
        info = {
            'timestamp': datetime.utcnow().isoformat(),
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_jetson': self.is_jetson
        }
        
        # Add system resources if psutil is available
        if PSUTIL_AVAILABLE:
            info.update(self._get_system_resources())
        
        # Add Jetson-specific information
        if self.is_jetson:
            info.update(await self._get_jetson_info())
        
        return info
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information using psutil"""
        try:
            # CPU information
            cpu_info = {
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'memory_used': memory.used
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_percent': (disk.used / disk.total) * 100
            }
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': (datetime.now() - boot_time).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
            return {}
    
    async def _get_jetson_info(self) -> Dict[str, Any]:
        """Get Jetson-specific information"""
        jetson_info = {}
        
        try:
            # Get Jetson model
            jetson_info['jetson_model'] = self._get_jetson_model()
            
            # Get JetPack version
            jetson_info['jetpack_version'] = self._get_jetpack_version()
            
            # Get CUDA version
            jetson_info['cuda_version'] = self._get_cuda_version()
            
            # Get temperature information
            jetson_info['temperatures'] = self._get_temperatures()
            
            # Get GPU information if jtop is available
            if JTOP_AVAILABLE:
                jetson_info['gpu_info'] = await self._get_gpu_info()
            
        except Exception as e:
            self.logger.error(f"Error getting Jetson information: {e}")
        
        return jetson_info
    
    def _get_jetson_model(self) -> Optional[str]:
        """Get Jetson model information"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return f.read().strip()
        except Exception:
            return None
    
    def _get_jetpack_version(self) -> Optional[str]:
        """Get JetPack version"""
        try:
            result = subprocess.run(['dpkg', '-l', 'nvidia-jetpack'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'nvidia-jetpack' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
        except Exception:
            pass
        return None
    
    def _get_cuda_version(self) -> Optional[str]:
        """Get CUDA version"""
        try:
            result = subprocess.run(['nvcc', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line.lower():
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.lower() == 'release':
                                if i + 1 < len(parts):
                                    return parts[i + 1].rstrip(',')
        except Exception:
            pass
        return None
    
    def _get_temperatures(self) -> Dict[str, float]:
        """Get system temperatures"""
        temperatures = {}
        
        # Try to read from thermal zones
        thermal_zones = ['/sys/class/thermal/thermal_zone0/temp',
                        '/sys/class/thermal/thermal_zone1/temp']
        
        for i, zone_path in enumerate(thermal_zones):
            try:
                with open(zone_path, 'r') as f:
                    temp_millicelsius = int(f.read().strip())
                    temp_celsius = temp_millicelsius / 1000.0
                    temperatures[f'thermal_zone_{i}'] = temp_celsius
            except Exception:
                continue
        
        return temperatures
    
    async def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information using jtop"""
        gpu_info = {}
        
        try:
            with jtop() as jetson:
                if jetson.ok():
                    gpu_info = {
                        'gpu_usage': jetson.gpu,
                        'memory_usage': jetson.memory,
                        'power_usage': jetson.power
                    }
        except Exception as e:
            self.logger.error(f"Error getting GPU info: {e}")
        
        return gpu_info
    
    async def reboot_device(self):
        """Reboot the device"""
        self.logger.warning("Reboot requested - initiating system reboot")
        
        try:
            # Give some time for the response to be sent
            await asyncio.sleep(2)
            
            # Execute reboot command
            if os.name == 'posix':  # Unix-like systems
                subprocess.run(['sudo', 'reboot'], check=True)
            else:
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to reboot device: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during reboot: {e}")
            raise
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if PSUTIL_AVAILABLE:
            try:
                metrics.update({
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                })
            except Exception as e:
                self.logger.error(f"Error getting system metrics: {e}")
        
        # Add temperature metrics
        if self.is_jetson:
            metrics['temperatures'] = self._get_temperatures()
        
        return metrics 