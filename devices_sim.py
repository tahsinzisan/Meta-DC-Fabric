class Device:
    def __init__(self, name, asn, loopback):
        self.name = name
        self.asn = asn
        self.loopback = loopback
        self.neighbors = {}      # neighbor_name: remote_asn
        self.state = "LIVE"      # LIVE/WARM/DRAIN
        self.routes_advertised = set()

    def add_neighbor(self, neighbor_name, remote_asn):
        self.neighbors[neighbor_name] = remote_asn

    def advertise_route(self, route):
        if self.state != "DRAIN":
            self.routes_advertised.add(route)

    def change_state(self, state):
        self.state = state

    def __repr__(self):
        return f"<Device {self.name} ASN:{self.asn} State:{self.state} Neighbors:{len(self.neighbors)}>"
