"""Database abstraction layer supporting MySQL and SQLite fallback.

Manages persistent storage for:
- User accounts & credentials (secure password hashing)
- Saved factory items / objects
- Saved warehouse containers

Attempts to connect to MySQL first (configurable via environment variables).
If MySQL credentials are not provided or unavailable, seamlessly uses SQLite.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """Handles database connections, migrations, and CRUD operations."""

    def __init__(self) -> None:
        self.db_type = "sqlite"
        self.mysql_conn = None
        self._init_connection()
        self._create_tables()

    def _init_connection(self) -> None:
        """Attempt connection to MySQL; fallback to SQLite if unavailable."""
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_user = os.environ.get("MYSQL_USER", "root")
        mysql_password = os.environ.get("MYSQL_PASSWORD", "")
        mysql_db = os.environ.get("MYSQL_DB", "bin_packing_db")

        # Try MySQL if pymysql is installed and credentials work
        try:
            import pymysql

            # First connect to server to ensure database exists
            temp_conn = pymysql.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                autocommit=True,
                connect_timeout=2,
            )
            with temp_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_db}`")
            temp_conn.close()

            # Connect to specific database
            self.mysql_conn = pymysql.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_db,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
            self.db_type = "mysql"
            print(f"[Database] Connected to MySQL database '{mysql_db}' successfully.")
            return
        except Exception as e:
            # Fallback to local SQLite database
            self.db_type = "sqlite"
            self.sqlite_path = os.path.abspath("packing_studio.db")
            print(f"[Database] MySQL not available ({e}). Using local SQLite storage at: {self.sqlite_path}")

    def get_connection(self) -> Any:
        """Get an active database connection."""
        if self.db_type == "mysql" and self.mysql_conn:
            self.mysql_conn.ping(reconnect=True)
            return self.mysql_conn
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self) -> None:
        """Create necessary tables if they do not exist."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS objects (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        name VARCHAR(150) NOT NULL,
                        length FLOAT NOT NULL,
                        width FLOAT NOT NULL,
                        height FLOAT NOT NULL,
                        weight FLOAT NOT NULL,
                        shape VARCHAR(50) DEFAULT 'cuboid',
                        fragile BOOLEAN DEFAULT FALSE,
                        stackable BOOLEAN DEFAULT TRUE,
                        rotatable BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS containers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        name VARCHAR(150) NOT NULL,
                        length FLOAT NOT NULL,
                        width FLOAT NOT NULL,
                        height FLOAT NOT NULL,
                        max_weight FLOAT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
        else:
            conn = self.get_connection()
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS objects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        length REAL NOT NULL,
                        width REAL NOT NULL,
                        height REAL NOT NULL,
                        weight REAL NOT NULL,
                        shape TEXT DEFAULT 'cuboid',
                        fragile INTEGER DEFAULT 0,
                        stackable INTEGER DEFAULT 1,
                        rotatable INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS containers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        length REAL NOT NULL,
                        width REAL NOT NULL,
                        height REAL NOT NULL,
                        max_weight REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
            conn.close()

    # -------------------------------------------------------------
    # Password Hashing Helpers
    # -------------------------------------------------------------
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with a salt."""
        salt = secrets.token_hex(16)
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"{salt}:{h}"

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        """Verify password against stored salt:hash."""
        try:
            salt, h = stored_hash.split(":", 1)
            candidate = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
            return secrets.compare_digest(h, candidate)
        except Exception:
            return False

    # -------------------------------------------------------------
    # User Authentication
    # -------------------------------------------------------------
    def register_user(self, username: str, password: str) -> Optional[int]:
        """Register a new user account. Returns user_id or None if taken."""
        username = username.strip()
        if not username or not password:
            return None

        pwd_hash = self.hash_password(password)

        if self.db_type == "mysql":
            conn = self.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                        (username, pwd_hash),
                    )
                    user_id = cur.lastrowid
                self.seed_user_defaults(user_id)
                return user_id
            except Exception:
                return None
        else:
            conn = self.get_connection()
            try:
                with conn:
                    cur = conn.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, pwd_hash),
                    )
                    user_id = cur.lastrowid
                conn.close()
                self.seed_user_defaults(user_id)
                return user_id
            except sqlite3.IntegrityError:
                conn.close()
                return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username and password; returns user dict or None."""
        username = username.strip()
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = %s",
                    (username,),
                )
                user = cur.fetchone()
                if user and self.verify_password(user["password_hash"], password):
                    return {"id": user["id"], "username": user["username"]}
                return None
        else:
            conn = self.get_connection()
            cur = conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            )
            row = cur.fetchone()
            conn.close()
            if row and self.verify_password(row["password_hash"], password):
                return {"id": row["id"], "username": row["username"]}
            return None

    def seed_user_defaults(self, user_id: int) -> None:
        """Seed initial factory objects and containers for new users."""
        default_containers = [
            ("Standard Warehouse Bay (12x10x10m)", 12.0, 10.0, 10.0, 200.0),
            ("Compact Bay (8x8x8m)", 8.0, 8.0, 8.0, 100.0),
        ]
        default_items = [
            ("Industrial Motor (Cuboid)", 5.0, 4.0, 3.0, 20.0, "cuboid", False, True, True),
            ("Steel Housing (Cube)", 3.0, 3.0, 3.0, 18.0, "cube", False, True, True),
            ("Pressure Cylinder", 3.0, 3.0, 4.0, 15.0, "cylinder", False, True, True),
            ("Storage Sphere", 3.0, 3.0, 3.0, 12.0, "sphere", False, False, True),
            ("Loading Ramp (Wedge)", 4.0, 3.0, 2.0, 14.0, "wedge", False, True, True),
            ("Structural Pyramid", 3.0, 3.0, 3.0, 11.0, "pyramid", False, False, True),
            ("Hexagonal Drum (Hex Prism)", 3.0, 3.0, 4.0, 16.0, "hexagonal_prism", False, True, True),
            ("Gas Canister (Capsule)", 2.0, 2.0, 4.0, 10.0, "capsule", False, False, True),
            ("Cable Spool (Torus)", 4.0, 4.0, 2.0, 13.0, "torus", False, True, True),
            ("Insulated Panel (Flat)", 4.0, 3.0, 0.5, 8.0, "flat", False, True, True),
            ("Precision Control Box", 4.0, 3.0, 2.0, 10.0, "cuboid", True, False, True),
        ]

        for name, l, w, h, mw in default_containers:
            self.create_container(user_id, name, l, w, h, mw)

        for name, l, w, h, wt, shape, fragile, stack, rot in default_items:
            self.create_object(user_id, name, l, w, h, wt, shape, fragile, stack, rot)

    # -------------------------------------------------------------
    # Objects (Items) CRUD
    # -------------------------------------------------------------
    def get_objects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all saved objects for a user."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM objects WHERE user_id = %s ORDER BY id ASC",
                    (user_id,),
                )
                items = cur.fetchall()
                # Cast booleans
                for it in items:
                    it["fragile"] = bool(it["fragile"])
                    it["stackable"] = bool(it["stackable"])
                    it["rotatable"] = bool(it["rotatable"])
                return items
        else:
            conn = self.get_connection()
            cur = conn.execute(
                "SELECT * FROM objects WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            )
            rows = [dict(row) for row in cur.fetchall()]
            conn.close()
            for r in rows:
                r["fragile"] = bool(r["fragile"])
                r["stackable"] = bool(r["stackable"])
                r["rotatable"] = bool(r["rotatable"])
            return rows

    def create_object(
        self,
        user_id: int,
        name: str,
        length: float,
        width: float,
        height: float,
        weight: float,
        shape: str = "cuboid",
        fragile: bool = False,
        stackable: bool = True,
        rotatable: bool = True,
    ) -> int:
        """Create a new item in user's inventory."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO objects (user_id, name, length, width, height, weight, shape, fragile, stackable, rotatable)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, name, length, width, height, weight, shape, fragile, stackable, rotatable),
                )
                return cur.lastrowid
        else:
            conn = self.get_connection()
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO objects (user_id, name, length, width, height, weight, shape, fragile, stackable, rotatable)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        name,
                        length,
                        width,
                        height,
                        weight,
                        shape,
                        1 if fragile else 0,
                        1 if stackable else 0,
                        1 if rotatable else 0,
                    ),
                )
                obj_id = cur.lastrowid
            conn.close()
            return obj_id

    def delete_object(self, user_id: int, object_id: int) -> bool:
        """Delete an object belonging to user."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM objects WHERE id = %s AND user_id = %s", (object_id, user_id))
                return cur.rowcount > 0
        else:
            conn = self.get_connection()
            with conn:
                cur = conn.execute("DELETE FROM objects WHERE id = ? AND user_id = ?", (object_id, user_id))
                count = cur.rowcount
            conn.close()
            return count > 0

    # -------------------------------------------------------------
    # Containers CRUD
    # -------------------------------------------------------------
    def get_containers(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all saved containers for a user."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM containers WHERE user_id = %s ORDER BY id ASC",
                    (user_id,),
                )
                return cur.fetchall()
        else:
            conn = self.get_connection()
            cur = conn.execute(
                "SELECT * FROM containers WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            )
            rows = [dict(row) for row in cur.fetchall()]
            conn.close()
            return rows

    def create_container(
        self,
        user_id: int,
        name: str,
        length: float,
        width: float,
        height: float,
        max_weight: float,
    ) -> int:
        """Create a new container for user."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO containers (user_id, name, length, width, height, max_weight)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, name, length, width, height, max_weight),
                )
                return cur.lastrowid
        else:
            conn = self.get_connection()
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO containers (user_id, name, length, width, height, max_weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, name, length, width, height, max_weight),
                )
                c_id = cur.lastrowid
            conn.close()
            return c_id

    def delete_container(self, user_id: int, container_id: int) -> bool:
        """Delete a container belonging to user."""
        if self.db_type == "mysql":
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM containers WHERE id = %s AND user_id = %s", (container_id, user_id))
                return cur.rowcount > 0
        else:
            conn = self.get_connection()
            with conn:
                cur = conn.execute("DELETE FROM containers WHERE id = ? AND user_id = ?", (container_id, user_id))
                count = cur.rowcount
            conn.close()
            return count > 0


# Global singleton
db = DatabaseManager()

