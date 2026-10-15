# PAN-OS Address Object & Group Manager


A simple and robust command-line toolkit for bulk managing address objects and address groups on Palo Alto Networks Panorama via the XML API.

This toolset is designed for network administrators and automation engineers to perform common, repetitive tasks safely and efficiently. All operations are driven by a central wrapper script, `panw-wrapper.py`, which handles environment setup and execution.

---

## 📋 Table of Contents

- [Features](#-features)
- [Getting Started](#-getting-started)
- [Available Actions](#️-available-actions)
- [CSV File Formats](#-csv-file-formats)
- [Security Notes](#-security-notes)

---

## ✨ Features

- **Unified Wrapper Script**: A single entry point (`panw-wrapper.py`) for all actions.
- **Automated Environment**: Automatically creates a Python virtual environment (`.venv`) and installs dependencies.
- **Backup and Restore**: Export existing objects to a CSV file before deleting, allowing for easy recovery.
- **Bulk Creation**: Create objects and groups in bulk by populating a simple CSV file.
- **Cross-Platform**: The wrapper script is compatible with Windows, macOS, and Linux.
- **Secure**: Prompts for your API key at runtime and never stores it on disk.

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.7+

### 2. Configuration (`panw.cfg`)

Before running the tool, create a configuration file named `panw.cfg` in the same directory. This file tells the scripts where to find your Panorama instance and which CSV files to use.

**Example `panw.cfg`:**
```ini
[PANW]
panorama_host = https://your-panorama-address
address_csv = inventory/address-objects.csv
address_group_csv = inventory/address-groups.csv
# Optional TLS settings (certificate verification is ON by default):
# ca_bundle = /path/to/panorama-ca.pem   # trust a private CA
# verify_ssl = false                     # lab only: skip verification
```

- **`panorama_host`**: The full URL to your Panorama management interface.
- **`address_csv`**: The path to the CSV file for managing **address objects**.
- **`address_group_csv`**: The path to the CSV file for managing **address groups**.
- **`ca_bundle`** / **`verify_ssl`** (optional): how Panorama's TLS certificate is checked. Verification is on by default.

The API key is prompted for at runtime. For automation you can set the `PANOS_API_KEY` environment variable instead.

> 💡 **Tip:** It's a good practice to store your CSV files in a subdirectory like `inventory/` to keep the project organized.

### 3. Running the Tool

All scripts should be executed through the `panw-wrapper.py` script. It's the only file you need to interact with directly.

First, make the wrapper executable (on macOS/Linux):
```bash
chmod +x panw-wrapper.py
```

Then, run the desired action. The wrapper will handle creating a virtual environment and installing dependencies on the first run.
```bash
# To delete address objects (and create a backup)
./panw-wrapper.py delete-objects

# To create address groups from a CSV file
./panw-wrapper.py create-groups
```

---

## ▶️ Available Actions

The following actions are available:

| Action             | Description                                                   |
| ------------------ | ------------------------------------------------------------- |
| `create-objects`   | Creates address objects from the `address_csv` file.          |
| `delete-objects`   | Deletes objects listed in `address_csv` (by `name` + `location`), creating a backup first. |
| `create-groups`    | Creates address groups from the `address_group_csv` file.     |
| `delete-groups`    | Deletes groups listed in `address_group_csv` (by `name` + `location`), creating a backup first.  |

Backups are written as `<timestamp>-address-object-backup.csv` / `<timestamp>-address-group-backup.csv` in the same format the create actions read, so restoring is just pointing `address_csv` (or `address_group_csv`) at the backup and running the matching create action. Nothing is committed: review and commit in Panorama.

---

## 📂 CSV File Formats

The scripts use specific headers in the CSV files. When a backup is created, it will automatically use this format.

### Address Objects (`address_csv`)

This file is for `ip-netmask`, `ip-range`, and `fqdn` objects.

| name         | value                 | type         | description      | location   | tag          |
| :----------- | :-------------------- | :----------- | :--------------- | :--------- | :----------- |
| `web-server-1` | `192.168.1.10/32`     | `ip-netmask` | Web frontend     | `Branch-FWs` | `external,pci` |
| `corp-dns`   | `dns.example.com`     | `fqdn`       | Corporate DNS    | `shared`   | `internal`   |
| `guest-range`| `10.100.0.1-10.100.0.254` | `ip-range`   | Guest WiFi Range | `Guest-DG`   |              |

- **`type`**: Must be one of `ip-netmask`, `ip-range`, or `fqdn`.
- **`location`**: The Panorama Device Group. Use `shared` for shared objects.

### Address Groups (`address_group_csv`)

This file is for static and dynamic address groups.

| name         | members                  | dynamic_filter   | description              | location   | tag        |
| :----------- | :----------------------- | :--------------- | :----------------------- | :--------- | :--------- |
| `web-servers`  | `web-server-1,corp-dns`  |                  | Group of all web servers | `Branch-FWs` | `external` |
| `dmz-dynamic`  |                          | `'dmz'`          | Dynamic group for DMZ    | `DataCenter` |            |

- For **static** groups, populate the `members` column with a comma-separated list of address object names.
- For **dynamic** groups, populate the `dynamic_filter` column with the filter criteria (e.g., `'tag1' and 'tag2'`). Leave `members` empty.

---

## 🔒 Security Notes

- Your API key is prompted for on each run (or read from `PANOS_API_KEY`) and is **never** stored on disk or printed. It is sent in the `X-PAN-KEY` header rather than the URL, so it doesn't land in web server or proxy logs.
- TLS certificate verification is **on** by default. Use `ca_bundle` for a private CA; `verify_ssl = false` is for lab boxes only.
- Object and device-group names are quoted safely in XPath expressions, so names containing quotes can't alter the query.
- The `panw.cfg` file and any CSV files may contain sensitive network information. Restrict access to these files as per your organization's security policy.

