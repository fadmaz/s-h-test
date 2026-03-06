import asyncio
import json
import base64
import threading
import time
import os
import logging
import warnings
import paho.mqtt.client as mqtt
from datetime import datetime
from scapy.all import ARP, Ether, sendp, getmacbyip

# Silence warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# === CONFIG ===
INVERTER_IP = os.getenv('INVERTER_IP', '192.168.1.139')
ROUTER_IP = os.getenv('ROUTER_IP', '192.168.1.1')
CLOUD_IP = os.getenv('TARGET_HOST', '8.212.18.157')
CLOUD_PORT = 1883
LISTEN_PORT = 18899

# --- HA MQTT ---
HA_BROKER = os.getenv('MQTT_HOST', 'core-mosquitto')
HA_PORT = int(os.getenv('MQTT_PORT', 1883))
HA_USER = os.getenv('MQTT_USER', '')
HA_PASS = os.getenv('MQTT_PASSWORD', '')
DEVICE_ID = "powmr_rwb1"
STATE_TOPIC = f"powmr/{DEVICE_ID}/state"

ha_client = mqtt.Client()
if HA_USER and HA_PASS:
    ha_client.username_pw_set(HA_USER, HA_PASS)

def connect_ha_mqtt():
    try:
        ha_client.connect(HA_BROKER, HA_PORT, 60)
        ha_client.loop_start()
        print("[HA MQTT] Connected to Mosquitto")
        publish_discovery()
    except Exception as e: print(f"[HA MQTT ERROR] {e}")

def publish_discovery():
    sensors = {
        "grid_v": ["Grid Voltage", "V", "voltage", "mdi:transmission-tower"],
        "grid_hz": ["Grid Frequency", "Hz", "frequency", "mdi:current-ac"],
        "out_v": ["Output Voltage", "V", "voltage", "mdi:power-plug"],
        "out_hz": ["Output Frequency", "Hz", "frequency", "mdi:current-ac"],
        "load_w": ["Active Load", "W", "power", "mdi:home-lightning-bolt"],
        "apparent_va": ["Apparent Load", "VA", "apparent_power", "mdi:flash"],
        "load_pct": ["Load Percentage", "%", "power_factor", "mdi:gauge"],
        "bat_v": ["Battery Voltage", "V", "voltage", "mdi:battery"],
        "bat_cap": ["Battery Capacity", "%", "battery", "mdi:battery-high"],
        "dischg_current": ["Battery Discharge Current", "A", "current", "mdi:battery-minus"],
        "bat_temp": ["Inverter Temperature", "°C", "temperature", "mdi:thermometer"],
        "pv_w": ["PV Power", "W", "power", "mdi:solar-power"],
        "pv_v": ["PV Voltage", "V", "voltage", "mdi:solar-panel"],
        "max_chg": ["Max Charge Current", "A", "current", "mdi:current-dc"],
        "util_chg": ["Utility Charge Current", "A", "current", "mdi:current-dc"],
        "bulk_v": ["Bulk Charging Voltage", "V", "voltage", "mdi:battery-charging-high"],
        "float_v": ["Float Charging Voltage", "V", "voltage", "mdi:battery-charging-medium"],
        "cut_v": ["Low Battery Cut-off", "V", "voltage", "mdi:battery-off-outline"]
    }
    for key, data in sensors.items():
        topic = f"homeassistant/sensor/{DEVICE_ID}/{key}/config"
        payload = {
            "name": f"PowMr {data[0]}", "state_topic": STATE_TOPIC, 
            "value_template": f"{{{{ value_json.{key} }}}}", "unit_of_measurement": data[1], 
            "device_class": data[2], "icon": data[3], "unique_id": f"{DEVICE_ID}_{key}", 
            "device": {"identifiers": [DEVICE_ID], "name": "PowMr 6.2kW Inverter", "manufacturer": "PowMr"}
        }
        ha_client.publish(topic, json.dumps(payload), retain=True)

