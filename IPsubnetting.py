import ipaddress

def validate_ip(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

def validate_cidr(cidr):
    return 0 <= cidr <= 32

def get_network(ip, cidr):
    net = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
    return str(net.network_address)

def get_broadcast(ip, cidr):
    net = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
    return str(net.broadcast_address)

def get_netmask(cidr):
    net = ipaddress.IPv4Network(f"0.0.0.0/{cidr}")
    return str(net.netmask)

def get_ip_class(ip):
    first_octet = int(ip.split('.')[0])
    if 1 <= first_octet <= 126:
        return 'A'
    elif 128 <= first_octet <= 191:
        return 'B'
    elif 192 <= first_octet <= 223:
        return 'C'
    elif 224 <= first_octet <= 239:
        return 'D (Multicast)'
    elif 240 <= first_octet <= 254:
        return 'E (Experimental)'
    else:
        return 'Unknown'

def get_total_hosts(cidr):
    host_bits = 32 - cidr
    if host_bits == 0:
        return 1
    return (2 ** host_bits) - 2

def run_subnetting():
    print("\n================== SUBNETTING ==================\n")
    
    ip = input("Enter the IP address: ").strip()
    if not validate_ip(ip):
        print("\n❌ Invalid IP address.\n")
        return
    
    try:
        cidr = int(input("Enter the CIDR: ").strip())
    except ValueError:
        print("\n❌ CIDR must be a number.\n")
        return

    if not validate_cidr(cidr):
        print("\n❌ CIDR out of range. Must be between 0 and 32.\n")
        return

    # === CALCULATIONS ===
    netmask = get_netmask(cidr)
    network_id = get_network(ip, cidr)
    broadcast = get_broadcast(ip, cidr)
    ip_class = get_ip_class(ip)
    total_hosts = get_total_hosts(cidr)

    # === OUTPUT ===
    print("\n============= RESULT ===========================\n")
    print(f"Address:        {ip}")
    print(f"Netmask:        {netmask} = /{cidr}")
    print(f"Network ID:     {network_id}/{cidr}")
    print(f"Class:          {ip_class}")
    print(f"Broadcast:      {broadcast}")
    print(f"Total Hosts:    {total_hosts}")
    print("\n================================================\n")

# === MAIN LOOP ===
while True:
    run_subnetting()
    
    print("What would you like to do next?")
    print("1) Add another IP")
    print("2) Exit the program")

    option = input("\nSelect an option: ").strip()
    
    if option != '1':
        print("\n👋 Exiting the program. See you!\n")
        break
