import csv
import requests
import urllib3
from getpass import getpass
from datetime import datetime
import configparser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = configparser.ConfigParser()
config.read("panw.cfg")

PANORAMA_HOST = config.get("PANW", "panorama_host")
CSV_FILE = config.get("PANW", "address_group_csv")
API_KEY = getpass("Enter PAN-OS API Key: ")

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_FILE = f"{timestamp}-address-group.csv"

out_fields = ["name", "members", "dynamic", "description", "location", "tag"]
with open(OUTPUT_FILE, mode='w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=out_fields)
    writer.writeheader()

def export_then_delete_address_group(name, device_group=None):
    is_shared = not device_group or device_group.strip().lower() == "shared"

    if is_shared:
        xpath = f"/config/shared/address-group/entry[@name='{name}']"
    else:
        xpath = (f"/config/devices/entry[@name='localhost.localdomain']"
                 f"/device-group/entry[@name='{device_group.strip()}']"
                 f"/address-group/entry[@name='{name}']")

    print(f"[*] Exporting and deleting: {name} via XPath: {xpath}")
    export_params = {
        'type': 'config',
        'action': 'get',
        'xpath': xpath,
        'key': API_KEY
    }

    response = requests.get(f"{PANORAMA_HOST}/api/", params=export_params, verify=False)
    if "<entry" not in response.text:
        print(f"[!] Could not find address-group '{name}'")
        return

    values = {"name": name, "location": device_group or "shared"}

    if "<dynamic>" in response.text:
        start = response.text.find("<dynamic>") + len("<dynamic>")
        end = response.text.find("</dynamic>", start)
        values["dynamic"] = response.text[start:end].strip()
        values["members"] = ""
    else:
        values["dynamic"] = ""
        if "<static>" in response.text:
            start = response.text.find("<static>")
            end = response.text.find("</static>", start)
            member_block = response.text[start:end]
            members = []
            for line in member_block.splitlines():
                line = line.strip()
                if line.startswith("<member>") and line.endswith("</member>"):
                    member_value = line.replace("<member>", "").replace("</member>", "").strip()
                    members.append(member_value)
            values["members"] = ",".join(members)
        else:
            values["members"] = ""

    if "<description>" in response.text:
        start = response.text.find("<description>") + len("<description>")
        end = response.text.find("</description>", start)
        values["description"] = response.text[start:end].strip()
    else:
        values["description"] = ""

    if "<tag>" in response.text:
        tag_start = response.text.find("<tag>")
        tag_end = response.text.find("</tag>", tag_start)
        tag_block = response.text[tag_start:tag_end]
        tags = [line.replace("<member>", "").replace("</member>", "").strip()
                for line in tag_block.splitlines() if "<member>" in line]
        values["tag"] = ",".join(tags)
    else:
        values["tag"] = ""

    with open(OUTPUT_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writerow(values)

    delete_params = {
        'type': 'config',
        'action': 'delete',
        'xpath': xpath,
        'key': API_KEY
    }
    del_resp = requests.get(f"{PANORAMA_HOST}/api/", params=delete_params, verify=False)
    if "<result>success</result>" in del_resp.text:
        print(f"[✓] Deleted address-group '{name}' from {device_group or 'Shared'}")
    else:
        print(f"[!] Failed to delete '{name}': {del_resp.text}")

def main():
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)
        for row in reader:
            name = row[0].strip()
            device_group = row[1].strip() if len(row) > 1 else None
            if name:
                export_then_delete_address_group(name, device_group)

if __name__ == "__main__":
    main()