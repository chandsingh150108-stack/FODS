"""Flask web server exposing REST APIs for bin packing management and 3D visualization.

Endpoints:
- User Authentication (Login, Register, Session check)
- Objects / Items Inventory CRUD
- Containers Inventory CRUD
- Simulation Runner (/api/pack) linking domain models & PackingEngine
- Static UI Serving (Pure HTML/CSS/JS frontend)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory, session

from database import db
from models import Container, Item
from packer import PackingEngine
from scenarios import ScenarioRepository

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "bin-packing-secret-key-3d-fods-larp-2026")


# -------------------------------------------------------------
# Auth Helper
# -------------------------------------------------------------
def get_current_user_id() -> int | None:
    """Extract user_id from session or Authorization header."""
    user_id = session.get("user_id")
    if user_id:
        return int(user_id)
    # Check Bearer token (user_id as simple token for demo or header)
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            return int(token)
        except ValueError:
            return None
    return None


# -------------------------------------------------------------
# Frontend Route
# -------------------------------------------------------------
@app.route("/")
def index():
    """Serve the single-page application."""
    return send_from_directory("static", "index.html")


# -------------------------------------------------------------
# Authentication API
# -------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user_id = db.register_user(username, password)
    if not user_id:
        return jsonify({"error": "Username is already taken"}), 409

    session["user_id"] = user_id
    session["username"] = username
    return jsonify({"token": str(user_id), "user": {"id": user_id, "username": username}})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = db.authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"token": str(user["id"]), "user": user})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/me", methods=["GET"])
def me():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user_id": uid, "username": session.get("username", "User")})


# -------------------------------------------------------------
# Objects (Items) API
# -------------------------------------------------------------
@app.route("/api/objects", methods=["GET"])
def list_objects():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401
    objects = db.get_objects(uid)
    return jsonify(objects)


@app.route("/api/objects", methods=["POST"])
def create_object():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Object name is required"}), 400

    try:
        length = float(data.get("length", 1.0))
        width = float(data.get("width", 1.0))
        height = float(data.get("height", 1.0))
        weight = float(data.get("weight", 1.0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric dimensions or weight"}), 400

    shape = data.get("shape", "cuboid")
    fragile = bool(data.get("fragile", False))
    stackable = bool(data.get("stackable", True))
    rotatable = bool(data.get("rotatable", True))

    obj_id = db.create_object(
        user_id=uid,
        name=name,
        length=length,
        width=width,
        height=height,
        weight=weight,
        shape=shape,
        fragile=fragile,
        stackable=stackable,
        rotatable=rotatable,
    )
    return jsonify({"id": obj_id, "success": True}), 201


@app.route("/api/objects/<int:obj_id>", methods=["DELETE"])
def delete_object(obj_id: int):
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401
    success = db.delete_object(uid, obj_id)
    return jsonify({"success": success})


# -------------------------------------------------------------
# Containers API
# -------------------------------------------------------------
@app.route("/api/containers", methods=["GET"])
def list_containers():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401
    containers = db.get_containers(uid)
    return jsonify(containers)


@app.route("/api/containers", methods=["POST"])
def create_container():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Container name is required"}), 400

    try:
        length = float(data.get("length", 10.0))
        width = float(data.get("width", 10.0))
        height = float(data.get("height", 10.0))
        max_weight = float(data.get("max_weight", 100.0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric dimensions or max weight"}), 400

    c_id = db.create_container(
        user_id=uid,
        name=name,
        length=length,
        width=width,
        height=height,
        max_weight=max_weight,
    )
    return jsonify({"id": c_id, "success": True}), 201


@app.route("/api/containers/<int:c_id>", methods=["DELETE"])
def delete_container(c_id: int):
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401
    success = db.delete_container(uid, c_id)
    return jsonify({"success": success})


# -------------------------------------------------------------
# Reset / Load Presets API
# -------------------------------------------------------------
@app.route("/api/presets/load", methods=["POST"])
def load_preset():
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    condition_num = int(data.get("condition", 1))

    if condition_num == 1:
        scenario = ScenarioRepository.get_test_condition_one()
    elif condition_num == 2:
        scenario = ScenarioRepository.get_test_condition_two()
    elif condition_num == 3:
        scenario = ScenarioRepository.get_test_condition_three()
    else:
        scenario = ScenarioRepository.get_test_condition_four()

    # Save to user inventory
    for c in scenario.containers:
        db.create_container(uid, f"Preset {c.id} ({c.length}x{c.width}x{c.height})", c.length, c.width, c.height, c.maximum_weight)
    for it in scenario.items:
        db.create_object(uid, it.name, it.length, it.width, it.height, it.weight, it.shape, it.fragile, it.stackable, it.rotatable)

    return jsonify({"success": True, "message": f"Loaded {scenario.name}"})


# -------------------------------------------------------------
# 3D Packing Simulation API
# -------------------------------------------------------------
@app.route("/api/pack", methods=["POST"])
def run_packing():
    """Run the 3D packing engine on the user's selected objects and container(s)."""
    uid = get_current_user_id()
    if not uid:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    selected_object_ids = data.get("object_ids", [])
    selected_container_ids = data.get("container_ids", [])

    all_objects = db.get_objects(uid)
    all_containers = db.get_containers(uid)

    # Filter objects and containers
    target_objects = [
        obj for obj in all_objects
        if not selected_object_ids or obj["id"] in selected_object_ids
    ]
    target_containers = [
        c for c in all_containers
        if not selected_container_ids or c["id"] in selected_container_ids
    ]

    if not target_containers:
        return jsonify({"error": "Please select at least one container."}), 400
    if not target_objects:
        return jsonify({"error": "Please select at least one object to pack."}), 400

    # Instantiate domain models
    containers: List[Container] = []
    for c in target_containers:
        containers.append(
            Container(
                id=c["id"],
                length=float(c["length"]),
                width=float(c["width"]),
                height=float(c["height"]),
                maximum_weight=float(c["max_weight"]),
            )
        )

    items: List[Item] = []
    for it in target_objects:
        items.append(
            Item(
                id=it["id"],
                name=it["name"],
                length=float(it["length"]),
                width=float(it["width"]),
                height=float(it["height"]),
                weight=float(it["weight"]),
                shape=it["shape"],
                fragile=bool(it["fragile"]),
                stackable=bool(it["stackable"]),
                rotatable=bool(it["rotatable"]),
            )
        )

    # Execute packing algorithm
    engine = PackingEngine()
    engine.pack(containers, items, verbose=False)

    # Format result for 3D visualization
    packed_containers: List[Dict[str, Any]] = []
    for c in containers:
        placed_items = []
        for it in c.packed_items:
            placed_items.append(
                {
                    "id": it.id,
                    "name": it.name,
                    "length": it.packed_length,
                    "width": it.packed_width,
                    "height": it.packed_height,
                    "weight": it.weight,
                    "shape": it.shape,
                    "fragile": it.fragile,
                    "stackable": it.stackable,
                    "volume": round(it.volume, 2),
                    "x": it.x,
                    "y": it.y,
                    "z": it.z,
                }
            )

        packed_containers.append(
            {
                "id": c.id,
                "name": next((tc["name"] for tc in target_containers if tc["id"] == c.id), f"Container {c.id}"),
                "length": c.length,
                "width": c.width,
                "height": c.height,
                "max_weight": c.maximum_weight,
                "used_weight": round(c.used_weight, 2),
                "total_volume": round(c.total_volume, 2),
                "used_volume": round(c.used_volume, 2),
                "utilization": round(c.utilization_percentage, 2),
                "items": placed_items,
            }
        )

    unpacked_list = [
        {
            "id": it.id,
            "name": it.name,
            "weight": it.weight,
            "shape": it.shape,
            "dimensions": f"{it.length} x {it.width} x {it.height}",
            "reason": "Exceeds dimensions, weight limit, or support constraint.",
        }
        for it in items
        if not it.packed
    ]

    total_packed = sum(len(c.packed_items) for c in containers)
    avg_util = (
        sum(c.utilization_percentage for c in containers) / len(containers)
        if containers
        else 0.0
    )

    return jsonify(
        {
            "success": True,
            "containers": packed_containers,
            "unpacked_items": unpacked_list,
            "summary": {
                "total_items": len(items),
                "packed_count": total_packed,
                "unpacked_count": len(unpacked_list),
                "containers_used": sum(1 for c in containers if len(c.packed_items) > 0),
                "average_utilization": round(avg_util, 2),
            },
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f" 3D Bin Packing Studio Web Server")
    print(f" -> http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)

