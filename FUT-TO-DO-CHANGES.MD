# Future Constraint Architecture & Industrial Research
## 3D Bin Packing Studio: Dual-Mode System Concept

This document records the comprehensive research on industry-standard packing, logistics, and warehousing constraints to guide future feature implementations.

---

## 1. System Architecture: Dual Startup Modes

When launching or creating a packing session, the user selects between two operational operating environments:

```text
                                [ Session Startup ]
                                         |
                +------------------------+------------------------+
                |                                                 |
                v                                                 v
   [ MODE A: TRUCK & LOGISTICS ]                     [ MODE B: FACTORY & WAREHOUSE ]
   • Dynamic In-Transit Forces                       • Static Stationary Storage
   • Multi-Drop Delivery (LIFO)                      • Facility Safety & Fire Codes
   • Axle Loads & CoG Balancing                      • Floor & Rack Bay Limits
   • Inertial Cargo Restraints                       • Long-Term Compressive Creep
```

---

## 2. Mode A: Truck & Logistics Constraints (Dynamic Transit)

Governed by transportation safety regulations (**DOT / FMCSA**, **ISO 1496**, **IMO / IMDG**, **EN 12195**).

### 2.1 Multi-Stop Unloading Sequence (LIFO Accessibility)
* **Standard:** Last-In, First-Out (LIFO) Delivery Routing.
* **Mechanism:** 
  * Each cargo item is assigned a `destination_stop` ($1, 2, 3 \dots$).
  * Cargo destined for Stop 1 must have an unobstructed, direct line of extraction to the rear trailer door without requiring relocation of items destined for Stops 2 or 3.
  * In mathematical modeling: Evaluated via raycast reachability or topological DAG (Directed Acyclic Graph) of blocking items along the longitudinal vehicle axis.

### 2.2 Axle Load Distribution & Legal Gross Limits
* **Standard:** Federal Bridge Gross Weight Formula (23 CFR § 658.17) / EU Directive 96/53/EC.
* **Mechanism:**
  * Total weight is partitioned between steer axle, drive tandem, and trailer tandem.
  * Over-the-road enforcement can fine or impound vehicles if an individual axle is overloaded, even if total gross weight is well below legal maximums.
  * Packing engine computes moment equilibrium about kingpin and trailer bogie pivot points.

### 2.3 Center of Gravity (CoG) & Lateral Rollover Stability
* **Standard:** ISO 1496-1 / NHTSA Heavy Vehicle Rollover Threshold.
* **Mechanism:**
  * Transverse (Left-to-Right) CoG must remain within $\pm 5\%$ of the trailer centerline.
  * Vertical CoG must remain below a safe geometric threshold to prevent vehicle rollovers during emergency braking or highway exit ramp maneuvers.

### 2.4 Dynamic Inertial Restraint & Void Filling
* **Standard:** EN 12195-1 (Cargo securing design forces: $0.8g$ forward, $0.5g$ lateral, $0.5g$ rearward).
* **Mechanism:**
  * Unlike static rooms, moving trucks experience sharp forward acceleration during hard braking.
  * Voids between cargo blocks must be zero or bridged using dunnage airbags/bulkheads to prevent cargo avalanches.

### 2.5 Directional "This Side Up" Orientation Locking
* **Standard:** ASTM D5276 / ISO 780 Symbol 0623.
* **Mechanism:**
  * Liquid drums, compressors, electronics, and hazardous chemicals cannot be pitched or rolled onto their side.
  * Only Yaw rotation (horizontal rotation around the vertical axis) is permitted (2 valid orientations instead of 6).

### 2.6 Cylindrical Rolling & Chocking Restraints
* **Standard:** 49 CFR § 393.106 (Cargo Securement Rules for Cylinders and Coils).
* **Mechanism:**
  * Items with round profiles lying on their curved surface will roll under transit vibration unless nested in cradles or flanked tightly by adjacent rectangular items.

