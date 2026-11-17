# 1500W Automated Antenna Tuner Project Design Log

## 1. Electrical & Voltage Stress Specifications
At 1,500W PEP legal limit feeding a 170-foot doublet antenna via 600-ohm ladder line, internal voltages and currents vary significantly based on operating frequency and complex load impedance ($Z_{\\text{load}} = R \\pm jX$).

| Location / Parameter | Waveform Attribute | Low-Impedance Node | High-Impedance Node |
| :--- | :--- | :--- | :--- |
| **50-Ohm Input Side** (Bruene Bridge) | **RMS / Peak** | **274 V RMS / 387 V Peak** | **274 V RMS / 387 V Peak** |
| **50-Ohm Input Side** (Bruene Bridge) | **Current** | **5.5 A RMS / 7.7 A Peak** | **5.5 A RMS / 7.7 A Peak** |
| **Tuner Output & RF Hot Rails** | **RF Voltage (Peak)** | ~300 V to 500 V | **6,000 V to 9,500 V Peak** |
| **Roller Inductor / Cap Loop** | **RF Current (RMS)** | **15 A to 22 A RMS** (Avg: 10-18A) | ~1 A to 3 A RMS |

### Core Safety Risks:
* **Peak RF Voltage:** At high-impedance points, peak RF voltage surges to **6 kV – 9.5 kV**. Touch contact or close-proximity arcing across gaps (<0.5 inch) can cause lethal ventricular fibrillation and deep tissue RF burns that cook muscle and bone marrow from the inside out.
* **Peak RF Current:** Circulating current can reach **20 A to 25 A RMS** on extreme low-impedance bands. Any oxidation or weak contact on the roller inductor wheel will create massive localized ohmic heating, pitting, or arc flashes. It also induces strong eddy currents into nearby metal chassis walls if proper clearances are not maintained.

---

## 2. Updated Four-Chassis Architecture & Shielding Boundaries
The updated physical configuration maps out complete RF and low-voltage isolation boundaries across **four distinct internal chambers**, requiring an airtight-like **RF-tight Faraday cage** layout.

| Chamber Boundary Crossing | Wire / Connection Type Required | Pass-Through Component | Core Purpose / Hazard Prevented |
| :--- | :--- | :--- | :--- |
| **Sampler Chamber** $\\rightarrow$ **Control Chamber** | Standard insulated hookup wire (22 AWG). | **Feedthrough Capacitors** (1,000 pF) screwed/soldered into the sampler wall. | Blocks raw RF from riding the DC analog voltage lines straight into the microcontroller ADCs. |
| **Sampler Chamber** $\\rightarrow$ **RF Tuner Chamber** | Heavy, double-shielded coax (**RG-213 or RG-393 Teflon**). | Chassis-mount **SO-239 Bulkhead Barrel** connectors. | Encloses the 1,500W transmitter power completely in metal until it safely arrives at the first tuning capacitor. |
| **Control Chamber** $\\rightarrow$ **Motor Chamber** | **Shielded Twisted-Pair (STP)** control cable (4-conductor, 18-20 AWG with foil shield). | Grounded metal cable glands or **chassis-mount XLR/circular metal connectors**. | Prevents high-amplitude square-wave motor pulses from radiating digital noise into display logic or picking up stray RF. |
| **Motor Chamber** $\\rightarrow$ **RF Tuner Chamber** | **No Wires Allowed.** Use non-conductive **Delrin, fiberglass, or ceramic shafts**. | Tight-fitting **brass/aluminum chassis bushings** pressed into the metal partition wall. | Blocks the high-voltage RF in the tank deck from jumping onto the stepper motor casings and traveling back to your controller. |

---

