#!/bin/bash
# Home Automation Setup for HP Z4 G4 "ebon"

echo "🏠 Setting up Home Automation"
echo "============================="

# Install Home Assistant
echo "🏡 Installing Home Assistant..."
docker run -d --name homeassistant \
  --restart=unless-stopped \
  --privileged \
  --network=host \
  -v ~/homeassistant:/config \
  -v /etc/localtime:/etc/localtime:ro \
  homeassistant/home-assistant:stable

# Install Node-RED for automation flows  
echo "🔴 Installing Node-RED..."
docker run -d --name nodered \
  --restart=unless-stopped \
  -p 1880:1880 \
  -v ~/nodered:/data \
  nodered/node-red

# Install Mosquitto MQTT Broker
echo "📡 Installing MQTT Broker..."
docker run -d --name mosquitto \
  --restart=unless-stopped \
  -p 1883:1883 \
  -p 9001:9001 \
  -v ~/mosquitto/config:/mosquitto/config \
  -v ~/mosquitto/data:/mosquitto/data \
  -v ~/mosquitto/log:/mosquitto/log \
  eclipse-mosquitto

# Install Zigbee2MQTT (if you have Zigbee devices)
echo "📶 Installing Zigbee2MQTT..."
docker run -d --name zigbee2mqtt \
  --restart=unless-stopped \
  -p 8080:8080 \
  -v ~/zigbee2mqtt:/app/data \
  -v /run/udev:/run/udev:ro \
  --device=/dev/ttyUSB0 \
  koenkk/zigbee2mqtt

# Install ESPHome (for ESP32/ESP8266 devices)
echo "⚡ Installing ESPHome..."
docker run -d --name esphome \
  --restart=unless-stopped \
  -p 6052:6052 \
  -v ~/esphome:/config \
  -v /etc/localtime:/etc/localtime:ro \
  --network=host \
  esphome/esphome

echo "✅ Home automation setup complete!"
echo
echo "🌐 Access your services:"
echo "• Home Assistant: http://10.0.0.29:8123"
echo "• Node-RED: http://10.0.0.29:1880"  
echo "• Zigbee2MQTT: http://10.0.0.29:8080"
echo "• ESPHome: http://10.0.0.29:6052"
echo
echo "📋 Next steps:"
echo "1. Setup Home Assistant (create account)"
echo "2. Configure Node-RED flows"
echo "3. Add smart devices (lights, sensors, etc.)"
echo "4. Create automations"