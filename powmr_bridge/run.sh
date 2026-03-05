#!/usr/bin/with-contenv bashio

echo "Initializing PowMr Network Interceptor..."

# 1. Soft attempt to enable IP forwarding (ignore read-only errors)
sysctl -w net.ipv4.ip_forward=1 2>/dev/null || echo "IP forwarding skip (Read-only OS, it's OK)"

# 2. Redirect incoming traffic on port 1883 to our local bridge
# If this fails, user likely needs to disable Protection Mode in Add-on settings
iptables -t nat -A PREROUTING -p tcp --dport 1883 -j REDIRECT --to-port 1883 || echo "Warning: iptables failed! Check if Protection Mode is OFF in HA Addon settings."

# Export HA MQTT settings
export MQTT_HOST=$(bashio::config 'mqtt_host' 'core-mosquitto')
export MQTT_PORT=$(bashio::config 'mqtt_port' '1883')
export MQTT_USER=$(bashio::config 'mqtt_user' '')
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' '')

# Export user options
export TARGET_HOST=$(bashio::config 'TARGET_HOST' '8.212.18.157')
export TARGET_PORT=$(bashio::config 'TARGET_PORT' '1883')
export LISTEN_PORT=$(bashio::config 'LISTEN_PORT' '1883')
export INVERTER_IP=$(bashio::config 'INVERTER_IP' '')
export ROUTER_IP=$(bashio::config 'ROUTER_IP' '')
export AUTO_INTERCEPT=$(bashio::config 'AUTO_INTERCEPT' 'true')

echo "Starting PowMr HA Bridge with ARP Spoofing..."
python3 /app/powmr_bridge.py
