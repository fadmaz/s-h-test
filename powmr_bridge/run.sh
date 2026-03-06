#!/usr/bin/with-contenv bashio

echo "--- PowMr Bridge 1.5.0 UNIVERSAL START ---"
echo "Mode: Passive Sniffing + ARP Spoofing"

# Очищуємо всі правила iptables, які ми могли створити раніше
iptables -t nat -F PREROUTING 2>/dev/null

# Експорт налаштувань для Python
export MQTT_HOST=$(bashio::config 'mqtt_host' 'core-mosquitto')
export MQTT_PORT=$(bashio::config 'mqtt_port' '1883')
export MQTT_USER=$(bashio::config 'mqtt_user' '')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' '')
export TARGET_HOST=$(bashio::config 'TARGET_HOST' '8.212.18.157')
export INVERTER_IP=$(bashio::config 'INVERTER_IP' '')
export ROUTER_IP=$(bashio::config 'ROUTER_IP' '')
export INVERTER_MAC=$(bashio::config 'INVERTER_MAC' '')
export ROUTER_MAC=$(bashio::config 'ROUTER_MAC' '')

echo "Launching Universal Python Bridge..."
python3 -u /app/powmr_bridge.py
