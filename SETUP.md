# Setup Guide for Azure IoT Jetson Nano Application

## Quick Start

This guide will help you set up the Azure IoT application both for development (Windows) and deployment (Jetson Nano).

## Prerequisites Installation

### For Development (Windows)

1. **Install Python 3.8 or higher:**
   - Download from https://www.python.org/downloads/
   - During installation, make sure to check "Add Python to PATH"
   - Verify installation: `python --version`

2. **Install Git:**
   - Download from https://git-scm.com/downloads
   - Choose default settings during installation

### For Jetson Nano Deployment

1. **Flash Jetson Nano SD Card:**
   - Use NVIDIA Jetson Nano Developer Kit SD Card Image
   - Flash using Balena Etcher or similar tool

2. **Initial Jetson Setup:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install required system packages
   sudo apt install -y python3 python3-pip git curl
   
   # Install Jetson Stats (optional but recommended)
   sudo -H pip3 install jetson-stats
   ```

## Project Setup

### 1. Clone Repository

For development:
```bash
git clone https://github.com/your-username/azure-iot-jetson.git
cd azure-iot-jetson
```

For Jetson Nano:
```bash
git clone https://github.com/your-username/azure-iot-jetson.git
cd azure-iot-jetson
```

### 2. Install Python Dependencies

**Windows:**
```bash
pip install -r requirements.txt
```

**Jetson Nano:**
```bash
pip3 install -r requirements.txt
```

### 3. Configure Environment

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your settings:
   ```bash
   # Use your favorite text editor
   nano .env  # or vim .env or code .env
   ```

3. **Required Configuration:**
   - `AZURE_IOT_CONNECTION_STRING`: Get this from Azure IoT Hub device settings
   - `DEVICE_ID`: Unique identifier for your device
   - `GITHUB_REPO`: Your GitHub repository (for auto-updates)

## Azure IoT Hub Setup

### 1. Create Azure IoT Hub

1. Go to Azure Portal (https://portal.azure.com)
2. Create a new resource → Internet of Things → IoT Hub
3. Choose your subscription and resource group
4. Give it a unique name
5. Choose pricing tier (Free tier is fine for testing)

### 2. Register Device

1. In your IoT Hub, go to "Devices" → "Add Device"
2. Enter device ID (e.g., "jetson-nano-001")
3. Choose "Symmetric Key" authentication
4. Click "Save"

### 3. Get Connection String

1. Click on your device in the device list
2. Copy the "Primary connection string"
3. Add this to your `.env` file as `AZURE_IOT_CONNECTION_STRING`

## Testing the Application

### 1. Run Tests (Development)

**Windows:**
```bash
python test_application.py
```

**Jetson Nano:**
```bash
python3 test_application.py
```

### 2. Run Application

**Windows (Development):**
```bash
python main.py
```

**Jetson Nano (Production):**
```bash
python3 main.py
```

## GitHub Setup for Auto-Updates

### 1. Create GitHub Repository

1. Go to GitHub.com
2. Create a new repository (e.g., "azure-iot-jetson")
3. Initialize with README
4. Add this code to the repository

### 2. Configure Auto-Updates

1. Set `AUTO_UPDATE_ENABLED=true` in `.env`
2. Set `GITHUB_REPO=your-username/azure-iot-jetson` in `.env`
3. Optionally create a GitHub token for private repos

### 3. Create Releases

1. Update `version.txt` with new version (e.g., "v1.1.0")
2. Commit and push changes
3. Go to GitHub → Releases → Create new release
4. Tag version should match `version.txt`
5. Publish release

The application will automatically check for updates every hour and apply them.

## Running as a Service (Jetson Nano)

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/azure-iot-device.service
```

Add the following content:
```ini
[Unit]
Description=Azure IoT Jetson Device Application
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/azure-iot-jetson
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable azure-iot-device.service

# Start the service
sudo systemctl start azure-iot-device.service

# Check status
sudo systemctl status azure-iot-device.service
```

## Monitoring

### View Logs
```bash
# Real-time logs
sudo journalctl -u azure-iot-device.service -f

# All logs
sudo journalctl -u azure-iot-device.service
```

### Azure IoT Hub Monitoring

1. Go to Azure Portal → Your IoT Hub
2. Click "Overview" to see device connections and messages
3. Use "Device-to-cloud messages" to see telemetry
4. Use "Cloud-to-device messages" to send commands

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check internet connection
   - Verify Azure IoT connection string
   - Ensure device is registered in IoT Hub

2. **Module Import Errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check Python version: `python --version`

3. **Permission Denied (Jetson)**
   - Add user to required groups: `sudo usermod -a -G i2c,gpio,dialout jetson`
   - Reboot after adding to groups

4. **Update Failed**
   - Check GitHub repository configuration
   - Verify internet connectivity
   - Check logs for detailed error messages

### Getting Help

1. Check application logs
2. Run the test script: `python test_application.py`
3. Verify Azure IoT Hub device status
4. Check GitHub repository settings

## Security Best Practices

1. **Never commit `.env` files** - they contain sensitive information
2. **Use device certificates** in production instead of shared access keys
3. **Regularly update** the application and dependencies
4. **Monitor device access** through Azure IoT Hub logs
5. **Use private GitHub repositories** for sensitive code

## Next Steps

1. Customize telemetry data for your specific use case
2. Add custom direct methods for device control
3. Implement data visualization dashboards
4. Add support for multiple sensor types
5. Integrate with Azure IoT Edge for local processing 