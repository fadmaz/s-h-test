#!/usr/bin/with-contenv bashio

echo "--- PowMr Bridge 1.7.0 (Autonomous Proxy) ---"

# 1. Експорт налаштувань
export MQTT_HOST=$(bashio::config 'mqtt_host' 'core-mosquitto')
export MQTT_PORT=$(bashio::config 'mqtt_port' '1883')
export MQTT_USER=$(bashio::config 'mqtt_user' '')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' '')
export TARGET_HOST=$(bashio::config 'TARGET_HOST' '8.212.18.157')
export INVERTER_IP=$(bashio::config 'INVERTER_IP' '192.168.1.139')
export ROUTER_IP=$(bashio::config 'ROUTER_IP' '192.168.1.1')

# 2. Очищення і налаштування REDIRECT для інвертора
echo "Cleaning up network rules for $INVERTER_IP..."
iptables -t nat -F PREROUTING 2>/dev/null
iptables -t nat -A PREROUTING -s $INVERTER_IP -p tcp --dport 1883 -j REDIRECT --to-port 18899 || echo "WARNING: iptables failed"

echo "Launching Autonomous Python Bridge..."
python3 -u /app/powmr_bridge.py
