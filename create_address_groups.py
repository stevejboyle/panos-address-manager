import csv
import requests
import urllib3
from getpass import getpass
import configparser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = configparser.ConfigParser()
config.read("panw.cfg")

PANORAMA_HOST = config.get("PANW", "panorama_host")
CSV_FILE = config.get("PANW", "address_group_csv")
API_KEY = getpass("Enter PAN-OS API Key: ")

def create_address_group(row):
    name = row["name"]
    members = row["members"].split(",") if row["members"] else []
    dynamic = row["dynamic"]
    description = row["description"]
    location = row["location"] or "shared"
    tags = row["tag"].split(",") if row["tag"] else []

    xpath = "/config/shared/address-group" if location.lower() == "shared" else (
        f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{location}']/address-group"
    )

    xml_entry = f"<entry name='{name}'>"
    if members:
        xml_entry += "<static>" + "".join([f"<member>{m}</member>" for m in members]) + "</static>"
    if dynamic:
        xml_entry += f"<dynamic>{dynamic}</dynamic>"
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

    print(f"[*] Creating address-group '{name}' in {location}")
    response = requests.get(f"{PANORAMA_HOST}/api/", params=params, verify=False)
    if "<result>success</result>" in response.text:
        print(f"[✓] Created address-group: {name}")
    else:
        print(f"[!] Failed to create '{name}': {response.text}")

def main():
    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            create_address_group(row)

if __name__ == "__main__":
    main()