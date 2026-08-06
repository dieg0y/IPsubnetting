"""
IP Subnetting Tool — CLI
========================

A command-line tool for IPv4 subnet calculations, designed as both
a practical utility AND a learning resource for networking concepts.

Architecture (Separation of Concerns):
    ┌─────────────────────┐
    │        App          │  ← Controller: user interaction flow
    ├─────────────────────┤
    │  SubnetCalculator   │  ← Business Logic: all calculations
    ├─────────────────────┤
    │    SubnetResult     │  ← Data Container: immutable result
    ├─────────────────────┤
    │      CLIView        │  ← Presentation: formatting & colors
    └─────────────────────┘

Author:  Diego Yonoff Molina
GitHub:  @dieg0y
"""

import os
import sys
import ipaddress
from dataclasses import dataclass
from typing import Optional, Tuple


# ============================================================
#  ANSI COLOR SUPPORT — Fix for Windows terminals
# ============================================================

def _enable_ansi_support() -> bool:
    """
    Enable ANSI escape code support on Windows terminals.

    On Windows 10+, the terminal supports ANSI/VT100 escape sequences
    but they are DISABLED by default. This function enables them.

    On Linux/macOS, ANSI support is enabled by default — no fix needed.

    Returns:
        True if colors are supported, False otherwise
    """
    # Linux, macOS, and other Unix-like systems support ANSI natively
    if sys.platform != "win32":
        return True

    # Windows 10+ — enable Virtual Terminal Processing
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32

        # STD_OUTPUT_HANDLE = -11
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))

        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        ENABLE_VTP = 0x0004
        kernel32.SetConsoleMode(handle, mode.value | ENABLE_VTP)
        return True
    except Exception:
        # Fallback: os.system('') can also enable ANSI on some Windows versions
        try:
            os.system("")
            return True
        except Exception:
            return False


# ============================================================
#  CONSTANTS — Networking reference values
# ============================================================

MIN_CIDR: int = 0
MAX_CIDR: int = 32

IP_CLASS_RANGES = {
    "A": (1, 126),
    "B": (128, 191),
    "C": (192, 223),
    "D": (224, 239),
    "E": (240, 254),
}

PRIVATE_NETWORKS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]


# ============================================================
#  DATA CONTAINER
# ============================================================

@dataclass(frozen=True)
class SubnetResult:
    """
    Immutable container for subnet calculation results.

    Attributes:
        ip_address:     Original IP address entered by the user
        cidr:           CIDR prefix length (0–32)
        network_id:     Network address (first address in the subnet)
        broadcast:      Broadcast address (last address in the subnet)
        netmask:        Subnet mask in dotted-decimal
        wildcard:       Wildcard mask (inverse of netmask, used in ACLs)
        ip_class:       Classful IP class (A through E)
        total_hosts:    Usable host count (excludes network & broadcast)
        first_host:     First usable host address (None for /31)
        last_host:      Last usable host address (None for /31)
        is_private:     True if IP belongs to RFC 1918 private range
        ip_binary:      Binary representation of the IP address
        netmask_binary: Binary representation of the netmask
    """
    ip_address: str
    cidr: int
    network_id: str
    broadcast: str
    netmask: str
    wildcard: str
    ip_class: str
    total_hosts: int
    first_host: Optional[str]
    last_host: Optional[str]
    is_private: bool
    ip_binary: str
    netmask_binary: str


# ============================================================
#  CORE LOGIC — All subnetting calculations
# ============================================================