class SolarParser:
    @staticmethod
    def parse_payload(payload_bytes):
        try:
            idx = payload_bytes.find(b'{"b":')
            if idx == -1: return
            raw_json = json.loads(payload_bytes[idx:].decode('utf-8', errors='ignore'))
            state = {}
            if "b" in raw_json and "ct" in raw_json["b"]:
                blocks = {item["cn"]: base64.b64decode(item["co"]) for item in raw_json["b"]["ct"]}
                if "PS4Z" in blocks:
                    r = blocks["PS4Z"]
                    if len(r) >= 44:
                        state["grid_v"] = int.from_bytes(r[5:7], 'little') / 10.0
                        state["bat_v"] = int.from_bytes(r[13:15], 'little') / 10.0
                        state["load_w"] = int.from_bytes(r[27:29], 'little')
                        state["pv_v"] = int.from_bytes(r[39:41], 'little') / 10.0
                        pv_w = int.from_bytes(r[41:43], 'little')
                        state["pv_w"] = pv_w if pv_w < 6500 else 0
                        state["grid_hz"] = int.from_bytes(r[7:9], 'little') / 10.0
                        state["bat_cap"] = int.from_bytes(r[15:17], 'little')
                        state["out_v"] = int.from_bytes(r[21:23], 'little') / 10.0
                        state["out_hz"] = int.from_bytes(r[23:25], 'little') / 10.0
                        state["apparent_va"] = int.from_bytes(r[25:27], 'little')
                        state["load_pct"] = int.from_bytes(r[29:31], 'little')
                        state["dischg_current"] = round((state["load_w"] / state["bat_v"]), 1) if (state["grid_v"] < 100 and state["load_w"] > 0) else 0
                if "Sgx0" in blocks:
                    r = blocks["Sgx0"]
                    if len(r) >= 42:
                        state["max_chg"] = int.from_bytes(r[13:15], 'little')
                        state["util_chg"] = int.from_bytes(r[17:19], 'little')
                        state["float_v"] = int.from_bytes(r[21:23], 'little') / 10.0
                        state["bulk_v"] = int.from_bytes(r[23:25], 'little') / 10.0
                        state["cut_v"] = int.from_bytes(r[27:29], 'little') / 10.0
                        state["bat_temp"] = r[41]
            if state:
                ha_client.publish(STATE_TOPIC, json.dumps(state))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ➡️ Data duplicated to HA.")
        except: pass

# --- PROXY ---
async def forward_stream(reader, writer, is_inverter=False):
    try:
        while True:
            data = await reader.read(8192)
            if not data: break
            if is_inverter: SolarParser.parse_payload(data)
            writer.write(data)
            await writer.drain()
    except Exception: pass
    finally: writer.close()

async def handle_client(inverter_reader, inverter_writer):
    peer = inverter_writer.get_extra_info('peername')
    print(f"[PROXY] Connection from {peer}. Establishing bridge to Cloud...")
    try:
        cloud_reader, cloud_writer = await asyncio.open_connection(CLOUD_IP, CLOUD_PORT)
        print("[PROXY] Bridge established. Forwarding traffic.")
        await asyncio.gather(
            forward_stream(inverter_reader, cloud_writer, is_inverter=True),
            forward_stream(cloud_reader, inverter_writer, is_inverter=False)
        )
    except Exception as e: print(f"[PROXY ERROR] {e}")
    finally: inverter_writer.close()

# --- ARP SPOOFER ---
class ArpSpoofer:
    def run(self):
        t_mac = getmacbyip(INVERTER_IP)
        g_mac = getmacbyip(ROUTER_IP)
        if not t_mac or not g_mac:
            print(f"[ARP ERROR] Could not find MAC for {INVERTER_IP} or {ROUTER_IP}")
            return
        print(f"[ARP] Interception ACTIVE: {INVERTER_IP} <-> {ROUTER_IP}")
        while True:
            sendp(Ether(dst=t_mac)/ARP(op=2, pdst=INVERTER_IP, psrc=ROUTER_IP, hwdst=t_mac), verbose=False)
            sendp(Ether(dst=g_mac)/ARP(op=2, pdst=ROUTER_IP, psrc=INVERTER_IP, hwdst=g_mac), verbose=False)
            time.sleep(2)

# --- MAIN ---
async def main():
    connect_ha_mqtt()
    threading.Thread(target=ArpSpoofer().run, daemon=True).start()
    server = await asyncio.start_server(handle_client, '0.0.0.0', LISTEN_PORT)
    print(f"--- PowMr Autonomous Proxy 1.7.0 ACTIVE ---")
    async with server: await server.serve_forever()

if __name__ == "__main__": asyncio.run(main())
