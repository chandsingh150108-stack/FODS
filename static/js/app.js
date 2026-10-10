/**
 * App.js: Application state, authentication, inventory CRUD, and simulation trigger.
 */

class App {
  constructor() {
    this.currentUser = null;
    this.token = localStorage.getItem('packing_auth_token') || null;

    this.objects = [];
    this.containers = [];

    this.selectedObjectIds = new Set();
    this.selectedContainerIds = new Set();

    this.activeTab = 'objects';
    this.visualizer = null;

    this.init();
  }

  async init() {
    // Initialize 3D Viewport
    this.visualizer = new Visualizer3D('canvas-3d');
    window.visualizer3d = this.visualizer;

    this.bindEvents();
    await this.checkAuth();
  }

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  // -------------------------------------------------------------
  // Authentication
  // -------------------------------------------------------------
  async checkAuth() {
    try {
      const res = await fetch('/api/auth/me', { headers: this.getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        this.currentUser = { id: data.user_id, username: data.username };
        this.updateAuthUi();
        await this.loadInventory();
        // Auto-pack on initial load
        setTimeout(() => this.runPacking(), 300);
      } else {
        this.showAuthModal(true);
      }
    } catch (e) {
      this.showAuthModal(true);
    }
  }

  updateAuthUi() {
    const authBtn = document.getElementById('btn-nav-auth');
    const userBadge = document.getElementById('user-badge');
    const userNameEl = document.getElementById('nav-username');

    if (this.currentUser) {
      authBtn.style.display = 'none';
      userBadge.style.display = 'flex';
      userNameEl.innerText = this.currentUser.username;
    } else {
      authBtn.style.display = 'block';
      userBadge.style.display = 'none';
    }
  }

  showAuthModal(show = true) {
    const modal = document.getElementById('auth-modal');
    if (show) modal.classList.add('active');
    else modal.classList.remove('active');
  }

  async handleLogin(username, password) {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');

      this.token = data.token;
      localStorage.setItem('packing_auth_token', this.token);
      this.currentUser = data.user;
      this.updateAuthUi();
      this.showAuthModal(false);
      await this.loadInventory();
      this.runPacking();
    } catch (err) {
      alert(err.message);
    }
  }