### 2.7 Hazardous Materials (HAZMAT) Segregation
* **Standard:** IMDG Code Segregation Tables / 49 CFR Part 177.
* **Mechanism:**
  * Items tagged with incompatible hazard classes (e.g., Class 3 Flammables vs. Class 5.1 Oxidizers, or Toxics vs. Food Grade) cannot share the same compartment or must observe mandatory physical standoff distances.

### 2.8 Multi-Temperature Bulkhead Partitions
* **Standard:** ATP Agreement for Perishable Foodstuffs Transport.
* **Mechanism:**
  * Multi-zone reefer trailers require separation of Frozen ($-18^\circ\text{C}$), Chilled ($+4^\circ\text{C}$), and Ambient goods using insulated internal divider walls.

---

## 3. Mode B: Factory & Warehouse Constraints (Static Storage)

Governed by facility safety codes (**RMI ANSI MH16.1**, **NFPA 13**, **OSHA**, **NIOSH**).

### 3.1 Long-Term Compressive Creep & Top-Load Limits
* **Standard:** ASTM D642 (Box Compression Test / BCT) with Safety Factor $SF \ge 3.0$–$5.0$.
* **Mechanism:**
  * Warehouse storage lasts months rather than days. Under sustained static load and fluctuating ambient relative humidity, paperboard/corrugated packaging experiences viscoelastic creep deformation, losing over $50\%$ of structural strength over 90 days.
  * Each item has a maximum static top load: $\sum W_{\text{above}} \le \text{MaxStaticTopLoad}$.

### 3.2 Ceiling & Fire Sprinkler Clearance Buffers
* **Standard:** NFPA 13 (Standard for the Installation of Sprinkler Systems, Chapter 12).
* **Mechanism:**
  * Storage stacks must maintain a mandatory clearance buffer of at least **18 inches (0.45 m)**—or **36 inches (0.90 m)** for dense, high-hazard commodities—below the lowest ceiling sprinkler head to permit proper water spray dispersal.

### 3.3 Picking Velocity & Accessibility (ABC Inventory Classification)
* **Standard:** Lean Warehousing / WMS Velocity Zoning.
* **Mechanism:**
  * High-turnover goods (**Class A**) must be positioned on bottom tiers and near front access faces for fast picking.
  * Medium-turnover (**Class B**) and slow/bulk storage (**Class C**) can be stacked higher or stored deeper.

### 3.4 Pallet Overhang Prohibition
* **Standard:** ISO 6780 / GMA Pallet Dimensions ($1200 \times 800\text{ mm}$ EUR or $48 \times 40\text{ in}$ GMA).
* **Mechanism:**
  * Packages must not overhang the perimeter of standard wooden pallets.
  * An overhang of just $1\text{ cm}$ decreases box compression resistance by **$20\text{–}32\%$** and risks catching on warehouse racking uprights during forklift retrieval.

### 3.5 Manual Material Handling & Ergonomic Golden Zone
* **Standard:** NIOSH Manual Material Handling (MMH) Equation / OSHA Ergonomic Guidelines.
* **Mechanism:**
  * Packages heavier than $15\text{–}20\text{ kg}$ intended for manual handling must not be placed above shoulder height ($> 1.4\text{ m}$) or below knuckle height ($< 0.4\text{ m}$).

### 3.6 Forklift & Pallet Jack Entry Pockets
* **Standard:** ASME B56.1 (Safety Standard for Powered Industrial Trucks).
* **Mechanism:**
  * Base layers or skid units must maintain standard fork opening clearances ($100\text{ mm}$ vertical clearance, $600\text{ mm}$ minimum span) to allow lifting without puncturing packaging.

### 3.7 Floor Slab & Rack Bay Weight Limits
* **Standard:** RMI Specification for the Design, Testing and Utilization of Industrial Steel Storage Racks.
* **Mechanism:**
  * Total combined load must respect structural floor slab load limits ($kN/\text{m}^2$) and beam deflection thresholds ($L / 180$).

