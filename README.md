# PAN-OS Address/Object Group Management Scripts

This repository provides Python scripts to **export, delete, and recreate** address objects and address groups on **Palo Alto Networks Panorama**, using the XML API.

## 📦 Script Overview

| Script Name                  | Description |
|-----------------------------|-------------|
| `delete_address_objects.py` | Exports and deletes address objects, writing a timestamped CSV backup |
| `delete_address_groups.py`  | Exports and deletes address groups (static/dynamic), writing a CSV |
| `create_address_objects.py` | Recreates address objects from a CSV |
| `create_address_groups.py`  | Recreates address groups from a CSV |

## 🧰 Requirements

- Python 3.x
- `requests` module (installed automatically inside `.venv`)
- Panorama XML API access
- API key (entered at runtime)

## 🔐 Authentication

You will be prompted to enter your **API key** at runtime via secure input (`getpass`).

## 🔧 Configuration File: `.panos.cfg`

The scripts use a config file for hostname and CSV filenames. Example:

```ini
[PANW]
host = https://your-panorama-host
address_csv = sample-address_objects.csv
address_group_csv = sample-address_groups.csv
```

- **`host`**: The Panorama hostname or IP
- **`address_csv`**: Path to input/output file for address objects
- **`address_group_csv`**: Path to input/output file for address groups

> ⚠️ Do **not** include your API key in this file for security reasons.

## 📂 CSV Format

### Address Objects

| name         | ip-netmask       | description     | location     | type         | tag        |
|--------------|------------------|------------------|--------------|--------------|------------|
| web-server-1 | 192.168.1.10/32  | Web frontend     | Branch-FWs   | ip-netmask   | external   |

### Address Groups

| name         | members                   | dynamic           | description              | location    | tag       |
|--------------|----------------------------|-------------------|---------------------------|-------------|-----------|
| web-servers  | web-server-1,api-gateway   |                   | Group of all web servers | Branch-FWs  | external  |
| api-group    |                            | 'tag eq dmz'      | Dynamic group for DMZ    | DataCenter  |           |

- Use `location = shared` for shared config scope.
- `members` is comma-separated for static groups.
- `dynamic` is a filter expression for dynamic groups.

## ▶️ Usage

Use the included wrapper script for convenience:

```bash
chmod +x panw-wrapper.py
./panw-wrapper.py delete-objects
./panw-wrapper.py create-groups
```

Available actions:
- `delete-objects`
- `delete-groups`
- `create-objects`
- `create-groups`

The wrapper will:
- Create a `.venv` (if needed)
- Install `requests`
- Execute the selected script in the venv

## 🔒 Security Notes

- API key is never stored; it is prompted per run.
- SSL certificate verification is disabled in scripts (`verify=False`) for compatibility.
- Consider locking down access to `.panos.cfg` and generated CSV files.

## 📄 License

MIT License

## 🙋 Need Help?

Open an issue or contact your automation/security team.