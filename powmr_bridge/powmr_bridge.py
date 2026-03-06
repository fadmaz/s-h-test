import asyncio
import json
import base64
import threading
import time
import warnings
import logging
import os
import paho.mqtt.client as mqtt
from datetime import datetime
from scapy.all import ARP, Ether, sendp, getmacbyip

# Silence warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# --- CONFIG ---
TARGET_HOST = os.getenv('TARGET_HOST', '8.212.18.157')
HA_BROKER = os.getenv('MQTT_HOST', 'core-mosquitto') 
HA_PORT = int(os.getenv('MQTT_PORT', 1883))
HA_USER = os.getenv('MQTT_USER', '')
HA_PASS = os.getenv('MQTT_PASSWORD', '')

INVERTER_IP = os.getenv('INVERTER_IP', '')
ROUTER_IP = os.getenv('ROUTER_IP', '')
LISTEN_PORT = 18899

DEVICE_ID = "powmr_rwb1"
STATE_TOPIC = f"powmr/{DEVICE_ID}/state"

# --- HEARTBEAT (Ping) ---
def heartbeat():
    while True:
        try:
            import subprocess
            subprocess.call(["ping", "-c", "1", "-W", "1", INVERTER_IP], stdout=subprocess.DEVNULL)
        except: pass
        time.sleep(30)

# --- MQTT ---
ha_client = mqtt.Client()
if HA_USER and HA_PASS: ha_client.username_pw_set(HA_USER, HA_PASS)

def connect_ha_mqtt():
    try:
        ha_client.connect(HA_BROKER, HA_PORT, 60)
        ha_client.loop_start()
        print(f"[HA MQTT] Connected to {HA_BROKER}")
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
            "name": f"PowMr {data[0]}",
            "state_topic": STATE_TOPIC,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "unit_of_measurement": data[1],
            "device_class": data[2],
            "icon": data[3],
            "unique_id": f"{DEVICE_ID}_{key}",
            "device": {"identifiers": [DEVICE_ID], "name": "PowMr 6.2kW Inverter", "manufacturer": "PowMr", "model": "RWB1 6200W"}
        }
        ha_client.publish(topic, json.dumps(payload), retain=True)

# --- PARSER ---
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
                        state["grid_hz"] = int.from_bytes(r[7:9], 'little') / 10.0
                        state["bat_v"] = int.from_bytes(r[13:15], 'little') / 10.0
                        state["bat_cap"] = int.from_bytes(r[15:17], 'little')
                        state["out_v"] = int.from_bytes(r[21:23], 'little') / 10.0
                        state["out_hz"] = int.from_bytes(r[23:25], 'little') / 10.0
                        state["apparent_va"] = int.from_bytes(r[25:27], 'little')
                        state["load_w"] = int.from_bytes(r[27:29], 'little')
                        state["load_pct"] = int.from_bytes(r[29:31], 'little')
                        state["pv_v"] = int.from_bytes(r[39:41], 'little') / 10.0
                        pv_w = int.from_bytes(r[41:43], 'little')
                        state["pv_w"] = pv_w if pv_w < 6500 else 0
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
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ➡️ Data captured and sent to HA.")
        except: pass

# --- PROXY ---
async def forward_stream(reader, writer, label, is_inverter=False):
    try:
        while True:
            data = await reader.read(8192)
            if not data: break
            if is_inverter: SolarParser.parse_payload(data)
            writer.write(data)
            await writer.drain()
    except Exception: pass
    finally: writer.close()

async def client_connected(ir, iw):
    peer = iw.get_extra_info('peername')
    print(f"[PROXY] Connection from {peer} (Expected Inverter: {INVERTER_IP})")
    try:
        cr, cw = await asyncio.open_connection(TARGET_HOST, 1883)
        print(f"[PROXY] Successfully connected to Cloud {TARGET_HOST}")
        await asyncio.gather(
            forward_stream(ir, cw, "Inv->Cloud", is_inverter=True),
            forward_stream(cr, iw, "Cloud->Inv", is_inverter=False)
        )
    except Exception as e: print(f"[PROXY ERROR] {e}")
    finally: iw.close()

# --- ARP SPOOFER ---
class ArpSpoofer:
    def __init__(self, target_ip, gateway_ip):
        self.target_ip, self.gateway_ip = target_ip, gateway_ip
        self.running = False

    def run(self):
        t_mac = getmacbyip(self.target_ip)
        g_mac = getmacbyip(self.gateway_ip)
        if not t_mac or not g_mac: return
        self.running = True
        print(f"[ARP] Spoofing ACTIVE: {self.target_ip} <-> {self.gateway_ip}")
        while self.running:
            sendp(Ether(dst=t_mac)/ARP(op=2, pdst=self.target_ip, psrc=self.gateway_ip, hwdst=t_mac), verbose=False)
            sendp(Ether(dst=g_mac)/ARP(op=2, pdst=self.gateway_ip, psrc=self.target_ip, hwdst=g_mac), verbose=False)
            time.sleep(2)

# --- MAIN ---
async def main():
    if INVERTER_IP and ROUTER_IP:
        threading.Thread(target=ArpSpoofer(INVERTER_IP, ROUTER_IP).run, daemon=True).start()
        threading.Thread(target=heartbeat, daemon=True).start()
    
    connect_ha_mqtt()
    
    proxy_server = await asyncio.start_server(client_connected, '0.0.0.0', LISTEN_PORT)
    print(f"--- PowMr Bridge 1.6.2 ACTIVE (Port {LISTEN_PORT}) ---")
    async with proxy_server: await proxy_server.serve_forever()

if __name__ == "__main__": asyncio.run(main())