### 3.8 Secondary Spill Containment & Bunding
* **Standard:** EPA 40 CFR 264.175 / OSHA 1910.106.
* **Mechanism:**
  * Chemical drums or liquid IBC totes must be positioned over certified sump containment pallets capable of holding $100\%$ of the largest single container or $10\%$ of total aggregate volume.

---

## 4. Side-by-Side Comparison Matrix

| Dimension / Parameter | Mode A: Truck & Logistics | Mode B: Factory & Warehouse |
| :--- | :--- | :--- |
| **Operational Setting** | Moving vehicle over public roadways | Stationary storage inside facility |
| **Primary Danger** | Inertial shifting, rollover, bridge weight fines | Box buckling, fire sprinkler blockage, picker strain |
| **Height Boundary (Z-Axis)** | Fixed trailer interior ceiling ($2.6\text{–}2.8\text{ m}$) | Clear ceiling height minus **18–36 inch NFPA buffer** |
| **Weight Balancing** | Axle load limits (Steer / Drive / Trailer) + Transverse CoG | Floor slab load ($kN/\text{m}^2$) & beam capacity |
| **Accessibility Driver** | **LIFO Stop Order** relative to back cargo door | **ABC Velocity** relative to ground / aisle picker line |
| **Stacking Strength Rating** | Dynamic transport load ($SF \approx 1.5\times$) | Long-duration static creep ($SF \approx 3.0\times\text{–}5.0\times$) |
| **Void Tolerance** | **Zero void preference** (tight bracing to prevent movement) | **Aisle/clearance voids mandatory** (for forklift/human access) |
| **Pallet Boundary** | Wall-to-wall loading inside trailer ($2.45\text{ m}$) | Strictly zero overhang outside pallet footprint ($1.2 \times 0.8\text{ m}$) |
| **Orientation Freedom** | Strictly bounded by "This Side Up" & roll inertia | Flexible, bounded by forklift tines / pallet orientation |

---

## 5. Universal Physical Baseline (Common to Both Modes)

Regardless of operational mode, the fundamental 3D packing engine maintains these hard physical laws:

1. **Geometric Containment:** $\forall i, \quad x_i + L_i \le L_C, \quad y_i + W_i \le W_C, \quad z_i + H_i \le H_C$.
2. **Axis-Aligned Non-Overlapping (AABB):** No two physical bounding boxes can overlap in 3D space.
3. **Gravity & Grounding Support:** Every item must rest on the container floor/pallet or maintain a minimum contact area on top surfaces directly beneath it.

---

## 6. Recommended Future Implementation Roadmap

When ready to implement, proceed in this priority sequence:

### Phase 1: High-ROI Engineering Rules
- [ ] **Dual-Mode Startup Toggle:** Allow selecting "Truck Transport" or "Warehouse Storage" on session creation.
- [ ] **Top-Load Bearing Limit (kg):** Replace binary fragile/stackable flags with numerical top-load resistance.
- [ ] **"This Side Up" Orientation Lock:** Allow 2-way Yaw rotation while prohibiting Pitch and Roll.
- [ ] **Minimum Base Support Area Ratio:** Require $\ge 75\%$ contact support to eliminate visually unrealistic overhangs.

### Phase 2: Logistics & Facility Specific Rules
- [ ] **Truck Mode:** Implement LIFO multi-stop route accessibility check.
- [ ] **Truck Mode:** Implement Center of Gravity (CoG) envelope calculation.
- [ ] **Warehouse Mode:** Implement NFPA fire sprinkler ceiling clearance buffer.
- [ ] **Warehouse Mode:** Implement Pallet zero-overhang enforcement.

### Phase 3: Advanced Regulatory Rules
- [ ] **Truck Mode:** Axle load moment calculation.
- [ ] **Truck Mode:** IMDG / DOT HAZMAT segregation compatibility matrix.
- [ ] **Warehouse Mode:** NIOSH manual lifting ergonomic height limit.