class SubnetCalculator:
    """
    Core subnetting engine using Python's ipaddress module.

    WHAT DOES ipaddress DO UNDER THE HOOD?
      Network Address = IP  AND  Netmask     (bitwise AND)
      Broadcast       = Network  OR  Wildcard  (bitwise OR)
      Wildcard        = NOT Netmask           (bitwise complement)
      Usable Hosts    = 2^(32 - CIDR) - 2
    """

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate an IPv4 address string."""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except (ipaddress.AddressValueError, ValueError):
            return False

    @staticmethod
    def validate_cidr(cidr: int) -> bool:
        """Validate a CIDR prefix length (must be 0–32)."""
        return MIN_CIDR <= cidr <= MAX_CIDR

    @staticmethod
    def _to_binary(ip: str) -> str:
        """
        Convert an IPv4 address to binary with dot separators.

        Example:
          192.168.1.100 → 11000000.10101000.00000001.01100100
        """
        octets = [int(o) for o in ip.split(".")]
        binary_octets = [f"{octet:08b}" for octet in octets]
        return ".".join(binary_octets)

    @staticmethod
    def get_ip_class(ip: str) -> str:
        """
        Determine the classful IP class from the first octet.

        ┌───────┬─────────────┬──────────┬──────────────────┐
        │ Class │ First Octet │ Default  │ Purpose          │
        │       │ Range       │ Mask     │                  │
        ├───────┼─────────────┼──────────┼──────────────────┤
        │   A   │   1 – 126   │  /8      │ Very large nets  │
        │   B   │ 128 – 191   │  /16     │ Medium nets      │
        │   C   │ 192 – 223   │  /24     │ Small nets       │
        │   D   │ 224 – 239   │  N/A     │ Multicast        │
        │   E   │ 240 – 254   │  N/A     │ Experimental     │
        └───────┴─────────────┴──────────┴──────────────────┘
        """
        first_octet = int(ip.split(".")[0])

        if first_octet == 0:
            return "A (This Network)"
        if first_octet == 127:
            return "A (Loopback)"

        for cls_name, (low, high) in IP_CLASS_RANGES.items():
            if low <= first_octet <= high:
                if cls_name == "D":
                    return "D (Multicast)"
                if cls_name == "E":
                    return "E (Experimental)"
                return cls_name

        return "Unknown"

    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """
        Check if an IP address is in a private (RFC 1918) range.

        Private ranges (NOT routable on the public internet):
          10.0.0.0/8      → Large enterprises
          172.16.0.0/12   → Medium networks
          192.168.0.0/16  → Home/SMB networks (your WiFi!)
        """
        ip_obj = ipaddress.IPv4Address(ip)
        return any(ip_obj in net for net in PRIVATE_NETWORKS)

    @staticmethod
    def get_total_hosts(cidr: int) -> int:
        """
        Calculate usable hosts: 2^(32 - CIDR) - 2

        We subtract 2 because:
          - Network address (host bits = 0) identifies the subnet
          - Broadcast address (host bits = 1) is for L2 flooding

        Edge cases:
          /32 → 1 host  (single-host route)
          /31 → 0 hosts (point-to-point, RFC 3021)
        """
        host_bits = MAX_CIDR - cidr

        if cidr == MAX_CIDR:
            return 1
        if cidr == MAX_CIDR - 1:
            return 0

        return (2 ** host_bits) - 2

    def calculate(self, ip: str, cidr: int) -> SubnetResult:
        """
        Perform all subnet calculations and return a SubnetResult.

        strict=False allows host bits in the IP
        (e.g., 192.168.1.100/24 is accepted, not just 192.168.1.0/24)
        """
        if not self.validate_ip(ip):
            raise ValueError(f"Invalid IPv4 address: '{ip}'")
        if not self.validate_cidr(cidr):
            raise ValueError(
                f"Invalid CIDR: {cidr}. Must be between {MIN_CIDR} and {MAX_CIDR}"
            )

        network = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
        total_hosts = self.get_total_hosts(cidr)

        if cidr == MAX_CIDR:
            first_host = str(network.network_address)
            last_host = str(network.network_address)
        elif cidr == MAX_CIDR - 1:
            first_host = None
            last_host = None
        else:
            first_host = str(network.network_address + 1)
            last_host = str(network.broadcast_address - 1)

        return SubnetResult(
            ip_address=ip,
            cidr=cidr,
            network_id=str(network.network_address),
            broadcast=str(network.broadcast_address),
            netmask=str(network.netmask),
            wildcard=str(network.hostmask),
            ip_class=self.get_ip_class(ip),
            total_hosts=total_hosts,
            first_host=first_host,
            last_host=last_host,
            is_private=self.is_private_ip(ip),
            ip_binary=self._to_binary(ip),
            netmask_binary=self._to_binary(str(network.netmask)),
        )


# ============================================================
#  PRESENTATION LAYER — Formatted output with colors
# ============================================================

class CLIView:
    """
    Handles all visual output — formatting, colors, and layout.

    Automatically detects if the terminal supports ANSI colors.
    If not (e.g., old Windows terminal, piped output), colors
    are disabled and plain text is shown instead.
    """

    _COLORS_ENABLED: bool = False

    _CODES = {
        "reset":   "\033[0m",
        "bold":    "\033[1m",
        "cyan":    "\033[96m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "red":     "\033[91m",
        "magenta": "\033[95m",
        "dim":     "\033[2m",
    }

    @classmethod
    def enable_colors(cls, enabled: bool = True) -> None:
        """
        Enable or disable colored output.

        Call this once at startup after checking terminal support.
        If disabled, _color() returns plain text with no escape codes.
        """
        cls._COLORS_ENABLED = enabled

    @classmethod
    def _color(cls, color: str, text: str) -> str:
        """
        Wrap text in an ANSI color sequence.

        If colors are disabled (unsupported terminal), returns plain text.
        This ensures the output is always readable, even without color.
        """
        if not cls._COLORS_ENABLED:
            return text
        return f"{cls._CODES[color]}{text}{cls._CODES['reset']}"

    # ----------------------------------------------------------
    #  Display methods
    # ----------------------------------------------------------

    @classmethod
    def show_banner(cls) -> None:
        """Display the application banner on startup."""
        W = 50
        print()
        print(cls._color("cyan", "  ╔" + "═" * W + "╗"))
        title = "IP SUBNETTING TOOL"
        inner = title.center(W)
        print(cls._color("cyan", "  ║") + inner + cls._color("cyan", "║"))
        print(cls._color("cyan", "  ╚" + "═" * W + "╝"))
        print(cls._color("dim", "  Calculate subnet info from any IP + CIDR"))
        print(cls._color("dim", "  " + "─" * W))
        print()

    @classmethod
    def show_error(cls, message: str) -> None:
        """Display a red error message."""
        print(f"\n  {cls._color('red', '✖')} {message}\n")

    @classmethod
    def show_result(cls, result: SubnetResult) -> None:
        """Display all subnet results in a structured table."""
        W = 52

        print()
        print(cls._color("bold", "  ┌" + "─" * W + "┐"))
        header = "SUBNET CALCULATION RESULTS".center(W)
        print(
            cls._color("bold", "  │")
            + cls._color("cyan", header)
            + cls._color("bold", "│")
        )
        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        def row(label: str, value: str) -> None:
            lbl = cls._color("yellow", f"  {label:<18}")
            val = cls._color("green", value)
            visual_len = 2 + 18 + len(value)
            padding = max(0, W - visual_len)
            print(
                cls._color("bold", "  │")
                + lbl
                + val
                + " " * padding
                + cls._color("bold", "│")
            )

        # --- Address Information ---
        row("Address:", result.ip_address)
        row("Netmask:", f"{result.netmask} = /{result.cidr}")
        row("Wildcard:", result.wildcard)
        row("Class:", result.ip_class)

        # Private/Public
        if result.is_private:
            priv_text = "Yes (RFC 1918)"
            priv_col = "green"
        else:
            priv_text = "No (Public)"
            priv_col = "magenta"

        lbl_priv = cls._color("yellow", f"  {'Private:':<18}")
        priv_val = cls._color(priv_col, priv_text)
        priv_pad = max(0, W - 2 - 18 - len(priv_text))
        print(
            cls._color("bold", "  │")
            + lbl_priv
            + priv_val
            + " " * priv_pad
            + cls._color("bold", "│")
        )

        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        # --- Network Information ---
        row("Network ID:", f"{result.network_id}/{result.cidr}")
        row("Broadcast:", result.broadcast)

        if result.first_host and result.last_host:
            row("Host Range:", f"{result.first_host} -> {result.last_host}")
        else:
            row("Host Range:", "N/A (/31 point-to-point)")

        row("Usable Hosts:", f"{result.total_hosts:,}")

        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        # --- Binary ---
        binary_header = "BINARY — Network vs Host bits".center(W)
        print(
            cls._color("bold", "  │")
            + cls._color("cyan", binary_header)
            + cls._color("bold", "│")
        )
        row("IP:", result.ip_binary)
        row("Netmask:", result.netmask_binary)

        print(cls._color("bold", "  └" + "─" * W + "┘"))
        print()

    @classmethod
    def show_menu(cls) -> None:
        """Display the post-calculation options menu."""
        print(cls._color("dim", "  " + "─" * 30))
        print(f"  {cls._color('bold', '1.')} Calculate another subnet")
        print(f"  {cls._color('bold', '2.')} Exit")
        print()


# ============================================================
#  APPLICATION CONTROLLER — User interaction flow
# ============================================================

class App:
    """
    Main application controller — manages the interaction loop.

    FLOW:
      1. Enable ANSI colors (if supported)
      2. Show banner
      3. Loop: prompt → calculate → display → continue?
      4. Exit gracefully
    """

    def __init__(self) -> None:
        self.calculator = SubnetCalculator()
        self.view = CLIView()

    def _get_input(self) -> Tuple[Optional[str], Optional[int]]:
        """Prompt user for IP address and CIDR, with validation."""
        ip = input(f"  {self.view._color('bold', 'IP Address:')} ").strip()
        if not self.calculator.validate_ip(ip):
            self.view.show_error(f"'{ip}' is not a valid IPv4 address")
            return None, None

        cidr_str = input(f"  {self.view._color('bold', 'CIDR [0-32]:')} ").strip()
        try:
            cidr = int(cidr_str)
        except ValueError:
            self.view.show_error(f"'{cidr_str}' is not a valid integer")
            return None, None

        if not self.calculator.validate_cidr(cidr):
            self.view.show_error(
                f"CIDR must be between {MIN_CIDR} and {MAX_CIDR}"
            )
            return None, None

        return ip, cidr

    def _ask_continue(self) -> bool:
        """Ask the user whether to perform another calculation."""
        self.view.show_menu()
        choice = input(f"  {self.view._color('bold', 'Option:')} ").strip()
        return choice == "1"

    def run(self) -> None:
        """Start the application's main loop."""
        # Step 0: Enable ANSI colors for this terminal
        colors_ok = _enable_ansi_support()
        self.view.enable_colors(colors_ok)

        self.view.show_banner()

        running = True
        while running:
            try:
                ip, cidr = self._get_input()

                if ip is not None and cidr is not None:
                    result = self.calculator.calculate(ip, cidr)
                    self.view.show_result(result)

                if not self._ask_continue():
                    running = False

            except KeyboardInterrupt:
                print(f"\n\n  {self.view._color('yellow', 'Interrupted by user')}\n")
                running = False

            except Exception as exc:
                self.view.show_error(f"Unexpected error: {exc}")
                if not self._ask_continue():
                    running = False

        print(f"  {self.view._color('cyan', 'Goodbye! Happy subnetting!')}\n")


# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = App()
    app.run()
