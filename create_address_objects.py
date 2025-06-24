import csv
import requests
import urllib3
from getpass import getpass
import configparser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = configparser.ConfigParser()
config.read("panw.cfg")

PANORAMA_HOST = config.get("PANW", "panorama_host")
CSV_FILE = config.get("PANW", "address_csv")
API_KEY = getpass("Enter PAN-OS API Key: ")

def create_address_object(row):
    name = row["name"]
    ip_netmask = row["ip-netmask"]
    description = row["description"]
    location = row["location"] or "shared"
    object_type = row["type"] or "ip-netmask"
    tags = row["tag"].split(",") if row["tag"] else []

    xpath = "/config/shared/address" if location.lower() == "shared" else (
        f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{location}']/address"
    )

    xml_entry = f"<entry name='{name}'>"
    if ip_netmask:
        xml_entry += f"<ip-netmask>{ip_netmask}</ip-netmask>"
    if description:
        xml_entry += f"<description>{description}</description>"
    if tags:
        xml_entry += "<tag>" + "".join([f"<member>{tag}</member>" for tag in tags]) + "</tag>"
    xml_entry += "</entry>"

    params = {
        "type": "config",
        "action": "set",
        "xpath": xpath,
        "element": xml_entry,
        "key": API_KEY
    }

    print(f"[*] Creating address object '{name}' in {location}")
    response = requests.get(f"{PANORAMA_HOST}/api/", params=params, verify=False)
    if "<result>success</result>" in response.text:
        print(f"[✓] Created address object: {name}")
    else:
        print(f"[!] Failed to create '{name}': {response.text}")

def main():
    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            create_address_object(row)

if __name__ == "__main__":
    main()