from netmiko import ConnectHandler
import time
import re

def get_bgp_neighbors(conn):
    """Get a list of all BGP neighbors from the device."""
    output = conn.send_command("show ip bgp neighbors")
    neighbors = re.findall(r'BGP neighbor is (\S+),', output)
    return neighbors

def apply_bgp_community(conn, bgp_as, vip_ip, community, neighbors):
    """Apply route-map to VIP for all BGP neighbors."""
    commands = [f"router bgp {bgp_as}"]

    # Route-map for this VIP
    commands.append(f"route-map SET_STATE permit 10")
    commands.append(f" match ip address {vip_ip}")
    commands.append(f" set community {community} additive")

    # Apply route-map to all neighbors
    for nbr in neighbors:
        commands.append(f"neighbor {nbr} route-map SET_STATE out")

    conn.send_config_set(commands)
    conn.save_config()
    print(f"[INFO] Applied {community} state to {vip_ip} on all neighbors")

def live_to_drain(host, username, password, bgp_as, vip_ip, warm_timer=30):
    """
    Transition VIP state from LIVE → WARM → DRAIN.
    """
    device = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password
    }

    conn = ConnectHandler(**device)
    neighbors = get_bgp_neighbors(conn)

    # LIVE → WARM
    apply_bgp_community(conn, bgp_as, vip_ip, "WARM", neighbors)
    print(f"[INFO] WARM state applied. Waiting {warm_timer}s...")
    time.sleep(warm_timer)

    # WARM → DRAIN
    apply_bgp_community(conn, bgp_as, vip_ip, "DRAIN", neighbors)
    print(f"[INFO] DRAIN state applied.")

    conn.disconnect()
    print(f"[INFO] Live-to-Drain transition complete for {vip_ip}.")

def drain_to_live(host, username, password, bgp_as, vip_ip, warm_timer=30):
    """
    Transition VIP state from DRAIN → WARM → LIVE.
    """
    device = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password
    }

    conn = ConnectHandler(**device)
    neighbors = get_bgp_neighbors(conn)

    # DRAIN → WARM
    apply_bgp_community(conn, bgp_as, vip_ip, "WARM", neighbors)
    print(f"[INFO] WARM state applied. Waiting {warm_timer}s...")
    time.sleep(warm_timer)

    # WARM → LIVE
    apply_bgp_community(conn, bgp_as, vip_ip, "LIVE", neighbors)
    print(f"[INFO] LIVE state applied.")

    conn.disconnect()
    print(f"[INFO] Drain-to-Live transition complete for {vip_ip}.")
