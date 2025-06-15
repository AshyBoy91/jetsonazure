"""
Configuration management for Azure IoT Device Application
"""

import os
from typing import Optional


class Config:
    """Configuration class for the IoT device application"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables and defaults"""
        
        # Azure IoT Hub Configuration
        self.connection_string = os.getenv(
            'AZURE_IOT_CONNECTION_STRING',
            ''
        )
        
        if not self.connection_string:
            raise ValueError(
                "AZURE_IOT_CONNECTION_STRING environment variable is required. "
                "Get this from your Azure IoT Hub device connection string."
            )
        
        # Device Configuration
        self.device_id = os.getenv('DEVICE_ID', 'jetson-nano-001')
        self.device_type = os.getenv('DEVICE_TYPE', 'jetson-nano')
        
        # Telemetry Configuration
        self.telemetry_interval = int(os.getenv('TELEMETRY_INTERVAL', '30'))  # seconds
        self.enable_cpu_metrics = os.getenv('ENABLE_CPU_METRICS', 'true').lower() == 'true'
        self.enable_memory_metrics = os.getenv('ENABLE_MEMORY_METRICS', 'true').lower() == 'true'
        self.enable_disk_metrics = os.getenv('ENABLE_DISK_METRICS', 'true').lower() == 'true'
        self.enable_temperature_metrics = os.getenv('ENABLE_TEMPERATURE_METRICS', 'true').lower() == 'true'
        
        # Update Configuration
        self.auto_update_enabled = os.getenv('AUTO_UPDATE_ENABLED', 'false').lower() == 'true'
        self.github_repo = os.getenv('GITHUB_REPO', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.update_branch = os.getenv('UPDATE_BRANCH', 'main')
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Jetson Nano Specific Configuration
        self.jetson_stats_enabled = os.getenv('JETSON_STATS_ENABLED', 'true').lower() == 'true'
        self.gpu_metrics_enabled = os.getenv('GPU_METRICS_ENABLED', 'true').lower() == 'true'
        
    def get_azure_connection_string(self) -> str:
        """Get Azure IoT Hub connection string"""
        return self.connection_string
    
    def get_device_info(self) -> dict:
        """Get device information as dictionary"""
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'telemetry_interval': self.telemetry_interval,
            'auto_update_enabled': self.auto_update_enabled,
            'jetson_stats_enabled': self.jetson_stats_enabled,
            'gpu_metrics_enabled': self.gpu_metrics_enabled
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        if not self.connection_string:
            return False
        
        if self.telemetry_interval < 1:
            return False
        
        if self.auto_update_enabled and not self.github_repo:
            return False
        
        return True


# Create a global config instance
config = Config() 