#!/usr/bin/env python3
"""
Test script for Azure IoT Jetson Nano Device Application
Tests individual components without requiring Azure IoT Hub connection
"""

import asyncio
import logging
import os
import sys
import tempfile
from unittest.mock import Mock, patch, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    # Test with minimal environment
    with patch.dict(os.environ, {
        'AZURE_IOT_CONNECTION_STRING': 'HostName=test.azure-devices.net;DeviceId=test;SharedAccessKey=testkey'
    }):
        try:
            from config import Config
            config = Config()
            
            assert config.connection_string is not None
            assert config.device_id == 'jetson-nano-001'  # default value
            assert config.telemetry_interval == 30  # default value
            
            logger.info("✓ Configuration test passed")
            return True
        except Exception as e:
            logger.error(f"✗ Configuration test failed: {e}")
            return False

def test_device_manager():
    """Test device manager functionality"""
    logger.info("Testing device manager...")
    
    try:
        from device_manager import DeviceManager
        
        device_manager = DeviceManager()
        
        # Test basic functionality
        metrics = device_manager.get_system_metrics()
        assert 'timestamp' in metrics
        
        logger.info("✓ Device manager test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Device manager test failed: {e}")
        return False

async def test_telemetry_sender():
    """Test telemetry sender functionality"""
    logger.info("Testing telemetry sender...")
    
    try:
        # Mock the Config to avoid Azure connection string requirement
        with patch.dict(os.environ, {
            'AZURE_IOT_CONNECTION_STRING': 'HostName=test.azure-devices.net;DeviceId=test;SharedAccessKey=testkey'
        }):
            from telemetry_sender import TelemetrySender
            
            telemetry_sender = TelemetrySender()
            
            # Test telemetry collection
            telemetry = await telemetry_sender.collect_telemetry()
            
            assert 'timestamp' in telemetry
            assert 'device_id' in telemetry
            assert 'message_type' in telemetry
            assert telemetry['message_type'] == 'telemetry'
            
            # Test formatting
            formatted = telemetry_sender.format_telemetry_for_display(telemetry)
            assert isinstance(formatted, str)
            assert len(formatted) > 0
            
            logger.info("✓ Telemetry sender test passed")
            return True
    except Exception as e:
        logger.error(f"✗ Telemetry sender test failed: {e}")
        return False

def test_update_manager():
    """Test update manager functionality"""
    logger.info("Testing update manager...")
    
    try:
        # Mock the Config to avoid Azure connection string requirement
        with patch.dict(os.environ, {
            'AZURE_IOT_CONNECTION_STRING': 'HostName=test.azure-devices.net;DeviceId=test;SharedAccessKey=testkey'
        }):
            from update_manager import UpdateManager
            
            update_manager = UpdateManager()
            
            # Test basic functionality
            status = update_manager.get_update_status()
            assert 'current_version' in status
            assert 'auto_update_enabled' in status
            
            # Test auto-update toggle
            update_manager.set_auto_update(True)
            assert update_manager.auto_update_enabled == True
            
            update_manager.set_auto_update(False)
            assert update_manager.auto_update_enabled == False
            
            logger.info("✓ Update manager test passed")
            return True
    except Exception as e:
        logger.error(f"✗ Update manager test failed: {e}")
        return False

async def test_main_application():
    """Test main application initialization"""
    logger.info("Testing main application...")
    
    try:
        # Mock Azure IoT Hub connection
        with patch.dict(os.environ, {
            'AZURE_IOT_CONNECTION_STRING': 'HostName=test.azure-devices.net;DeviceId=test;SharedAccessKey=testkey'
        }):
            with patch('azure.iot.device.IoTHubDeviceClient.create_from_connection_string'):
                from main import AzureIoTDevice
                
                device = AzureIoTDevice()
                
                # Test initialization
                assert device.config is not None
                assert device.device_manager is not None
                assert device.telemetry_sender is not None
                assert device.update_manager is not None
                
                logger.info("✓ Main application test passed")
                return True
    except Exception as e:
        logger.error(f"✗ Main application test failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available"""
    logger.info("Testing dependencies...")
    
    required_modules = [
        'asyncio',
        'json',
        'logging',
        'os',
        'platform',
        'subprocess',
        'tempfile',
        'pathlib',
        'datetime',
        'typing',
        'hashlib',
        'zipfile',
        'shutil'
    ]
    
    try:
        for module in required_modules:
            __import__(module)
        
        logger.info("✓ All core dependencies available")
        
        # Test optional dependencies
        optional_modules = {
            'psutil': 'System monitoring (recommended)',
            'aiohttp': 'HTTP client for updates (required)',
            'azure.iot.device': 'Azure IoT Device SDK (required)'
        }
        
        for module, description in optional_modules.items():
            try:
                __import__(module)
                logger.info(f"✓ {module} available - {description}")
            except ImportError:
                logger.warning(f"⚠ {module} not available - {description}")
        
        return True
    except ImportError as e:
        logger.error(f"✗ Dependency test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    logger.info("Starting comprehensive application tests...")
    logger.info("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_config),
        ("Device Manager", test_device_manager),
        ("Telemetry Sender", test_telemetry_sender),
        ("Update Manager", test_update_manager),
        ("Main Application", test_main_application)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} Test ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Application is ready to run.")
    else:
        logger.warning(f"⚠ {total - passed} tests failed. Check the logs above.")
    
    return passed == total

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Azure IoT Jetson Nano Application Test Suite")
        print()
        print("This script tests the application components without requiring")
        print("a real Azure IoT Hub connection.")
        print()
        print("Usage: python test_application.py")
        return
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Ready to run the application!")
        print("Next steps:")
        print("1. Configure your Azure IoT Hub connection string in .env")
        print("2. Run: python main.py")
    else:
        print("\n❌ Some tests failed. Please check the configuration and dependencies.")
        sys.exit(1)

if __name__ == "__main__":
    main() 