# Meta-Inspired Pod-Based Clos Data Center Fabric Simulation with BGP Automation

## Project Overview
In this project, I replicated **Meta’s pod-based Clos data center fabric** in a lab setting. The goal was to simulate a hyperscale data center where traffic is distributed efficiently across multiple racks and pods using **Anycast VIPs** and **ECMP load balancing**.

I implemented a **BGP underlay network** with:

- Uniform AS-numbering
- Hierarchical route summarization
- State-aware routing policies (**LIVE/WARM/DRAIN**)

The project also includes an **automation pipeline** for deploying pods and configuring BGP, as well as a **test framework** inspired by Meta’s **unit → emulation → canary pipeline** to verify routing correctness and resilience.

## Objectives
- Recreate a **3-plane Clos architecture** like Meta’s pods.
- Configure **BGP routing policies** to emulate real-world data center behavior.
- Enable **LIVE/WARM/DRAIN state changes** to simulate maintenance or failures.
- Automate deployment so new pods can be added quickly without manual intervention.
- Build a **test pipeline** to validate BGP stability and traffic forwarding.

## Architecture & Topology
The network is organized into three layers:

- **Spine Switches (SSW)** – Top-level aggregation (ASN 65401-65500)  
- **Fabric Switches (FSW)** – Intermediate layer within a pod (ASN 65301-65304)  
- **Rack/TOR Switches (RSW/TOR)** – Connect to servers (ASN 65201-65299)  

### IP Addressing Plan
- **Pod-based:** `100.podId.x.x`  
- **P2P links:**  
  - Spine ↔ Fabric: `100.podId.100.0/24`  
  - Fabric ↔ TOR: `100.podId.200.0/24`  
- **Rack networks:** `100.podId.1.0/24 → 100.podId.x.0/24`  

### Traffic Distribution
- Each TOR advertises the same **Anycast VIP**, allowing traffic to reach any pod.
- **ECMP** ensures traffic is evenly spread across RSW → FSW → SSW → VIP paths.

### Topology Outline
<img width="4096" height="3166" alt="image" src="https://github.com/user-attachments/assets/3307d4f7-fb6b-4af4-82c6-66194a7b65bc" />


- Each Spine connects to all Fabric switches.
- Each Fabric switch connects to all TORs in its pod.
- TORs connect to servers in their respective racks.

## BGP Policy Design & Planning

### Uniform AS Numbering
Each pod is treated as a **BGP confederation**, allowing reuse of AS numbers without conflicts:  
- Spine ASNs: 65401-65500 
- Fabric ASNs: 65301-65304
- TOR ASNs: 65201-65299 

This makes routing predictable and simplifies automation.

### Hierarchical Route Summarization
- TORs advertise per-rack prefixes.  
- Fabric switches aggregate rack prefixes into pod-level summaries.  
- Spine switches aggregate pod-level summaries per spine plane.  

This reduces FIB size and keeps the control plane efficient.

### State-Aware BGP Policies (LIVE/WARM/DRAIN)
- **LIVE:** Device is fully active, carries production traffic normally.  
- **WARM:** Transitional state; traffic is gradually shifted away but the device can still carry traffic if needed.  
- **DRAIN:** Device stops carrying production traffic; only infrastructure traffic is allowed.  

Policies are applied per VIP using **BGP communities**, so upstream devices adjust routing automatically.

## Automation Pipeline

### Pod Setup (podSetup.py)
- Automatically configures Spine, Fabric, and TOR switches.  
- Sets up BGP sessions, loopbacks, and eBGP multihop links.  
- Uses the ASN and IP plan described above.  
- Makes adding new pods fast and error-free.

### State Management (state_change.py)
- Handles **LIVE → DRAIN** and **DRAIN → LIVE** transitions with **WARM** as an intermediate step.  
- Automatically updates BGP community for the VIP and propagates it to all peers.  
- Ensures traffic shifts gracefully without disruption.

### Test & Emulation Framework (test_framework.py)
Inspired by Meta’s **unit → emulation → canary pipeline**, this framework validates configuration correctness and traffic behavior:  
- **Unit Tests:** Check BGP configuration correctness (ASN, neighbor IPs, loopbacks).  
- **Emulation:** Simulate traffic for VIPs and ensure upstream routing changes as expected when states change.  
- **Canary:** Change state for a single TOR/FSW and monitor ECMP and route propagation to ensure no disruption occurs.
