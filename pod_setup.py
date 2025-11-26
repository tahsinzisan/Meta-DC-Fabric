from netmiko import ConnectHandler

spines = [
    {
        "asn": "65401",
        "loopback": "20.0.1.1"
    }
]

def podSetup(podId, torCount):
    podId = str(podId)

    device = {
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin",
    }

    # Configure Spines
    for spine in spines:
        asn = spine["asn"]
        device["host"] = spine["loopback"]
        conn = ConnectHandler(**device)

        conn.send_config_set([f"router bgp {asn}"])
        for i in range(1, 5):  # 4 FSWs
            nei_ip = f"20.{podId}.{i}.1"
            nei_asn = str(65300 + i)
            cmds = [
                f"router bgp {asn}",
                f"neighbor {nei_ip} remote-as {nei_asn}",
                "neighbor {nei_ip} update-source loopback0",
            ]
            conn.send_config_set(cmds)

        conn.disconnect()

    # Configure Fabric switches (4 per pod)
    for i in range(1, 5):
        asn = str(65300 + i)
        device["host"] = f"20.{podId}.{i}.1"
        conn = ConnectHandler(**device)

        conn.send_config_set([f"router bgp {asn}"])

        # Uplinks to spines
        for spine in spines:
            nei_ip = spine["loopback"]
            cmds = [
                f"neighbor {nei_ip} remote-as {spine['asn']}",
                "neighbor {nei_ip} update-source loopback0",
                "neighbor {nei_ip} ebgp-multihop 2"
            ]
            conn.send_config_set(cmds)

        # Downlinks to RSWs
        for r in range(1, torCount + 1):
            nei_ip = f"20.{podId}.0.{r}"
            nei_asn = str(65200 + r)
            cmds = [
                f"neighbor {nei_ip} remote-as {nei_asn}",
                "neighbor {nei_ip} update-source loopback0",
                "neighbor {nei_ip} ebgp-multihop 2",
            ]
            conn.send_config_set(cmds)

        conn.disconnect()

    # Configure RSWs (TORs)
    for r in range(1, torCount + 1):
        asn = str(65200 + r)
        device["host"] = f"20.{podId}.0.{r}"
        conn = ConnectHandler(**device)

        conn.send_config_set([f"router bgp {asn}"])
        for i in range(1, 5):
            nei_ip = f"20.{podId}.{i}.1"
            nei_asn = str(65300 + i)
            cmds = [
                f"neighbor {nei_ip} remote-as {nei_asn}",
                "neighbor {nei_ip} update-source loopback0",
                "neighbor {nei_ip} ebgp-multihop 2",
            ]
            conn.send_config_set(cmds)

        conn.disconnect()
