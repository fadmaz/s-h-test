#!/usr/bin/with-contenv bashio

echo "Initializing PowMr Network Interceptor..."

# Redirect incoming traffic from 1883 to our local port 18899
# This is safe and doesn't require system-wide IP forwarding
iptables -t nat -A PREROUTING -p tcp --dport 1883 -j REDIRECT --to-port 18899 || echo "CRITICAL WARNING: iptables failed! You MUST turn OFF Protection Mode in HA Add-on settings."

# Export HA MQTT settings
export MQTT_HOST=$(bashio::config 'mqtt_host' 'core-mosquitto')
export MQTT_PORT=$(bashio::config 'mqtt_port' '1883')
export MQTT_USER=$(bashio::config 'mqtt_user' '')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' '')

# Export user options
export TARGET_HOST=$(bashio::config 'TARGET_HOST' '8.212.18.157')
export TARGET_PORT=$(bashio::config 'TARGET_PORT' '1883')
export LISTEN_PORT=$(bashio::config 'LISTEN_PORT' '18899')
export INVERTER_IP=$(bashio::config 'INVERTER_IP' '')
export ROUTER_IP=$(bashio::config 'ROUTER_IP' '')
export AUTO_INTERCEPT=$(bashio::config 'AUTO_INTERCEPT' 'true')

echo "Starting PowMr HA Bridge with ARP Spoofing..."
python3 /app/powmr_bridge.py
