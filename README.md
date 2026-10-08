# 3D Bin Packing Studio (Factory & Warehouse Logistics)

A constraint-based 3D bin packing engine and modern interactive WebGL studio for warehouse logistics and container space optimization.

---

## 🚀 Key Features

1. **Modern Frontend (Pure HTML, CSS, & Vanilla JS)**:
   - High-DPI hardware-accelerated 3D viewport using **Three.js** and **OrbitControls**.
   - Professional dark enterprise UI designed for engineering and logistics workflows.
   - **Interactive Raycast Hover Cards**: Mouse over any 3D item to see exact dimensions, weight, volume, placement coordinates `(x, y, z)`, and safety badges (`Fragile`, `Stackable`, `Heavy`).
   - **Exploded View Slider**: Smoothly expand items outward from container centers to inspect internal and stacked items.
   - **Packing Sequence Animation**: Animated replay of items dropping into position in packing order with bounce easing.
   - **Multi-Container Tab Navigation**: Easily switch between containers with automated camera re-framing.

2. **Custom Inventory & Container Selection**:
   - Save and manage your custom **Objects (Items)** (name, dimensions, weight, 10 supported 3D shapes, fragility, stackability, rotatability).
   - Dynamic shape-aware dimension forms (Sphere asks for Diameter, Cube for Side Length, Torus for Major & Tube Radius, etc.).
   - Save and manage your custom **Containers** (name, dimensions, max weight capacity).
   - **Selective Packing**: Checkbox selection allowing you to pick specific objects for specific containers.
   - Quick one-click benchmark preset buttons (Presets 1 to 4).

3. **User Authentication & Database**:
   - Secure account registration & login with salted SHA-256 password hashing.
   - Users only see and manage their own saved objects and containers.
   - **Database Support**:
     - **MySQL**: Automatically connects to your local MySQL service (`MySQL80`). Configurable via environment variables.
     - **SQLite Fallback**: If MySQL credentials are not supplied, automatically falls back to local SQLite (`packing_studio.db`) with zero setup required.

4. **Algorithmic Engine (DSA Implementation)**:
   - In-place **Selection Sort** (Volume descending, Weight descending tie-breaker).
   - **Extreme-Point / Corner Candidate Generation** with deduplication.
   - **Multi-Constraint Verification**: Physical boundary checks, weight limits, 3D AABB non-overlap intersection detection, and structural support stability ($\ge 50\%$ footprint overlap on non-fragile, heavier bases).
   - **Greedy Best-Fit Multi-Container Strategy**: Minimizes residual bin volume.

---

## 💻 How to Run

Install dependencies:
```powershell
pip install -r requirements.txt
```

Start the application (starts the web server and automatically opens your browser):
```powershell
python main.py
```
*(Or alternatively run `python app.py`)*

Access the Studio at **[http://localhost:5000](http://localhost:5000)**.

---

## 🗄️ Database Configuration (Optional MySQL)

By default, the server connects to MySQL if root password is blank, or falls back to SQLite.
To connect to your specific MySQL installation, set environment variables in your terminal:

```powershell
$env:MYSQL_HOST = "localhost"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "your_mysql_password"
$env:MYSQL_DB = "bin_packing_db"
python main.py
```

---

## 📂 Project Structure

```
FODS Larp/
├── app.py                  # Flask server exposing REST APIs and static UI
├── database.py             # Database manager (MySQL with SQLite fallback & user auth)
├── models.py               # Domain models (Item, Container, Orientation) & physics
├── packer.py               # Packing engine (Selection sort, candidate generator, Best-Fit)
├── scenarios.py            # Benchmark test scenarios (Conditions 1-4)
├── requirements.txt        # Python package dependencies
├── FUT-TO-DO-CHANGES.MD    # Future constraints & dual-mode research
├── static/
│   ├── index.html          # Frontend Single-Page Application
│   ├── css/
│   │   └── style.css       # Enterprise dark theme stylesheet
│   └── js/
│       ├── app.js          # App state, auth, inventory CRUD, packing runner
│       └── visualizer3d.js # Three.js WebGL viewport, raycaster, exploded view
└── main.py                 # Web application launcher
```
