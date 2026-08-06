```markdown
# 🌐 IP Subnetting Tool (CLI)

A command-line tool for IPv4 subnet calculations — built as both a **practical utility**
and a **learning resource** for networking students and IT professionals.

## ✨ Features

| Feature | Description |
|---|---|
| 🔢 **Full Subnet Info** | Network ID, Broadcast, Netmask, Wildcard mask |
| 📊 **Host Range** | First & last usable host addresses |
| 🔤 **IP Classification** | Class A–E with descriptions (Multicast, Loopback, etc.) |
| 🔒 **Private/Public Detection** | RFC 1918 private range identification |
| 💻 **Binary Representation** | IP & Netmask in binary — see network vs. host bits! |
| ⚡ **Edge Cases** | Correctly handles /31 (point-to-point) & /32 (host route) |
| ✅ **Input Validation** | Clear error messages for invalid IPs or CIDRs |
| 🎨 **Colored Output** | ANSI colors for readability |
| 🏗️ **Clean Architecture** | OOP with separation of concerns, type hints, dataclasses |
| 📦 **Reusable** | Import `SubnetCalculator` in your own scripts |

## 🚀 Quick Start

### Prerequisites
- Python 3.6+
- No external dependencies (uses only `ipaddress` from the standard library)

### Installation

```bash
git clone https://github.com/dieg0y/IPsubnetting.git
cd IPsubnetting
python IPsubnetting.py
```

## 💻 Usage Example

```
  ╔════════════════════════════════════════════════╗
  ║              IP SUBNETTING TOOL                ║
  ╚════════════════════════════════════════════════╝
  Calculate subnet info from any IP + CIDR

  IP Address: 192.168.1.100
  CIDR [0-32]: 24

  ┌──────────────────────────────────────────────────┐
  │          SUBNET CALCULATION RESULTS              │
  ├──────────────────────────────────────────────────┤
  │  Address:        192.168.1.100                   │
  │  Netmask:        255.255.255.0 = /24             │
  │  Wildcard:       0.0.0.255                       │
  │  Class:          C                               │
  │  Private:        Yes (RFC 1918)                  │
  ├──────────────────────────────────────────────────┤
  │  Network ID:     192.168.1.0/24                  │
  │  Broadcast:      192.168.1.255                   │
  │  Host Range:     192.168.1.1 → 192.168.1.254    │
  │  Usable Hosts:   254                             │
  ├──────────────────────────────────────────────────┤
  │        BINARY — Network vs Host bits             │
  │  IP:             11000000.10101000.00000001.01100100  │
  │  Netmask:        11111111.11111111.11111111.00000000  │
  └──────────────────────────────────────────────────┘

  ──────────────────────────────────
  1. Calculate another subnet
  2. Exit
```

## 🧑‍🏫 Using as a Library

The `SubnetCalculator` class can be imported and used programmatically:

```python
from IPsubnetting import SubnetCalculator

calc = SubnetCalculator()
result = calc.calculate("10.10.10.5", 23)

print(result.network_id)    # "10.10.10.0"
print(result.broadcast)     # "10.10.11.255"
print(result.first_host)    # "10.10.10.1"
print(result.last_host)     # "10.10.11.254"
print(result.total_hosts)   # 510
print(result.is_private)    # True
print(result.ip_binary)     # "00001010.00001010.00001010.00000101"
```

## 🏗️ Architecture

```
┌─────────────────────┐
│        App          │  ← Controller: user interaction loop
├─────────────────────┤
│  SubnetCalculator   │  ← Business Logic: pure calculations
├─────────────────────┤
│    SubnetResult     │  ← Data Container: immutable result
├─────────────────────┤
│      CLIView        │  ← Presentation: formatting & colors
└─────────────────────┘
```

- **SubnetCalculator**: All networking math. No I/O. Easy to unit test.
- **SubnetResult**: Frozen dataclass. Cannot be modified after creation.
- **CLIView**: All terminal output. Could be replaced with JSON/GUI.
- **App**: Orchestrates the flow. Injects calculator + view.

## 🛠️ Technical Details

| | |
|---|---|
| **Language** | Python 3.6+ |
| **Core Module** | `ipaddress` (Standard Library) |
| **Architecture** | OOP, Separation of Concerns |
| **Type Safety** | Full type hints |
| **Immutability** | Frozen dataclass for results |
| **Complexity** | O(1) for all calculations |

## 📊 Use Cases

- 🎓 Network engineering students learning subnetting
- 💼 IT professionals needing quick calculations
- 📜 Preparing for certifications (CCNA, CompTIA Network+)
- 🔧 Automating network documentation
- 📦 As a library in other Python networking tools

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features (IPv6 support, subnet division, VLSM)
- Submit pull requests

## 👤 Author

**Diego Yonoff Molina**
- GitHub: [@dieg0y](https://github.com/dieg0y)
- LinkedIn: [diegoyonoff](https://www.linkedin.com/in/diegoyonoff/)
- Portfolio: [dieg0y.github.io](https://dieg0y.github.io/)

---

⭐ If this tool helped you learn subnetting, consider giving it a star!
```
