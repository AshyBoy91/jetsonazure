#!/usr/bin/env python3
"""
Azure IoT Edge Module for Jetson Nano
Enhanced version with edge computing capabilities
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import statistics

from azure.iot.device import IoTHubModuleClient, Message
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError

from config import Config
from device_manager import DeviceManager
from telemetry_sender import TelemetrySender
from update_manager import UpdateManager
from edge_analytics import EdgeAnalytics


class AzureIoTEdgeModule:
    """Azure IoT Edge Module for Jetson Nano with local processing"""
    
    def __init__(self):
        self.config = Config()
        self.module_client: Optional[IoTHubModuleClient] = None
        self.device_manager = DeviceManager()
        self.telemetry_sender = TelemetrySender()
        self.update_manager = UpdateManager()
        self.edge_analytics = EdgeAnalytics()
        self.running = False
        
        # Edge-specific configuration
        self.local_processing_enabled = os.getenv('LOCAL_PROCESSING_ENABLED', 'true').lower() == 'true'
        self.alert_thresholds = {
            'cpu_threshold': float(os.getenv('CPU_ALERT_THRESHOLD', '80.0')),
            'memory_threshold': float(os.getenv('MEMORY_ALERT_THRESHOLD', '85.0')),
            'temperature_threshold': float(os.getenv('TEMP_ALERT_THRESHOLD', '70.0')),
            'disk_threshold': float(os.getenv('DISK_ALERT_THRESHOLD', '90.0'))
        }
        
        # Data buffers for local analytics
        self.telemetry_buffer = []
        self.max_buffer_size = 100
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    async def connect_to_edge_hub(self):
        """Connect to Azure IoT Edge Hub"""
        try:
            # Create module client from environment (IoT Edge runtime provides this)
            self.module_client = IoTHubModuleClient.create_from_edge_environment()
            await self.module_client.connect()
            self.logger.info("Successfully connected to Azure IoT Edge Hub")
            
            # Set up method handlers
            self.module_client.on_method_request_received = self.method_request_handler
            self.module_client.on_twin_desired_properties_patch_received = self.twin_patch_handler
            
        except ConnectionFailedError as e:
            self.logger.error(f"Failed to connect to IoT Edge Hub: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            raise
    
    async def method_request_handler(self, method_request):
        """Handle direct method calls from Azure IoT Hub/Edge"""
        self.logger.info(f"Received method call: {method_request.name}")
        
        try:
            if method_request.name == "get_edge_analytics":
                response_payload = await self.edge_analytics.get_comprehensive_analytics(
                    self.telemetry_buffer
                )
                response_status = 200
                
            elif method_request.name == "configure_alerts":
                if method_request.payload:
                    self.alert_thresholds.update(method_request.payload)
                response_payload = {"result": "Alert thresholds updated", "thresholds": self.alert_thresholds}
                response_status = 200
                
            elif method_request.name == "get_local_data":
                # Return recent local data without sending to cloud
                recent_data = self.telemetry_buffer[-10:] if self.telemetry_buffer else []
                response_payload = {"recent_telemetry": recent_data, "buffer_size": len(self.telemetry_buffer)}
                response_status = 200
                
            else:
                response_payload = {"result": f"Unknown method: {method_request.name}"}
                response_status = 404
                
        except Exception as e:
            self.logger.error(f"Error handling method {method_request.name}: {e}")
            response_payload = {"result": f"Error: {str(e)}"}
            response_status = 500
        
        # Send method response
        from azure.iot.device import MethodResponse
        method_response = MethodResponse.create_from_method_request(
            method_request, response_status, response_payload
        )
        await self.module_client.send_method_response(method_response)
    
    async def twin_patch_handler(self, patch):
        """Handle device twin desired properties updates"""
        self.logger.info(f"Received twin patch: {patch}")
        
        # Handle configuration updates
        if "local_processing_enabled" in patch:
            self.local_processing_enabled = patch["local_processing_enabled"]
        
        if "alert_thresholds" in patch:
            self.alert_thresholds.update(patch["alert_thresholds"])
        
        # Report back to device twin
        reported_properties = {
            "local_processing_enabled": self.local_processing_enabled,
            "alert_thresholds": self.alert_thresholds,
            "buffer_size": len(self.telemetry_buffer),
            "last_update_check": datetime.utcnow().isoformat()
        }
        
        await self.module_client.patch_twin_reported_properties(reported_properties)
    
    async def send_telemetry(self):
        """Enhanced telemetry with local processing"""
        while self.running:
            try:
                # Collect telemetry data
                telemetry_data = await self.telemetry_sender.collect_telemetry()
                
                # Add to local buffer for analytics
                if self.local_processing_enabled:
                    self.telemetry_buffer.append(telemetry_data)
                    if len(self.telemetry_buffer) > self.max_buffer_size:
                        self.telemetry_buffer.pop(0)  # Remove oldest entry
                
                # Add edge processing metadata
                telemetry_data['edge_processed'] = True
                telemetry_data['buffer_size'] = len(self.telemetry_buffer)
                
                # Send to IoT Hub
                message = Message(json.dumps(telemetry_data))
                message.content_encoding = "utf-8"
                message.content_type = "application/json"
                message.custom_properties["message-source"] = "jetson-edge-module"
                
                await self.module_client.send_message_to_output(message, "telemetry")
                self.logger.debug(f"Sent telemetry with edge processing")
                
            except Exception as e:
                self.logger.error(f"Error sending telemetry: {e}")
            
            await asyncio.sleep(self.telemetry_sender.interval)
    
    async def run(self):
        """Main application loop"""
        self.logger.info("Starting Azure IoT Edge Module for Jetson Nano")
        
        try:
            await self.connect_to_edge_hub()
            self.running = True
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.send_telemetry())
            ]
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            self.logger.info("Edge module interrupted by user")
        except Exception as e:
            self.logger.error(f"Edge module error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.module_client:
            await self.module_client.disconnect()
        self.logger.info("Edge module cleanup completed")


if __name__ == "__main__":
    asyncio.run(AzureIoTEdgeModule().run()) 