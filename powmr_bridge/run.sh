#!/usr/bin/with-contenv bashio

echo "--- PowMr Bridge 1.2.2 Booting ---"

# Експорт всіх параметрів з конфігурації HA
export MQTT_HOST=$(bashio::config 'mqtt_host' 'core-mosquitto')
export MQTT_PORT=$(bashio::config 'mqtt_port' '1883')
export MQTT_USER=$(bashio::config 'mqtt_user' '')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' '')
export TARGET_HOST=$(bashio::config 'TARGET_HOST' '8.212.18.157')
export TARGET_PORT=$(bashio::config 'TARGET_PORT' '1883')
export LISTEN_PORT=$(bashio::config 'LISTEN_PORT' '18899')
export INVERTER_IP=$(bashio::config 'INVERTER_IP' '')
export ROUTER_IP=$(bashio::config 'ROUTER_IP' '')
export INVERTER_MAC=$(bashio::config 'INVERTER_MAC' '')
export ROUTER_MAC=$(bashio::config 'ROUTER_MAC' '')

# Налаштування iptables
echo "Configuring network redirection..."
iptables-legacy -t nat -A PREROUTING -p tcp --dport 1883 -j REDIRECT --to-port $LISTEN_PORT 2>/dev/null || \
iptables -t nat -A PREROUTING -p tcp --dport 1883 -j REDIRECT --to-port $LISTEN_PORT || \
echo "WARNING: iptables failed. Make sure Protection Mode is OFF."

echo "Starting PowMr HA Bridge..."
python3 -u /app/powmr_bridge.py
