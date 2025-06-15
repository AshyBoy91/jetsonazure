<<<<<<< HEAD
# Azure IoT Edge Application for Jetson Nano

A comprehensive Python application designed to run on NVIDIA Jetson Nano that provides both direct Azure IoT Hub connectivity and Azure IoT Edge capabilities with local processing, telemetry collection, and automatic over-the-air (OTA) update capabilities.

## Features

### **Core Capabilities**
- **Azure IoT Hub Integration**: Direct connection to Azure IoT Hub for telemetry and management
- **Azure IoT Edge Support**: Local processing and analytics at the edge
- **Jetson Nano Monitoring**: Comprehensive system metrics (CPU, memory, disk, GPU, temperature, power)
- **Hybrid Architecture**: Choose between direct IoT Hub or IoT Edge deployment

### **Edge Computing Features**
- **Local Data Processing**: Real-time analytics without cloud dependency
- **Intelligent Alerting**: Configurable thresholds with immediate local response
- **Offline Operation**: Continue processing when cloud connectivity is lost
- **Edge Analytics**: Local trend analysis, anomaly detection, and health scoring

### **Management & Updates**
- **Remote Device Management**: Direct method calls and device twin synchronization
- **Automatic OTA Updates**: Self-updating from GitHub releases with rollback capability
- **Container Support**: Docker-based deployment for IoT Edge modules
- **Comprehensive Logging**: Detailed monitoring and debugging capabilities

## Prerequisites

### Hardware
- NVIDIA Jetson Nano (or compatible device)
- Internet connection (Wi-Fi or Ethernet)

### Software
- Python 3.7 or higher
- pip package manager
- Git (for version control and updates)

### Azure Requirements
- Azure IoT Hub instance
- Device registered in Azure IoT Hub
- Device connection string

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/azure-iot-jetson.git
   cd azure-iot-jetson
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Jetson Nano specific packages (optional but recommended):**
   ```bash
   # For Jetson Nano hardware monitoring
   sudo -H pip install jetson-stats
   ```

4. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your Azure IoT Hub connection string and settings
   ```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Copy `env.example` to `.env` and update the values:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_IOT_CONNECTION_STRING` | Azure IoT Hub device connection string | Required |
| `DEVICE_ID` | Unique device identifier | jetson-nano-001 |
| `DEVICE_TYPE` | Device type identifier | jetson-nano |
| `TELEMETRY_INTERVAL` | Telemetry sending interval (seconds) | 30 |
| `AUTO_UPDATE_ENABLED` | Enable automatic updates | false |
| `GITHUB_REPO` | GitHub repository for updates | your-username/repo-name |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |

### Azure IoT Hub Setup

1. Create an Azure IoT Hub in the Azure portal
2. Register a new device in your IoT Hub
3. Copy the device connection string
4. Set the `AZURE_IOT_CONNECTION_STRING` environment variable

## Usage

### Running the Application

```bash
python main.py
```

The application will:
1. Connect to Azure IoT Hub
2. Start sending telemetry data
3. Listen for direct method calls
4. Check for updates (if enabled)

### Telemetry Data

The application sends the following telemetry data:

- **System Metrics**: CPU usage, memory usage, disk usage
- **Temperature Data**: System temperatures from thermal sensors
- **Network Information**: Network interface details and connectivity status
- **Jetson-Specific Data**: GPU usage, power consumption, fan speed (if available)
- **Application Metrics**: Uptime, configuration status

### Direct Methods

The application supports the following direct methods from Azure IoT Hub:

- `reboot`: Reboot the device
- `update_firmware`: Trigger a firmware update
- `get_device_info`: Get comprehensive device information

Example method call from Azure IoT Hub:
```json
{
  "methodName": "get_device_info",
  "payload": {}
}
```

### Device Twin Properties

The application synchronizes with the following device twin properties:

- `telemetry_interval`: Update telemetry sending interval
- `auto_update_enabled`: Enable/disable automatic updates

## Automatic Updates

The application can automatically update itself from GitHub releases:

1. Set `AUTO_UPDATE_ENABLED=true` in your environment
2. Configure `GITHUB_REPO` with your repository name
3. Optionally set `GITHUB_TOKEN` for private repositories
4. Create releases in your GitHub repository
5. The application will check for updates every hour

### Creating Releases

To create a new release:

1. Update `version.txt` with the new version number
2. Commit and push your changes
3. Create a release in GitHub with a version tag (e.g., `v1.1.0`)
4. The application will automatically download and apply the update

## Development

### Project Structure

```
azure-iot-jetson/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── device_manager.py      # Device-specific operations
├── telemetry_sender.py    # Telemetry collection and sending
├── update_manager.py      # Automatic update functionality
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── version.txt           # Current application version
└── README.md             # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Monitoring and Debugging

### Logs

The application logs to stdout with configurable log levels. To save logs to a file:

```bash
python main.py > app.log 2>&1
```

### System Service

To run as a system service on Jetson Nano, create a systemd service file:

```ini
[Unit]
Description=Azure IoT Jetson Device Application
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/path/to/azure-iot-jetson
Environment=PYTHONPATH=/path/to/azure-iot-jetson
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check your Azure IoT Hub connection string
2. **Permission Denied**: Ensure proper permissions for GPIO access on Jetson Nano
3. **Module Not Found**: Install missing dependencies with pip
4. **Update Failed**: Check GitHub repository configuration and network connectivity

### Support

- Check the logs for detailed error messages
- Verify your Azure IoT Hub configuration
- Ensure all dependencies are installed
- Test network connectivity to Azure services

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Considerations

- Store sensitive information (connection strings, tokens) in environment variables
- Use device certificates instead of shared access keys in production
- Regularly update dependencies and the application
- Monitor device access and usage through Azure IoT Hub

## Next Steps

- Add custom telemetry data specific to your use case
- Implement additional direct methods for device control
- Add data visualization dashboards
- Integrate with Azure IoT Edge for local processing
- Add support for multiple device types 
=======
# jetsonazure
Repo for Jetson Azure IoT Hub IoT Edge
>>>>>>> 2b07e4c5811172d37f939bcadecb94ae30d4a45d
