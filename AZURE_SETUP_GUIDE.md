# Azure Portal & Jetson Nano Setup Guide

This guide walks you through setting up Azure IoT Hub/Edge and deploying to Jetson Nano.

## Part 1: Azure Portal Setup

### Step 1: Create Azure IoT Hub

1. **Go to Azure Portal** (https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"IoT Hub"** and select it
4. Click **"Create"**
5. Fill out the form:
   - **Subscription**: Choose your subscription
   - **Resource Group**: Create new (e.g., "iot-jetson-rg")
   - **IoT Hub Name**: Choose unique name (e.g., "jetson-iot-hub-001")
   - **Region**: Choose closest region
   - **Tier**: Choose "Standard S1" (Free tier works for testing)
6. Click **"Review + Create"** → **"Create"**
7. Wait for deployment (3-5 minutes)

### Step 2: Register IoT Device (for Direct IoT Hub)

1. **Navigate to your IoT Hub**
2. In left menu, click **"Devices"** 
3. Click **"Add Device"**
4. Fill out:
   - **Device ID**: `jetson-nano-001` (or your preferred name)
   - **Authentication type**: `Symmetric key`
   - **Auto-generate keys**: ✅ Checked
   - **Connect this device to IoT Hub**: ✅ Enabled
5. Click **"Save"**
6. **IMPORTANT**: Click on your device and copy the **"Primary connection string"**
   - Save this - you'll need it for the `.env` file

### Step 3: Register IoT Edge Device (for IoT Edge)

1. **In your IoT Hub**, go to **"IoT Edge"** in left menu
2. Click **"Add an IoT Edge device"**
3. Fill out:
   - **Device ID**: `jetson-edge-001`
   - **Authentication type**: `Symmetric key`
   - **Auto-generate keys**: ✅ Checked
4. Click **"Save"**
5. **IMPORTANT**: Click on your Edge device and copy the **"Primary connection string"**
   - This is different from the regular device connection string

### Step 4: Create Container Registry (for IoT Edge)

1. **Go back to Azure Portal home**
2. Click **"Create a resource"**
3. Search for **"Container Registry"** and select it
4. Fill out:
   - **Registry name**: Choose unique name (e.g., "jetsonregistry001")
   - **Resource group**: Use same as IoT Hub
   - **Location**: Same as IoT Hub
   - **SKU**: Basic (for testing)
   - **Admin user**: ✅ Enable
5. Click **"Review + Create"** → **"Create"**
6. **After creation**, go to registry → **"Access keys"**
7. **Copy**:
   - Login server (e.g., jetsonregistry001.azurecr.io)
   - Username
   - Password

## Part 2: Jetson Nano Setup

### Step 1: Prepare Jetson Nano

1. **Flash SD card** with JetPack (if not done)
2. **Boot Jetson Nano** and complete initial setup
3. **Update system**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Install required packages**:
   ```bash
   # Install Docker (if not installed)
   sudo apt install -y docker.io
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   
   # Install Python and Git
   sudo apt install -y python3 python3-pip git curl
   
   # Install additional tools
   sudo apt install -y nano htop
   ```

5. **Reboot** to apply Docker group changes:
   ```bash
   sudo reboot
   ```

### Step 2: Copy Code to Jetson Nano

1. **Clone/copy your project** to Jetson Nano:
   ```bash
   # Option 1: If using Git
   git clone https://github.com/your-username/azure-iot-jetson.git
   cd azure-iot-jetson
   
   # Option 2: If copying files manually
   # Use SCP, SFTP, or USB to copy project folder
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Install Jetson-specific packages** (optional but recommended):
   ```bash
   sudo -H pip3 install jetson-stats
   ```

### Step 3: Configure Environment

1. **Create environment file**:
   ```bash
   cp env.example .env
   nano .env
   ```

2. **Edit `.env` file** with your Azure details:
   ```bash
   # For Direct IoT Hub (use device connection string from Step 2)
   AZURE_IOT_CONNECTION_STRING=HostName=jetson-iot-hub-001.azure-devices.net;DeviceId=jetson-nano-001;SharedAccessKey=your-device-key
   
   # Device Configuration
   DEVICE_ID=jetson-nano-001
   DEVICE_TYPE=jetson-nano
   
   # Telemetry Configuration
   TELEMETRY_INTERVAL=30
   LOG_LEVEL=INFO
   
   # For GitHub updates (optional)
   GITHUB_REPO=your-username/azure-iot-jetson
   AUTO_UPDATE_ENABLED=false
   ```

### Step 4: Test Direct IoT Hub Connection

1. **Run the basic application**:
   ```bash
   python3 main.py
   ```

2. **Verify in Azure Portal**:
   - Go to IoT Hub → Overview
   - You should see "Device-to-cloud messages" increasing
   - Go to IoT Hub → Devices → your device → Message to device
   - You should see "Last activity time" updating

3. **Test direct method call**:
   - In Azure Portal: IoT Hub → Devices → your device
   - Click "Direct Method"
   - Method name: `get_device_info`
   - Payload: `{}`
   - Click "Invoke Method"
   - You should get device information back

## Part 3: IoT Edge Setup (Advanced)

### Step 1: Install IoT Edge Runtime on Jetson

1. **Install IoT Edge runtime**:
   ```bash
   # Add Microsoft repository
   curl https://packages.microsoft.com/config/ubuntu/18.04/multiarch/prod.list > ./microsoft-prod.list
   sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
   curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
   sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
   
   # Install IoT Edge
   sudo apt update
   sudo apt install -y aziot-edge
   ```

2. **Configure IoT Edge** with your connection string:
   ```bash
   sudo nano /etc/aziot/config.toml
   ```
   
   Add this configuration:
   ```toml
   [provisioning]
   source = "manual"
   connection_string = "HostName=jetson-iot-hub-001.azure-devices.net;DeviceId=jetson-edge-001;SharedAccessKey=your-edge-device-key"
   
   [agent]
   name = "edgeAgent"
   type = "docker"
   
   [agent.config]
   image = "mcr.microsoft.com/azureiotedge-agent:1.4"
   
   [connect]
   workload_uri = "unix:///var/run/iotedge/workload.sock"
   management_uri = "unix:///var/run/iotedge/mgmt.sock"
   ```

3. **Start IoT Edge**:
   ```bash
   sudo systemctl enable aziot-edge
   sudo systemctl start aziot-edge
   
   # Check status
   sudo systemctl status aziot-edge
   sudo iotedge check
   ```

### Step 2: Build and Deploy IoT Edge Module

1. **Install Azure CLI** (on your development machine):
   ```bash
   # On Windows/Mac/Linux development machine
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   az login
   az extension add --name azure-iot
   ```

2. **Build container image**:
   ```bash
   # On your development machine, in project folder
   docker build -f Dockerfile.arm64v8 -t jetsonregistry001.azurecr.io/jetsonmonitor:1.0.0-arm64v8 .
   ```

3. **Push to container registry**:
   ```bash
   # Login to your container registry
   docker login jetsonregistry001.azurecr.io -u <username> -p <password>
   
   # Push image
   docker push jetsonregistry001.azurecr.io/jetsonmonitor:1.0.0-arm64v8
   ```

4. **Deploy to IoT Edge device**:
   ```bash
   # Edit deployment.template.json to use your container registry
   # Then deploy using Azure CLI
   az iot edge set-modules --device-id jetson-edge-001 --hub-name jetson-iot-hub-001 --content deployment.template.json
   ```

## Part 4: Verification & Testing

### Direct IoT Hub Testing

1. **Check telemetry in Azure Portal**:
   - IoT Hub → Overview → Usage tiles
   - Should see message count increasing

2. **Test direct methods**:
   - IoT Hub → Devices → your device → Direct Method
   - Try: `get_device_info`, `reboot` (careful!)

3. **Check device twin**:
   - IoT Hub → Devices → your device → Device Twin
   - Should see reported properties

### IoT Edge Testing

1. **Check edge modules**:
   ```bash
   # On Jetson Nano
   sudo iotedge list
   sudo iotedge logs JetsonMonitorModule
   ```

2. **Verify in Azure Portal**:
   - IoT Hub → IoT Edge → your edge device
   - Should show modules running
   - Check telemetry in cloud

## Part 5: Troubleshooting

### Common Issues

#### "Connection refused" errors:
```bash
# Check connection string format
# Ensure no extra spaces/characters
# Verify device exists in Azure Portal
```

#### "Module not starting" in IoT Edge:
```bash
# Check logs
sudo iotedge logs JetsonMonitorModule

# Check image architecture
docker images | grep jetsonmonitor

# Verify container registry credentials
```

#### "Permission denied" errors:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again

# For system access
sudo usermod -aG i2c,gpio,dialout $USER
```

#### Python import errors:
```bash
# Install missing packages
pip3 install -r requirements.txt

# For Jetson-specific packages
sudo -H pip3 install jetson-stats
```

### Getting Help

1. **Check logs**:
   ```bash
   # Application logs
   python3 main.py 2>&1 | tee app.log
   
   # IoT Edge logs
   sudo iotedge logs JetsonMonitorModule
   sudo journalctl -u aziot-edge
   ```

2. **Test network connectivity**:
   ```bash
   ping azure.microsoft.com
   nslookup your-iot-hub.azure-devices.net
   ```

3. **Verify Azure configuration**:
   - Double-check connection strings
   - Ensure devices are enabled in Azure Portal
   - Check IoT Hub pricing tier limits

## Part 6: Production Deployment

### Run as System Service

1. **Create systemd service file**:
   ```bash
   sudo nano /etc/systemd/system/azure-iot-device.service
   ```

2. **Add service configuration**:
   ```ini
   [Unit]
   Description=Azure IoT Jetson Device Application
   After=network.target
   
   [Service]
   Type=simple
   User=jetson
   WorkingDirectory=/home/jetson/azure-iot-jetson
   Environment=PYTHONPATH=/home/jetson/azure-iot-jetson
   ExecStart=/usr/bin/python3 main.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable azure-iot-device.service
   sudo systemctl start azure-iot-device.service
   sudo systemctl status azure-iot-device.service
   ```

### Security Best Practices

1. **Use device certificates** (production):
   - Generate X.509 certificates
   - Configure in Azure IoT Hub
   - Update application configuration

2. **Network security**:
   - Configure firewall rules
   - Use VPN for remote access
   - Monitor network traffic

3. **Regular updates**:
   - Enable automatic security updates
   - Monitor for vulnerabilities
   - Keep Azure SDK updated

## Summary Checklist

### Azure Portal Setup ✅
- [ ] Created IoT Hub
- [ ] Registered device(s)
- [ ] Copied connection string(s)
- [ ] (Optional) Created Container Registry

### Jetson Nano Setup ✅
- [ ] Updated system packages
- [ ] Installed Docker and Python
- [ ] Copied project code
- [ ] Configured .env file
- [ ] Tested basic connectivity

### Testing ✅
- [ ] Direct IoT Hub connection works
- [ ] Telemetry visible in Azure Portal
- [ ] Direct methods respond
- [ ] (Optional) IoT Edge modules running

### Production Ready ✅
- [ ] Running as system service
- [ ] Logs being collected
- [ ] Monitoring configured
- [ ] Backup/recovery plan

**You're now ready to demonstrate a full Azure IoT solution!** 🚀 