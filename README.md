# 🌐 IP Subnetting Tool (CLI)

A lightweight, user-friendly command-line tool for calculating subnet information from an IP address and CIDR notation.

## 📋 Features

- **Network Analysis**: Automatically calculates Network ID, Broadcast Address, and Netmask
- **IP Classification**: Identifies IP class (A, B, C, D, or E)
- **Host Calculation**: Determines total usable hosts in the subnet
- **Input Validation**: Robust error handling for invalid IP addresses or CIDR values
- **Interactive CLI**: Clean, repeatable interface for multiple calculations
- **Pure Python**: Built using only the standard `ipaddress` module (no external dependencies)

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or higher
- Works on Windows, Linux, and macOS

### Installation

1. Clone this repository:
```bash
git clone https://github.com/dieg0y/IPsubnetting.git
cd IPsubnetting
```

2. Run the script:
```bash
python IPsubnetting.py
```

## 💻 Usage Example
```
========================================
    IP SUBNETTING CALCULATOR
========================================

Enter an IP address: 192.168.1.0
Enter CIDR (e.g., 24): 24

--- Subnet Information ---
Network ID       : 192.168.1.0
Broadcast Address: 192.168.1.255
Netmask          : 255.255.255.0
IP Class         : C
Usable Hosts     : 254

Do you want to calculate another subnet? (y/n): n
```

## 🛠️ Technical Details

- **Language**: Python 3
- **Core Module**: `ipaddress` (Python Standard Library)
- **Time Complexity**: O(1) for all calculations
- **Error Handling**: Validates IP format and CIDR range (0-32)

## 📊 Use Cases

- Network engineering students learning subnetting
- IT professionals needing quick subnet calculations
- Preparing for networking certifications (CCNA, CompTIA Network+)
- Automating network documentation tasks

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Diego Yonoff Molina**
- GitHub: [@dieg0y](https://github.com/dieg0y)
- LinkedIn: [diegoyonoff](https://www.linkedin.com/in/diegoyonoff/)
- Portfolio: [dieg0y.github.io](https://dieg0y.github.io/)

---

⭐ If you found this tool helpful, consider giving it a star!
