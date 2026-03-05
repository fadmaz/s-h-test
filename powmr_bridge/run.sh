#!/usr/bin/with-contenv bashio

echo "--- PowMr Bridge 1.3.0 START ---"

# Експорт налаштувань
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

# 1. Повне очищення
iptables -t nat -F PREROUTING 2>/dev/null

# 2. Встановлення перехоплення (1883, 8883, 8080)
if [ -n "$INVERTER_IP" ]; then
    echo "Redirection active for $INVERTER_IP (1883, 8883, 8080 -> $LISTEN_PORT)"
    iptables -t nat -I PREROUTING 1 -s $INVERTER_IP -p tcp --dport 1883 -j REDIRECT --to-port $LISTEN_PORT
    iptables -t nat -I PREROUTING 2 -s $INVERTER_IP -p tcp --dport 8883 -j REDIRECT --to-port $LISTEN_PORT
    iptables -t nat -I PREROUTING 3 -s $INVERTER_IP -p tcp --dport 8080 -j REDIRECT --to-port $LISTEN_PORT
fi

echo "Launching Python Bridge 1.3.0..."
python3 -u /app/powmr_bridge.py
