# 1500W Automated Antenna Tuner Project Design Log
### Revision 3.2 — Core Architecture & Peer-Review Corrections

### Section 1: System Topology & Antenna Balance
To safely interface the unbalanced 50-ohm output of the 1,500W amplifier with a 170-foot doublet antenna fed by 600-ohm ladder line, a standard unbalanced T-network output configuration **is rejected** due to high-Z reactive core saturation failures. 

The system will utilize an **Unbalanced T-Network mounted on an isolated, floating sub-deck**, paired with a heavy-duty **1:1 Guanella Current Balun (RF Choke) placed strictly on the stable 50-ohm input side**. This forces perfect common-mode isolation at a stable 50-ohm node before the signal enters the high-voltage tuning elements.

```
[50Ω Amp Input] ──► [Bruene Bridge] ──► [1:1 Input Current Balun] ──► [Floating T-Network Deck] ──► [600Ω Output]
```

### Section 2: Four-Chassis Enclosure Isolation Layout
To prevent slot-antenna leakage and protect low-voltage digital controls from extreme high-voltage RF fields, the cabinet layout has been expanded from two chambers to **four fully isolated compartments** partitioned by full-height 12-gauge metal walls:
1.  **Sampler Chamber:** Houses the low-loss 50-ohm Bruene bridge circuit.
2.  **Control Chamber:** Encloses the microcontroller, front-panel user interface controls, and screen.
3.  **Motor Chamber:** Houses the NEMA 17/23 stepper assemblies away from direct RF hot-zones.
4.  **RF Tank Chamber:** Houses the Jennings variables, Harris roller inductor, and high-voltage padding elements.

### Section 3: Material Sourcing & Cut List (Revised)

| Target Panel Component | Dimensions (Each) | Qty | Placement Role & Requirements | Material Type |
| :--- | :--- | :--- | :--- | :--- |
| **Chassis Floor (Base)** | **16" × 16"** | 1 | Main mounting plate for heavy RF components. | 12 Gauge (0.081") 5052-H32 |
| **Full-Height Partition Walls** | **16" × 10"** | **3** | Generates 4 distinct isolation bays. Continuous TIG seams. | 12 Gauge (0.081") 5052-H32 |
| **Front UI Panel Face** | **16" × 10"** | 1 | Screen and rotary control cutouts. | 14 Gauge (0.064") 5052-H32 |
| **Rear Connection Panel** | **16" × 10"** | 1 | Heavy bulkhead grounding and RF output blocks. | 14 Gauge (0.064") 5052-H32 |
| **Side Wall Panels** | **16" × 10"** | 2 | Left and right structural enclosure sides. | 14 Gauge (0.064") 5052-H32 |
| **Removable Lid (Top)** | **16" × 16"** | 1 | Access lid; fits tight against BeCu finger gaskets. | 14 Gauge (0.064") 5052-H32 |

#### Corrected Raw Material Ordering Stock
*   **12-Gauge Stock (0.081" thick):** **Order one (1) 24" × 36" sheet of 5052-H32 aluminum.** *(The previous 24"x24" sheet choice was geometrically short and failed to account for nesting layout drops required to cut the floor plus three 16"x10" internal walls)*.
*   **14-Gauge Stock (0.064" thick):** **Order one (1) 36" × 36" sheet of 5052-H32 aluminum.**
*   **Structural Frame Angle:** **Order 20 linear feet of 1" × 1" × 1/8" thick 6061-T6 aluminum angle stock.** *(Upgraded from 1/16" thin wall to prevent chassis flexing under heavy component loads)*.

### Section 4: High-Voltage Margin & Fixed Padding Upgrades
To safely utilize matching **Jennings UCSX 20–675 pF 10 kV variable capacitors** on both sides of the T-network, the variable units will be heavily protected by a **binary-weighted fixed padding array** (100 pF, 200 pF, and 400 pF steps). 
*   **The Constraint:** To maintain an 8 kV to 10 kV safety ceiling, the variable capacitors will be strictly forbidden from meshing past **75 pF on lower bands (80m/160m)**. High-capacitance loads will be carried exclusively by the padding array.
*   **Component Specification:** Padding capacitors must be **High-RF-Current Class 1 Ceramic Transmitting Doornob Capacitors (e.g., Centralab or Russian K15U series)** rated for a minimum of **15 kV Peak and 20–40 kVA of reactive power** to withstand severe circulating current heating.

### Section 5: Control Telemetry, Closed-Loop Tracking, & Thermal Design

*   **Closed-Loop Tracking:** Open-loop stepper counting is rejected. The motor chamber will interface with the RF tank via non-conductive Delrin shafts. Position feedback will be tracked natively via **12-bit SPI multi-turn absolute magnetic shaft encoders** mounted directly to the component side of the drive shaft, eliminating compliance and backlash errors.
*   **Limit Controls:** Dual heavy-duty **mechanical limit high/low microswitches** will be wired directly to the hardware motor driver enable pins to cut power instantly before the motor torque can crush the vacuum bellows or strip the roller inductor wheels.
*   **Chamber Filtering:** All signal and sensor lines crossing bulkheads will pass through **10,000 pF (0.01 µF) filtered feedthrough capacitors** paired with a **1 kΩ series carbon-resistor** at the analog-to-digital converters to create a high-rejection lowpass RC filter.
*   **Thermal Venting:** To vent up to 200W of inductive heat loss generated during high-Q low-band operations, the RF deck will feature cooling cutouts shielded with **hex-cell honeycomb EMI ventilation windows** to block HF radiation while maintaining high air velocity.
*   **Hardware PTT Safety Loop:** A high-speed vacuum relay's auxiliary contact is **hardwired directly in series with the amplifier's physical keying line**. If the microcontroller registers a limit switch fault, high SWR spike, or cabinet latch break, the hardware circuit drops the PTT loop instantly (< 2 ms) to prevent hot-switching arc destruction.
