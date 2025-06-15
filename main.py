#!/usr/bin/env python3
"""
Azure IoT Edge Device Application for Jetson Nano
Main entry point for the IoT device application.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Optional

from azure.iot.device import IoTHubDeviceClient, Message
from azure.iot.device.exceptions import ConnectionFailedError, ConnectionDroppedError

from config import Config
from device_manager import DeviceManager
from telemetry_sender import TelemetrySender
from update_manager import UpdateManager


class AzureIoTDevice:
    """Main Azure IoT Device class"""
    
    def __init__(self):
        self.config = Config()
        self.device_client: Optional[IoTHubDeviceClient] = None
        self.device_manager = DeviceManager()
        self.telemetry_sender = TelemetrySender()
        self.update_manager = UpdateManager()
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    async def connect_to_azure(self):
        """Connect to Azure IoT Hub"""
        try:
            self.device_client = IoTHubDeviceClient.create_from_connection_string(
                self.config.connection_string
            )
            await self.device_client.connect()
            self.logger.info("Successfully connected to Azure IoT Hub")
            
            # Set up method handlers
            self.device_client.on_method_request_received = self.method_request_handler
            self.device_client.on_twin_desired_properties_patch_received = self.twin_patch_handler
            
        except ConnectionFailedError as e:
            self.logger.error(f"Failed to connect to Azure IoT Hub: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            raise
    
    async def method_request_handler(self, method_request):
        """Handle direct method calls from Azure IoT Hub"""
        self.logger.info(f"Received method call: {method_request.name}")
        
        try:
            if method_request.name == "reboot":
                response_payload = {"result": "Reboot initiated"}
                response_status = 200
                await self.device_manager.reboot_device()
                
            elif method_request.name == "update_firmware":
                response_payload = await self.update_manager.handle_firmware_update(
                    method_request.payload
                )
                response_status = 200
                
            elif method_request.name == "get_device_info":
                response_payload = await self.device_manager.get_device_info()
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
        await self.device_client.send_method_response(method_response)
    
    async def twin_patch_handler(self, patch):
        """Handle device twin desired properties updates"""
        self.logger.info(f"Received twin patch: {patch}")
        
        # Handle configuration updates
        if "telemetry_interval" in patch:
            self.telemetry_sender.set_interval(patch["telemetry_interval"])
        
        if "auto_update_enabled" in patch:
            self.update_manager.set_auto_update(patch["auto_update_enabled"])
        
        # Report back to device twin
        reported_properties = {
            "telemetry_interval": self.telemetry_sender.interval,
            "auto_update_enabled": self.update_manager.auto_update_enabled,
            "last_update_check": datetime.utcnow().isoformat()
        }
        
        await self.device_client.patch_twin_reported_properties(reported_properties)
    
    async def send_telemetry(self):
        """Send telemetry data to Azure IoT Hub"""
        while self.running:
            try:
                telemetry_data = await self.telemetry_sender.collect_telemetry()
                message = Message(json.dumps(telemetry_data))
                message.content_encoding = "utf-8"
                message.content_type = "application/json"
                
                await self.device_client.send_message(message)
                self.logger.debug(f"Sent telemetry: {telemetry_data}")
                
            except Exception as e:
                self.logger.error(f"Error sending telemetry: {e}")
            
            await asyncio.sleep(self.telemetry_sender.interval)
    
    async def check_for_updates(self):
        """Periodically check for application updates"""
        while self.running:
            try:
                if self.update_manager.auto_update_enabled:
                    await self.update_manager.check_for_updates()
            except Exception as e:
                self.logger.error(f"Error checking for updates: {e}")
            
            # Check every hour
            await asyncio.sleep(3600)
    
    async def run(self):
        """Main application loop"""
        self.logger.info("Starting Azure IoT Device Application")
        
        try:
            await self.connect_to_azure()
            self.running = True
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.send_telemetry()),
                asyncio.create_task(self.check_for_updates())
            ]
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.device_client:
            await self.device_client.disconnect()
        self.logger.info("Application cleanup completed")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received. Cleaning up...")
    sys.exit(0)


async def main():
    """Main function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run the IoT device
    device = AzureIoTDevice()
    await device.run()


if __name__ == "__main__":
    asyncio.run(main()) 