## 3. Padded Output Stage Capacitor Topology (160m Optimization)
To allow the use of two matching **Jennings UCSX 20–675 pF 10 kV variable capacitors** side-by-side without arcing over at low-frequency/high-capacitance nodes, a padded array topology is integrated:
* **The Problem:** The 20–675 pF variable unit drops its breakdown rating from **10 kV down to 3 kV** when fully meshed out to its maximum 675 pF capacity.
* **The Solution:** A high-voltage vacuum relay (e.g., Kilovac HC-1 or Jennings RJ4B) switches a fixed-value high-voltage capacitor (such as a 200 pF or 300 pF mica or vacuum "bathtub" capacitor) in parallel on the lower bands (80m/160m).
* **The Benefit:** Keeps the primary 20-675 pF variable unmeshed (below 200 pF) where it retains its high **8 kV – 10 kV handling**, safely clearing the 6 kV to 9.5 kV peak output voltage nodes of the doublet antenna.
* **Switching Protocol:** Firmware must execute a strict **Break-Before-Make** sequence. The PTT interlock must open to drop the amplifier offline completely before the vacuum relay is ever allowed to switch contacts to prevent destructive hot-switching arcs.

---

## 4. Enclosure Materials & Master Cut List
* **Recommended Material:** **5052-H32 Aluminum Alloy**. Chosen for high weldability (TIG) and excellent formability (can be bent 90 degrees easily without fracturing or cracking like 6061-T6 alloy). 
* **TIG Welding Specs:** Use **5356 aluminum filler rod** to match the magnesium content of the 5052 alloy; protect with pure Argon gas with a 4-5 second post-flow setup.

The master enclosure dimensions are **16" Width × 16" Depth × 10" Height**.

### Sheet Metal Cut List
1. **Chassis Floor (Base Plate):** 16" × 16" | Qty: 1 | **12 Gauge (0.081") 5052-H32** (Prevents flexing from heavy vacuum caps/roller inductor)
2. **Internal Shield Partition:** 16" × 9.75" | Qty: 1 | **12 Gauge (0.081") 5052-H32** (Solid separator plate)
3. **Front UI Panel Face:** 16" × 10" | Qty: 1 | **14 Gauge (0.064") 5052-H32** (Hosts screen & manual controls)
4. **Rear Connection Panel:** 16" × 10" | Qty: 1 | **14 Gauge (0.064") 5052-H32** (Coax connectors, ground rods)
5. **Side Wall Panels:** 16" × 10" | Qty: 2 | **14 Gauge (0.064") 5052-H32** (Structural outer panels)
6. **Removable Top Lid:** 16" × 16" | Qty: 1 | **14 Gauge (0.064") 5052-H32** (Secured via security Torx screws)

### Raw Sheet Stock Order Quantities (Includes 35-40% Buffer for Errors)
* **12 Gauge (0.081") Stock:** One (1) sheet of 5052-H32 Aluminum, **24" × 24"** (2 ft × 2 ft)
* **14 Gauge (0.064") Stock:** One (1) sheet of 5052-H32 Aluminum, **36" × 36"** (3 ft × 3 ft)
* **Frame Stock:** **10 to 12 linear feet of 3/4" × 3/4" × 1/16" thick aluminum angle stock** for internal corner framing.

---

## 5. Front-Panel Control UI & Interface Layout
To provide real-time user monitoring and complete safety isolation from the front panel, an internal double-wall sub-chassis houses the digital logic:
* **Display Shielding:** An open cutout is avoided. A fine copper mesh window is sandwiched behind the panel screen cutout to maintain Faraday continuity.
* **Manual Overrides:** Control knobs utilize non-conductive plastic shafts or isolated Delrin shaft extensions connected to optical encoders.
* **Menu Architecture:**
  * *Tuning Monitor:* Real-time SWR ratio, Forward/Reflected PEP Wattage, current band/frequency, and step counts for Cap 1, Cap 2, and the Roller Inductor.
  * *Manual Override Mode:* Disengages PID loops; maps front rotary encoders directly to stepper motor pulses for manual tuning calibration.
  * *Utilities:* "Find Home" routine to reference motor limits; "Save Profile" option to commit optimal step coordinates to internal EEPROM.
