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

Networking Concepts Covered:
    - IPv4 addressing & CIDR notation
    - Network / Broadcast addresses
    - Netmask & Wildcard mask
    - IP class classification (A–E)
    - Usable host ranges (first & last)
    - Binary representation (network vs host bits)
    - Private vs Public ranges (RFC 1918)
    - Edge cases: /31 (point-to-point) & /32 (host route)

Author:  Diego Yonoff Molina
GitHub:  @dieg0y
"""

import ipaddress
from dataclasses import dataclass
from typing import Optional, Tuple


# ============================================================
#  CONSTANTS — Networking reference values
# ============================================================
# Understanding these ranges is fundamental to IP networking.

MIN_CIDR: int = 0
MAX_CIDR: int = 32

# Classful IP ranges based on the first octet (RFC 791)
#
#  Class A → 0-127   (but 0 and 127 are special)
#  Class B → 128-191
#  Class C → 192-223
#  Class D → 224-239  (Multicast, RFC 5771)
#  Class E → 240-255  (Experimental)
#
IP_CLASS_RANGES = {
    "A": (1, 126),
    "B": (128, 191),
    "C": (192, 223),
    "D": (224, 239),
    "E": (240, 254),
}

# RFC 1918 Private address spaces (NOT routable on the public internet)
#
#  10.0.0.0/8      → Used by large enterprises
#  172.16.0.0/12   → Used by medium networks
#  192.168.0.0/16  → Used by home/SMB networks (your WiFi!)
#
PRIVATE_NETWORKS = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]


# ============================================================
#  DATA CONTAINER — Holds all calculated subnet information
# ============================================================


@dataclass(frozen=True)
class SubnetResult:
    """
    Immutable container for subnet calculation results.

    WHY @dataclass?
      - Auto-generates __init__, __repr__, __eq__ (less boilerplate)
      - frozen=True makes it immutable (can't modify after creation)
      - Self-documenting: every field is visible at a glance

    WHY immutable?
      - Calculation results shouldn't change after being computed
      - Prevents accidental mutation bugs
      - Can be safely passed around (thread-safe, hashable)

    Attributes:
        ip_address:     Original IP address entered by the user
        cidr:           CIDR prefix length (0–32)
        network_id:     Network address (first address in the subnet)
        broadcast:      Broadcast address (last address in the subnet)
        netmask:        Subnet mask in dotted-decimal (e.g., 255.255.255.0)
        wildcard:       Wildcard mask = inverse of netmask (used in ACLs)
        ip_class:       Classful IP class (A through E)
        total_hosts:    Usable host count (excludes network & broadcast)
        first_host:     First usable host address (None for /31)
        last_host:      Last usable host address (None for /31)
        is_private:     True if IP belongs to an RFC 1918 private range
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

    WHY A CLASS INSTEAD OF FUNCTIONS?
      1. Encapsulation: all network logic lives in one namespace
      2. Testability: easy to instantiate and test in isolation
      3. Extensibility: could add IPv6 support via subclassing
      4. Dependency injection: the App can swap calculators

    WHAT DOES ipaddress DO UNDER THE HOOD?
      Network Address = IP  AND  Netmask     (bitwise AND)
      Broadcast       = Network  OR  Wildcard  (bitwise OR)
      Wildcard        = NOT Netmask           (bitwise complement)
      Usable Hosts    = 2^(32 - CIDR) - 2    (minus net & broadcast)

    All these bit operations are handled for you by the module,
    but understanding the math is key to mastering subnetting.
    """

    # ----------------------------------------------------------
    #  Validators
    # ----------------------------------------------------------

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """
        Validate an IPv4 address string.

        The ipaddress module checks:
          - Exactly 4 octets separated by dots
          - Each octet is an integer from 0 to 255
          - No ambiguous leading zeros (e.g., "01.2.3.4")

        Args:
            ip: String like "192.168.1.1"

        Returns:
            True if valid, False otherwise
        """
        try:
            ipaddress.IPv4Address(ip)
            return True
        except (ipaddress.AddressValueError, ValueError):
            return False

    @staticmethod
    def validate_cidr(cidr: int) -> bool:
        """
        Validate a CIDR prefix length.

        CIDR = count of leading 1-bits in the netmask.
          /0  → 0.0.0.0         (all addresses)
          /24 → 255.255.255.0   (typical LAN)
          /32 → 255.255.255.255 (single host)

        Args:
            cidr: Integer to validate

        Returns:
            True if within 0–32, False otherwise
        """
        return MIN_CIDR <= cidr <= MAX_CIDR

    # ----------------------------------------------------------
    #  Helper calculations
    # ----------------------------------------------------------

    @staticmethod
    def _to_binary(ip: str) -> str:
        """
        Convert an IPv4 address to binary with dot separators.

        EXAMPLE — Why this matters for learning:
          IP:      11000000.10101000.00000001.01100100  (192.168.1.100)
          Netmask: 11111111.11111111.11111111.00000000  (/24)
                   ─────────── NETWORK ────── ── HOST ──

          Where the netmask has 1s = NETWORK bits (can't change)
          Where the netmask has 0s = HOST bits (can be assigned)

        Args:
            ip: Valid IPv4 address string

        Returns:
            Binary string like "11000000.10101000.00000001.01100100"
        """
        octets = [int(o) for o in ip.split(".")]
        # f"{value:08b}" formats as 8-bit binary, zero-padded
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

        Special cases:
          - 127.x.x.x → Loopback (your own machine)
          - 0.x.x.x   → "This network" (obsolete)

        Args:
            ip: Valid IPv4 address string

        Returns:
            Class letter with description for special types
        """
        first_octet = int(ip.split(".")[0])

        # Special ranges first
        if first_octet == 0:
            return "A (This Network)"
        if first_octet == 127:
            return "A (Loopback)"

        # Standard class ranges
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

        Private IPs are used inside local networks and are NOT
        routable on the public internet. Your home router assigns
        addresses from 192.168.x.x — that's RFC 1918!

        Args:
            ip: Valid IPv4 address string

        Returns:
            True if private, False if public
        """
        ip_obj = ipaddress.IPv4Address(ip)
        return any(ip_obj in net for net in PRIVATE_NETWORKS)

    @staticmethod
    def get_total_hosts(cidr: int) -> int:
        """
        Calculate the number of usable hosts in a subnet.

        FORMULA:  2^(32 - CIDR) - 2

        Why subtract 2?
          - Network address (host bits all 0) → identifies the subnet
          - Broadcast address (host bits all 1) → for L2 flooding

        Edge cases:
          - /32 → 1 host  (single-host route, common in routing tables)
          - /31 → 0 hosts (point-to-point link, RFC 3021)
          - /0  → 4,294,967,294 hosts (the entire IPv4 space minus 2)

        Args:
            cidr: Valid CIDR prefix length

        Returns:
            Number of usable host addresses
        """
        host_bits = MAX_CIDR - cidr

        if cidr == MAX_CIDR:       # /32 → single host
            return 1
        if cidr == MAX_CIDR - 1:   # /31 → point-to-point (RFC 3021)
            return 0

        return (2**host_bits) - 2

    # ----------------------------------------------------------
    #  Main calculation — Orchestrates everything
    # ----------------------------------------------------------

    def calculate(self, ip: str, cidr: int) -> SubnetResult:
        """
        Perform all subnet calculations and return a SubnetResult.

        This is the main entry point. It:
          1. Validates inputs (fail fast with clear errors)
          2. Creates an IPv4Network object (the core data structure)
          3. Computes all derived values
          4. Packages them into an immutable SubnetResult

        The `strict=False` parameter:
          - strict=True  → IP must be the network address (e.g., 192.168.1.0/24 ✓, 192.168.1.100/24 ✗)
          - strict=False → IP can have host bits set (e.g., 192.168.1.100/24 ✓)
          We use False because users typically enter host IPs, not network IDs.

        Args:
            ip:   Valid IPv4 address string
            cidr: Valid CIDR prefix length (0–32)

        Returns:
            SubnetResult with all calculated information

        Raises:
            ValueError: If IP or CIDR is invalid
        """
        # --- Validate inputs (fail fast) ---
        if not self.validate_ip(ip):
            raise ValueError(f"Invalid IPv4 address: '{ip}'")
        if not self.validate_cidr(cidr):
            raise ValueError(
                f"Invalid CIDR: {cidr}. Must be between {MIN_CIDR} and {MAX_CIDR}"
            )

        # --- Core calculation ---
        network = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)

        # --- Host range ---
        total_hosts = self.get_total_hosts(cidr)

        if cidr == MAX_CIDR:
            # /32: the "host" is the address itself
            first_host = str(network.network_address)
            last_host = str(network.network_address)
        elif cidr == MAX_CIDR - 1:
            # /31: no usable hosts per traditional rules (RFC 3021)
            first_host = None
            last_host = None
        else:
            # Normal case: first = network+1, last = broadcast-1
            first_host = str(network.network_address + 1)
            last_host = str(network.broadcast_address - 1)

        # --- Build the immutable result ---
        return SubnetResult(
            ip_address=ip,
            cidr=cidr,
            network_id=str(network.network_address),
            broadcast=str(network.broadcast_address),
            netmask=str(network.netmask),
            wildcard=str(network.hostmask),          # hostmask = wildcard
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

    WHY SEPARATE PRESENTATION FROM LOGIC?
      - Can change the UI (add GUI, JSON output) without touching math
      - Easy to test: mock the view, verify it received correct data
      - Single Responsibility: this class only cares about HOW to display

    ANSI COLOR CODES:
      These escape sequences are interpreted by the terminal.
      \033[1m  = bold    \033[91m = red
      \033[92m = green   \033[93m = yellow
      \033[95m = magenta \033[96m = cyan
      \033[2m  = dim     \033[0m  = reset
    """

    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "magenta": "\033[95m",
        "dim": "\033[2m",
    }

    @classmethod
    def _color(cls, color: str, text: str) -> str:
        """Wrap text in an ANSI color sequence."""
        return f"{cls.COLORS[color]}{text}{cls.COLORS['reset']}"

    # ----------------------------------------------------------
    #  Display methods
    # ----------------------------------------------------------

    @classmethod
    def show_banner(cls) -> None:
        """Display the application banner on startup."""
        title = "IP SUBNETTING TOOL"
        print()
        print(cls._color("cyan", "  ╔" + "═" * 46 + "╗"))
        print(cls._color("cyan", "  ║") + title.center(50) + cls._color("cyan", "║"))
        print(cls._color("cyan", "  ╚" + "═" * 46 + "╝"))
        print(cls._color("dim", "  Calculate subnet info from any IP + CIDR"))
        print(cls._color("dim", "  " + "─" * 46))
        print()

    @classmethod
    def show_error(cls, message: str) -> None:
        """Display a red error message."""
        print(f"\n  {cls._color('red', '✖')} {message}\n")

    @classmethod
    def show_result(cls, result: SubnetResult) -> None:
        """
        Display all subnet results in a structured table.

        Layout inspired by 'ipcalc' (Linux) — familiar to network engineers.
        """
        W = 50  # table width

        # --- Header ---
        print()
        print(cls._color("bold", "  ┌" + "─" * W + "┐"))
        print(
            cls._color("bold", "  │")
            + cls._color("cyan", "  SUBNET CALCULATION RESULTS".center(W - 2))
            + cls._color("bold", "│")
        )
        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        # --- Row helper ---
        def row(label: str, value: str) -> None:
            """Print a single formatted row: label + value."""
            lbl = cls._color("yellow", f"  {label:<18}")
            val = cls._color("green", value)
            # Calculate padding: we need to account for ANSI escape sequences
            # in the printed length (they don't take visual space)
            visual_len = 2 + 18 + len(value)  # 2 spaces + 18 label + value
            padding = max(0, W - 2 - visual_len)
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

        # Private/Public with inline coloring
        priv_text = (
            cls._color("green", "Yes (RFC 1918)")
            if result.is_private
            else cls._color("magenta", "No (Public)")
        )
        lbl_priv = cls._color("yellow", f"  {'Private:':<18}")
        priv_visual = "Yes (RFC 1918)" if result.is_private else "No (Public)"
        priv_pad = max(0, W - 2 - 2 - 18 - len(priv_visual))
        print(
            cls._color("bold", "  │") + lbl_priv + priv_text + " " * priv_pad + cls._color("bold", "│")
        )

        # --- Separator ---
        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        # --- Network Information ---
        row("Network ID:", f"{result.network_id}/{result.cidr}")
        row("Broadcast:", result.broadcast)

        if result.first_host and result.last_host:
            row("Host Range:", f"{result.first_host} → {result.last_host}")
        else:
            row("Host Range:", "N/A (/31 point-to-point)")

        row("Usable Hosts:", f"{result.total_hosts:,}")

        # --- Separator ---
        print(cls._color("bold", "  ├" + "─" * W + "┤"))

        # --- Binary (Learning Section) ---
        print(
            cls._color("bold", "  │")
            + cls._color("cyan", "  BINARY — Network vs Host bits".center(W - 2))
            + cls._color("bold", "│")
        )
        row("IP:", result.ip_binary)
        row("Netmask:", result.netmask_binary)

        # --- Footer ---
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
      1. Show banner
      2. Loop:
           a. Prompt for IP + CIDR
           b. Validate inputs
           c. Calculate & display results
           d. Ask: continue or exit?
      3. Exit gracefully

    WHY A CLASS?
      - Could inject a different View (JSON, GUI) for testing
      - Could add history tracking, logging, etc.
      - Clean single entry point: App().run()
    """

    def __init__(self) -> None:
        self.calculator = SubnetCalculator()
        self.view = CLIView()

    def _get_input(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Prompt user for IP address and CIDR, with validation.

        Returns:
            (ip, cidr) on success, (None, None) on validation failure
        """
        # --- IP Address ---
        ip = input(f"  {self.view._color('bold', 'IP Address:')} ").strip()
        if not self.calculator.validate_ip(ip):
            self.view.show_error(f"'{ip}' is not a valid IPv4 address")
            return None, None

        # --- CIDR ---
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
        """
        Ask the user whether to perform another calculation.

        Returns:
            True if user wants to continue, False otherwise
        """
        self.view.show_menu()
        choice = input(f"  {self.view._color('bold', 'Option:')} ").strip()
        return choice == "1"

    def run(self) -> None:
        """
        Start the application's main loop.

        Handles:
          - Normal flow: input → calculate → display → repeat
          - Ctrl+C: graceful interruption
          - Unexpected errors: displays message, offers to continue
        """
        self.view.show_banner()

        running = True
        while running:
            try:
                # Step 1: Get & validate input
                ip, cidr = self._get_input()

                # Step 2: Calculate & display
                if ip is not None and cidr is not None:
                    result = self.calculator.calculate(ip, cidr)
                    self.view.show_result(result)

                # Step 3: Continue or exit?
                if not self._ask_continue():
                    running = False

            except KeyboardInterrupt:
                # User pressed Ctrl+C — exit gracefully
                print(
                    f"\n\n  {self.view._color('yellow', '🛑 Interrupted by user')}\n"
                )
                running = False

            except Exception as exc:
                # Catch-all for unexpected errors (never crash silently)
                self.view.show_error(f"Unexpected error: {exc}")
                if not self._ask_continue():
                    running = False

        # Farewell message
        print(f"  {self.view._color('cyan', '👋 Goodbye! Happy subnetting!')}\n")


# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    """
    This guard ensures the code only runs when executed directly,
    NOT when imported as a module.

    WHY THIS MATTERS:
      # Another script can now reuse your calculator:
      from IPsubnetting import SubnetCalculator
      result = SubnetCalculator().calculate("10.0.0.1", 24)
      print(result.total_hosts)  # 254

    This makes your code a reusable LIBRARY, not just a script.
    """
    app = App()
    app.run()
