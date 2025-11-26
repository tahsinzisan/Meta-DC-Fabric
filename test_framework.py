from devices_sim import Device


# UNIT TEST: Test podSetup logic

def unit_test():
    print("UNIT TEST: ASN and neighbor assignments")
    # create sample pod
    spine = Device("SSW1", 65401, "20.1.0.1")
    fsw = Device("FSW1", 65301, "20.1.1.1")
    rsw = Device("RSW1", 65201, "20.1.0.101")

    # emulate connections
    fsw.add_neighbor(spine.name, spine.asn)
    rsw.add_neighbor(fsw.name, fsw.asn)

    # check neighbor setup
    assert fsw.neighbors[spine.name] == spine.asn
    assert rsw.neighbors[fsw.name] == fsw.asn
    print("Unit test passed: neighbor ASN assignments are correct")


# EMULATION TEST: simulate route propagation & states

def emulation_test():
    print("\nEMULATION TEST: Route advertisement and LIVE/WARM/DRAIN")
    spine = Device("SSW1", 65401, "20.1.0.1")
    fsw = Device("FSW1", 65301, "20.1.1.1")
    rsw = Device("RSW1", 65201, "20.1.0.101")

    fsw.add_neighbor(spine.name, spine.asn)
    rsw.add_neighbor(fsw.name, fsw.asn)

    # initial LIVE state
    rsw.advertise_route("10.0.1.0/24")
    fsw.advertise_route("10.0.1.0/24")

    print(f"RSW routes: {rsw.routes_advertised}")
    print(f"FSW routes: {fsw.routes_advertised}")

    # Transition RSW to WARM (route still advertised but deprioritized)
    rsw.change_state("WARM")
    rsw.advertise_route("10.0.1.0/24")  # emulates reduced preference
    print(f"RSW state after WARM: {rsw.state}, routes: {rsw.routes_advertised}")

    # Transition RSW to DRAIN (no production route advertised)
    rsw.change_state("DRAIN")
    rsw.advertise_route("10.0.1.0/24")
    print(f"RSW state after DRAIN: {rsw.state}, routes: {rsw.routes_advertised}")
    assert "10.0.1.0/24" not in rsw.routes_advertised
    print("Emulation test passed: route advertisement respects LIVE/WARM/DRAIN states")


# CANARY TEST: simulate a small pod for full deployment

def canary_test():
    print("\nCANARY TEST: small-scale pod simulation")
    spines = [Device(f"SSW{i}", 65400+i, f"20.1.{i}.1") for i in range(1,2)]
    fsws = [Device(f"FSW{i}", 65300+i, f"20.1.{i}.2") for i in range(1,3)]
    rsws = [Device(f"RSW{i}", 65200+i, f"20.1.0.{i}") for i in range(1,3)]

    # connect neighbors
    for fsw in fsws:
        for spine in spines:
            fsw.add_neighbor(spine.name, spine.asn)
    for rsw, fsw in zip(rsws, fsws):
        rsw.add_neighbor(fsw.name, fsw.asn)

    # emulate advertisement
    for rsw in rsws:
        rsw.advertise_route("10.0.1.0/24")
    for fsw in fsws:
        fsw.advertise_route("10.0.1.0/24")

    # simulate maintenance
    rsws[0].change_state("DRAIN")
    rsws[0].advertise_route("10.0.1.0/24")  # should not propagate

    # verify
    assert "10.0.1.0/24" not in rsws[0].routes_advertised
    print("Canary test passed: small pod simulation successful")

# Run all tests
if __name__ == "__main__":
    unit_test()
    emulation_test()
    canary_test()