  async handleRegister(username, password) {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Registration failed');

      this.token = data.token;
      localStorage.setItem('packing_auth_token', this.token);
      this.currentUser = data.user;
      this.updateAuthUi();
      this.showAuthModal(false);
      await this.loadInventory();
      this.runPacking();
    } catch (err) {
      alert(err.message);
    }
  }

  logout() {
    localStorage.removeItem('packing_auth_token');
    this.token = null;
    this.currentUser = null;
    this.updateAuthUi();
    this.showAuthModal(true);
  }

  // -------------------------------------------------------------
  // Inventory (Objects & Containers)
  // -------------------------------------------------------------
  async loadInventory() {
    if (!this.currentUser) return;
    try {
      const [objRes, conRes] = await Promise.all([
        fetch('/api/objects', { headers: this.getAuthHeaders() }),
        fetch('/api/containers', { headers: this.getAuthHeaders() }),
      ]);

      if (objRes.ok) this.objects = await objRes.json();
      if (conRes.ok) this.containers = await conRes.json();

      // By default select all objects and first container if none selected
      if (this.selectedObjectIds.size === 0) {
        this.objects.forEach(o => this.selectedObjectIds.add(o.id));
      }
      if (this.selectedContainerIds.size === 0 && this.containers.length > 0) {
        this.selectedContainerIds.add(this.containers[0].id);
      }

      this.renderObjectsList();
      this.renderContainersList();
      this.updateSelectionSummary();
    } catch (e) {
      console.error('Error loading inventory:', e);
    }
  }

  renderObjectsList() {
    const listEl = document.getElementById('objects-list');
    const badgeEl = document.getElementById('badge-objects-count');
    if (!listEl) return;
    listEl.innerHTML = '';
    if (badgeEl) badgeEl.innerText = this.objects.length;

    if (this.objects.length === 0) {
      listEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 30px;">No objects found. Click "+ Add Object" above.</div>`;
      return;
    }

    this.objects.forEach(obj => {
      const isSelected = this.selectedObjectIds.has(obj.id);
      const card = document.createElement('div');
      card.className = `inventory-card ${isSelected ? 'selected' : ''}`;
      card.onclick = (e) => {
        if (e.target.closest('.btn-delete')) return;
        this.toggleObjectSelection(obj.id);
      };

      card.innerHTML = `
        <div class="card-header">
          <div class="card-title-group">
            <input type="checkbox" class="custom-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); window.app.toggleObjectSelection(${obj.id})">
            <span class="card-title">${obj.name}</span>
          </div>
          <button class="btn-delete" title="Delete object" onclick="window.app.deleteObject(${obj.id})">✕</button>
        </div>
        <div class="card-specs">
          <div class="spec-item">Size: <span>${obj.length}x${obj.width}x${obj.height}m</span></div>
          <div class="spec-item">Weight: <span>${obj.weight}kg</span></div>
          <div class="spec-item">Shape: <span>${this.formatShapeName(obj.shape)}</span></div>
        </div>
        <div class="card-tags">
          ${obj.fragile ? '<span class="tag tag-fragile">Fragile</span>' : ''}
          ${obj.stackable ? '<span class="tag tag-stack">Stackable</span>' : ''}
          ${obj.rotatable ? '<span class="tag tag-rot">Rotatable</span>' : ''}
          ${this.getShapeTagHtml(obj.shape)}
        </div>
      `;
      listEl.appendChild(card);
    });
  }

  formatShapeName(shape) {
    if (!shape) return 'Cuboid';
    const map = {
      'cuboid': 'Cuboid',
      'cube': 'Cube',
      'cylinder': 'Cylinder',
      'sphere': 'Sphere',
      'wedge': 'Wedge',
      'triangular_prism': 'Triangular Prism',
      'pyramid': 'Pyramid',
      'capsule': 'Capsule',
      'hexagonal_prism': 'Hex Prism',
      'torus': 'Torus / Spool',
      'flat': 'Flat Package',
    };
    return map[shape.toLowerCase()] || (shape.charAt(0).toUpperCase() + shape.slice(1));
  }

  getShapeTagHtml(shape) {
    if (!shape || shape === 'cuboid' || shape === 'cube') return '';
    const s = shape.toLowerCase();
    const label = this.formatShapeName(s);
    return `<span class="tag tag-${s}">${label}</span>`;
  }

  getShapeDimensionConfig(shape) {
    const s = (shape || 'cuboid').toLowerCase();
    const configs = {
      cuboid: {
        fields: [
          { name: 'length', label: 'Length (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
          { name: 'width', label: 'Width (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Height (m)', defaultVal: 2.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.length, width: vals.width, height: vals.height }),
      },
      cube: {
        fields: [
          { name: 'side', label: 'Side Length (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.side, width: vals.side, height: vals.side }),
      },
      cylinder: {
        fields: [
          { name: 'diameter', label: 'Diameter (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Height (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.diameter, width: vals.diameter, height: vals.height }),
      },
      sphere: {
        fields: [
          { name: 'diameter', label: 'Diameter (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.diameter, width: vals.diameter, height: vals.diameter }),
      },
      wedge: {
        fields: [
          { name: 'baseLength', label: 'Base Length (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
          { name: 'width', label: 'Width (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'rampHeight', label: 'Ramp Height (m)', defaultVal: 2.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.baseLength, width: vals.width, height: vals.rampHeight }),
      },
      pyramid: {
        fields: [
          { name: 'baseLength', label: 'Base Length (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'baseWidth', label: 'Base Width (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Apex Height (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.baseLength, width: vals.baseWidth, height: vals.height }),
      },
      capsule: {
        fields: [
          { name: 'diameter', label: 'Diameter (m)', defaultVal: 2.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Total Height (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.diameter, width: vals.diameter, height: vals.height }),
      },
      hexagonal_prism: {
        fields: [
          { name: 'diameter', label: 'Outer Diameter (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Height (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.diameter, width: vals.diameter, height: vals.height }),
      },
      torus: {
        fields: [
          { name: 'diameter', label: 'Outer Diameter (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
          { name: 'height', label: 'Height / Thickness (m)', defaultVal: 2.0, step: 0.1, min: 0.1 },
        ],
        resolve: (vals) => ({ length: vals.diameter, width: vals.diameter, height: vals.height }),
      },
      flat: {
        fields: [
          { name: 'length', label: 'Length (m)', defaultVal: 4.0, step: 0.1, min: 0.1 },
          { name: 'width', label: 'Width (m)', defaultVal: 3.0, step: 0.1, min: 0.1 },
          { name: 'thickness', label: 'Thickness (m)', defaultVal: 0.5, step: 0.05, min: 0.05 },
        ],
        resolve: (vals) => ({ length: vals.length, width: vals.width, height: vals.thickness }),
      },
    };
    return configs[s] || configs.cuboid;
  }

  renderShapeDimensionInputs(shape) {
    const container = document.getElementById('dimensions-container');
    if (!container) return;

    const config = this.getShapeDimensionConfig(shape);
    let html = '<div class="form-row">';
    config.fields.forEach(f => {
      html += `
        <div class="form-group">
          <label for="dim-${f.name}">${f.label}</label>
          <input type="number" step="${f.step || 0.1}" min="${f.min || 0.1}" id="dim-${f.name}" name="${f.name}" class="form-input" value="${f.defaultVal}" required>
        </div>
      `;
    });
    html += '</div>';
    container.innerHTML = html;
  }

  renderContainersList() {
    const listEl = document.getElementById('containers-list');
    const badgeEl = document.getElementById('badge-containers-count');
    if (!listEl) return;
    listEl.innerHTML = '';
    if (badgeEl) badgeEl.innerText = this.containers.length;

    if (this.containers.length === 0) {
      listEl.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 30px;">No containers found. Click "+ Add Container".</div>`;
      return;
    }

    this.containers.forEach(c => {
      const isSelected = this.selectedContainerIds.has(c.id);
      const card = document.createElement('div');
      card.className = `inventory-card ${isSelected ? 'selected' : ''}`;
      card.onclick = (e) => {
        if (e.target.closest('.btn-delete')) return;
        this.toggleContainerSelection(c.id);
      };

      const volume = (c.length * c.width * c.height).toFixed(1);

      card.innerHTML = `
        <div class="card-header">
          <div class="card-title-group">
            <input type="checkbox" class="custom-checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); window.app.toggleContainerSelection(${c.id})">
            <span class="card-title">${c.name}</span>
          </div>
          <button class="btn-delete" title="Delete container" onclick="window.app.deleteContainer(${c.id})">✕</button>
        </div>
        <div class="card-specs">
          <div class="spec-item">Dimensions: <span>${c.length}x${c.width}x${c.height}m</span></div>
          <div class="spec-item">Max Weight: <span>${c.max_weight}kg</span></div>
          <div class="spec-item">Volume: <span>${volume}m³</span></div>
        </div>
      `;
      listEl.appendChild(card);
    });
  }

  toggleObjectSelection(id) {
    if (this.selectedObjectIds.has(id)) {
      this.selectedObjectIds.delete(id);
    } else {
      this.selectedObjectIds.add(id);
    }
    this.renderObjectsList();
    this.updateSelectionSummary();
  }

  toggleContainerSelection(id) {
    if (this.selectedContainerIds.has(id)) {
      this.selectedContainerIds.delete(id);
    } else {
      this.selectedContainerIds.add(id);
    }
    this.renderContainersList();
    this.updateSelectionSummary();
  }

  selectAllObjects(selectAll = true) {
    if (selectAll) {
      this.objects.forEach(o => this.selectedObjectIds.add(o.id));
    } else {
      this.selectedObjectIds.clear();
    }
    this.renderObjectsList();
    this.updateSelectionSummary();
  }

  updateSelectionSummary() {
    const summaryEl = document.getElementById('selection-summary-text');
    if (summaryEl) {
      summaryEl.innerText = `${this.selectedObjectIds.size} Objects | ${this.selectedContainerIds.size} Containers`;
    }
  }

  async deleteObject(id) {
    if (!confirm('Delete this object?')) return;
    try {
      await fetch(`/api/objects/${id}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });
      this.selectedObjectIds.delete(id);
      await this.loadInventory();
    } catch (e) {
      console.error(e);
    }
  }

  async deleteContainer(id) {
    if (!confirm('Delete this container?')) return;
    try {
      await fetch(`/api/containers/${id}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });
      this.selectedContainerIds.delete(id);
      await this.loadInventory();
    } catch (e) {
      console.error(e);
    }
  }

  // -------------------------------------------------------------
  // Packing Simulation
  // -------------------------------------------------------------
  async runPacking() {
    if (!this.currentUser) return;
    if (this.selectedContainerIds.size === 0) {
      alert('Please select at least one container to pack into.');
      return;
    }
    if (this.selectedObjectIds.size === 0) {
      alert('Please select at least one object to pack.');
      return;
    }

    const btnPack = document.getElementById('btn-run-pack');
    if (btnPack) {
      btnPack.innerText = 'Calculating 3D Packing...';
      btnPack.disabled = true;
    }

    try {
      const res = await fetch('/api/pack', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          object_ids: Array.from(this.selectedObjectIds),
          container_ids: Array.from(this.selectedContainerIds),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Packing calculation failed');

      // Hand results directly to Three.js Visualizer
      this.visualizer.loadData(data.containers);

      // Handle unpacked items notice
      this.renderUnpackedNotice(data.unpacked_items, data.summary);
    } catch (err) {
      alert(err.message);
    } finally {
      if (btnPack) {
        btnPack.innerText = 'Pack & Calculate 3D';
        btnPack.disabled = false;
      }
    }
  }

  renderUnpackedNotice(unpacked, summary) {
    const noticeEl = document.getElementById('unpacked-notice');
    if (!noticeEl) return;
    if (unpacked && unpacked.length > 0) {
      noticeEl.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 4px;">Notice: ${unpacked.length} item(s) could not fit</div>
        ${unpacked.map(u => `<div>• <b>${u.name}</b> (${u.dimensions}): ${u.reason}</div>`).join('')}
      `;
      noticeEl.style.display = 'block';
    } else {
      noticeEl.style.display = 'none';
    }
  }

  // -------------------------------------------------------------
  // UI Event Bindings
  // -------------------------------------------------------------
  bindEvents() {
    // Tab switching
    document.getElementById('tab-btn-objects').onclick = () => {
      document.getElementById('tab-btn-objects').classList.add('active');
      document.getElementById('tab-btn-containers').classList.remove('active');
      document.getElementById('tab-content-objects').style.display = 'flex';
      document.getElementById('tab-content-containers').style.display = 'none';
    };

    document.getElementById('tab-btn-containers').onclick = () => {
      document.getElementById('tab-btn-containers').classList.add('active');
      document.getElementById('tab-btn-objects').classList.remove('active');
      document.getElementById('tab-content-containers').style.display = 'flex';
      document.getElementById('tab-content-objects').style.display = 'none';
    };

    // Pack Action
    document.getElementById('btn-run-pack').onclick = () => this.runPacking();

    // Select All / Deselect All
    document.getElementById('btn-select-all-objects').onclick = () => this.selectAllObjects(true);
    document.getElementById('btn-deselect-all-objects').onclick = () => this.selectAllObjects(false);

    // Sequence Animation
    const animBtn = document.getElementById('btn-play-anim');
    if (animBtn) animBtn.onclick = () => this.visualizer.playSequenceAnimation();

    // Reset Camera
    const resetCamBtn = document.getElementById('btn-reset-cam');
    if (resetCamBtn) resetCamBtn.onclick = () => this.visualizer.resetCamera();

    // Auth Modal
    document.getElementById('btn-nav-auth').onclick = () => this.showAuthModal(true);
    document.getElementById('btn-close-auth-modal').onclick = () => this.showAuthModal(false);
    document.getElementById('btn-logout').onclick = () => this.logout();

    // Auth Switch
    let isRegisterMode = false;
    const authTitle = document.getElementById('auth-modal-title');
    const authSubmit = document.getElementById('btn-auth-submit');
    const authSwitch = document.getElementById('btn-switch-auth');

    authSwitch.onclick = () => {
      isRegisterMode = !isRegisterMode;
      authTitle.innerText = isRegisterMode ? 'Create an Account' : 'Welcome Back';
      authSubmit.innerText = isRegisterMode ? 'Sign Up' : 'Log In';
      authSwitch.innerText = isRegisterMode ? 'Already have an account? Log In' : "Don't have an account? Sign Up";
    };

    document.getElementById('auth-form').onsubmit = (e) => {
      e.preventDefault();
      const u = document.getElementById('auth-username').value;
      const p = document.getElementById('auth-password').value;
      if (isRegisterMode) this.handleRegister(u, p);
      else this.handleLogin(u, p);
    };

    // Add Object Modal
    const objModal = document.getElementById('add-object-modal');
    document.getElementById('btn-open-add-object').onclick = () => {
      objModal.classList.add('active');
      const shape = document.getElementById('obj-shape')?.value || 'cuboid';
      this.renderShapeDimensionInputs(shape);
    };
    document.getElementById('btn-close-add-object').onclick = () => objModal.classList.remove('active');

    const shapeSelect = document.getElementById('obj-shape');
    if (shapeSelect) {
      shapeSelect.onchange = () => {
        const s = shapeSelect.value;
        this.renderShapeDimensionInputs(s);
        const stackCheckbox = document.getElementById('obj-stackable');
        if (['sphere', 'pyramid'].includes(s)) {
          stackCheckbox.checked = false;
        } else if (['cuboid', 'cube', 'hexagonal_prism', 'flat'].includes(s)) {
          stackCheckbox.checked = true;
        }
      };
    }

    document.getElementById('add-object-form').onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('obj-name').value.trim();
      const shape = document.getElementById('obj-shape').value;
      const weight = parseFloat(document.getElementById('obj-weight').value);
      const fragile = document.getElementById('obj-fragile').checked;
      const stackable = document.getElementById('obj-stackable').checked;
      const rotatable = document.getElementById('obj-rotatable').checked;

      const config = this.getShapeDimensionConfig(shape);
      const vals = {};
      config.fields.forEach(f => {
        const inp = document.getElementById(`dim-${f.name}`);
        vals[f.name] = inp ? parseFloat(inp.value) : f.defaultVal;
      });

      const { length, width, height } = config.resolve(vals);

      try {
        const res = await fetch('/api/objects', {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({ name, length, width, height, weight, shape, fragile, stackable, rotatable }),
        });
        if (res.ok) {
          objModal.classList.remove('active');
          document.getElementById('add-object-form').reset();
          this.renderShapeDimensionInputs('cuboid');
          await this.loadInventory();
        }
      } catch (err) {
        console.error(err);
      }
    };

    // Add Container Modal
    const cModal = document.getElementById('add-container-modal');
    document.getElementById('btn-open-add-container').onclick = () => cModal.classList.add('active');
    document.getElementById('btn-close-add-container').onclick = () => cModal.classList.remove('active');

    document.getElementById('add-container-form').onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('c-name').value;
      const length = parseFloat(document.getElementById('c-length').value);
      const width = parseFloat(document.getElementById('c-width').value);
      const height = parseFloat(document.getElementById('c-height').value);
      const max_weight = parseFloat(document.getElementById('c-max-weight').value);

      try {
        const res = await fetch('/api/containers', {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({ name, length, width, height, max_weight }),
        });
        if (res.ok) {
          cModal.classList.remove('active');
          document.getElementById('add-container-form').reset();
          await this.loadInventory();
        }
      } catch (err) {
        console.error(err);
      }
    };

    // Initialize Add Object modal inputs with default shape
    this.renderShapeDimensionInputs('cuboid');
  }
}

// Instantiate on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});

