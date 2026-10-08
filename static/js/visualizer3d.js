/**
 * Visualizer3D: High-DPI hardware-accelerated WebGL 3D packing viewport.
 * Powered by Three.js and OrbitControls.
 */

class Visualizer3D {
  constructor(canvasContainerId) {
    this.container = document.getElementById(canvasContainerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    this.containerGroup = null;
    this.itemMeshes = [];
    this.hoveredMesh = null;

    this.currentContainerIndex = 0;
    this.containersData = [];

    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    this.tooltipEl = document.getElementById('hover-tooltip');
    this.explodeFactor = 0;

    this.init();
  }

  init() {
    // 1. Scene & Atmosphere
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f1115);
    this.scene.fog = new THREE.FogExp2(0x0f1115, 0.012);

    // 2. Camera
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(24, 18, 24);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(window.devicePixelRatio || 1);
    this.renderer.setSize(width, height);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.1;
    this.controls.target.set(0, 5, 0);

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    this.scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
    dirLight.position.set(35, 45, 30);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    this.scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0x94a3b8, 0.25);
    fillLight.position.set(-35, 25, -30);
    this.scene.add(fillLight);

    // 6. Grid Floor (Subtle Technical Grid)
    const gridHelper = new THREE.GridHelper(100, 50, 0x333d4b, 0x1e242d);
    gridHelper.position.y = -0.01;
    this.scene.add(gridHelper);

    // Container Group
    this.containerGroup = new THREE.Group();
    this.scene.add(this.containerGroup);

    // Event Listeners
    window.addEventListener('resize', () => this.onWindowResize());
    this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));

    // Render loop
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  getItemColor(item) {
    if (item.fragile) return 0xef4444;       // Crimson Red (Fragile)
    if (item.weight >= 20) return 0xf97316;   // Amber Orange (Heavy)

    const shape = (item.shape || '').toLowerCase();
    switch (shape) {
      case 'cylinder':
        return 0x06b6d4; // Cyan
      case 'sphere':
        return 0x10b981; // Emerald Green
      case 'wedge':
        return 0x6366f1; // Indigo
      case 'triangular_prism':
        return 0x6366f1; // Indigo
      case 'pyramid':
        return 0xec4899; // Pink
      case 'capsule':
        return 0x14b8a6; // Teal
      case 'hexagonal_prism':
        return 0x8b5cf6; // Violet
      case 'torus':
        return 0xd97706; // Warm Amber
      case 'flat':
        return 0xeab308; // Warm Yellow
      case 'cube':
        return 0x2563eb; // Deep Blue
      case 'cuboid':
      default:
        return 0x3b82f6; // Cobalt / Steel Blue
    }
  }

  createShapeGeometry(item) {
    const l = Math.max(0.01, item.length);
    const w = Math.max(0.01, item.width);
    const h = Math.max(0.01, item.height);
    const shape = (item.shape || 'cuboid').toLowerCase();

    let geom;

    switch (shape) {
      case 'cylinder': {
        geom = new THREE.CylinderGeometry(1, 1, h, 32);
        geom.scale(l / 2, 1, w / 2);
        break;
      }
      case 'sphere': {
        geom = new THREE.SphereGeometry(1, 32, 24);
        geom.scale(l / 2, h / 2, w / 2);
        break;
      }
      case 'wedge':
      case 'triangular_prism': {
        const s = new THREE.Shape();
        s.moveTo(-l / 2, -h / 2);
        s.lineTo(l / 2, -h / 2);
        s.lineTo(l / 2, h / 2);
        s.closePath();
        geom = new THREE.ExtrudeGeometry(s, { depth: w, bevelEnabled: false });
        geom.center();
        break;
      }
      case 'pyramid': {
        geom = new THREE.CylinderGeometry(0, Math.SQRT2 / 2, h, 4, 1);
        geom.rotateY(Math.PI / 4);
        geom.scale(l, 1, w);
        break;
      }
      case 'hexagonal_prism': {
        geom = new THREE.CylinderGeometry(1, 1, h, 6);
        geom.scale(l / 2, 1, w / 2);
        break;
      }
      case 'capsule': {
        const rx = l / 2;
        const rz = w / 2;
        const ry = Math.min(rx, rz, h / 2);
        const cylH = Math.max(0.01, h - 2 * ry);
        const points = [];
        const segs = 10;
        for (let i = segs; i >= 0; i--) {
          const a = (Math.PI / 2) + (i / segs) * (Math.PI / 2);
          points.push(new THREE.Vector2(Math.sin(a) * 1.0, -cylH / 2 - Math.cos(a) * ry));
        }
        for (let i = 0; i <= segs; i++) {
          const a = (i / segs) * (Math.PI / 2);
          points.push(new THREE.Vector2(Math.cos(a) * 1.0, cylH / 2 + Math.sin(a) * ry));
        }
        geom = new THREE.LatheGeometry(points, 24);
        geom.scale(rx, 1, rz);
        break;
      }
      case 'torus': {
        const rMajor = Math.min(l, w) / 3;
        const rTube = Math.min(h / 2, rMajor * 0.7);
        geom = new THREE.TorusGeometry(rMajor, rTube, 16, 32);
        geom.rotateX(Math.PI / 2);
        geom.scale(l / (2 * (rMajor + rTube)), h / (2 * rTube), w / (2 * (rMajor + rTube)));
        break;
      }
      case 'cube':
      case 'flat':
      case 'cuboid':
      default: {
        geom = new THREE.BoxGeometry(l, h, w);
        break;
      }
    }

    return geom;
  }

  loadData(containersData) {
    this.containersData = containersData || [];
    this.currentContainerIndex = 0;
    this.renderCurrentContainer();
    this.renderContainerTabs();
  }

  renderCurrentContainer() {
    // Clear old container objects
    while (this.containerGroup.children.length > 0) {
      this.containerGroup.remove(this.containerGroup.children[0]);
    }
    this.itemMeshes = [];

    const cData = this.containersData[this.currentContainerIndex];
    if (!cData) return;

    // Update HUD metrics
    this.updateHudMetrics(cData);

    const offsetX = -cData.length / 2;
    const offsetZ = -cData.width / 2;

    // 1. Technical translucent outer shell
    const shellGeo = new THREE.BoxGeometry(cData.length, cData.height, cData.width);
    const shellMat = new THREE.MeshPhysicalMaterial({
      color: 0x94a3b8,
      transparent: true,
      opacity: 0.06,
      roughness: 0.2,
      metalness: 0.05,
      transmission: 0.5,
      depthWrite: false,
    });
    const shellMesh = new THREE.Mesh(shellGeo, shellMat);
    shellMesh.position.set(0, cData.height / 2, 0);
    this.containerGroup.add(shellMesh);

    // 2. Technical wireframe edges
    const edgesGeo = new THREE.EdgesGeometry(shellGeo);
    const edgesMat = new THREE.LineBasicMaterial({ color: 0x475569, linewidth: 1.5 });
    const wireframe = new THREE.LineSegments(edgesGeo, edgesMat);
    wireframe.position.copy(shellMesh.position);
    this.containerGroup.add(wireframe);

    // 3. Technical Floor Plaque
    const floorGeo = new THREE.BoxGeometry(cData.length, 0.2, cData.width);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x161922, roughness: 0.9 });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.position.set(0, -0.1, 0);
    floorMesh.receiveShadow = true;
    this.containerGroup.add(floorMesh);

    // 4. Place 3D Items
    (cData.items || []).forEach((item, idx) => {
      const color = this.getItemColor(item);
      const geom = this.createShapeGeometry(item);

      const mat = new THREE.MeshStandardMaterial({
        color: color,
        roughness: 0.35,
        metalness: 0.15,
      });
      const mesh = new THREE.Mesh(geom, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;

      // Coordinate mapping: Length->X, Height->Y, Width->Z
      const posX = item.x + item.length / 2 + offsetX;
      const posY = item.z + item.height / 2;
      const posZ = item.y + item.width / 2 + offsetZ;

      mesh.position.set(posX, posY, posZ);
      mesh.userData = {
        item: item,
        basePos: new THREE.Vector3(posX, posY, posZ),
        animIndex: idx,
      };

      // Crisp subtle edge outline
      const itemEdges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geom),
        new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 })
      );
      mesh.add(itemEdges);

      this.containerGroup.add(mesh);
      this.itemMeshes.push(mesh);
    });

    this.resetCamera();
  }

  updateHudMetrics(cData) {
    const dimEl = document.getElementById('metric-dim');
    const itemsEl = document.getElementById('metric-items');
    const weightEl = document.getElementById('metric-weight');
    const utilEl = document.getElementById('metric-util');
    const fillEl = document.getElementById('progress-fill');

    if (dimEl) dimEl.innerText = `${cData.length} x ${cData.width} x ${cData.height} m`;
    if (itemsEl) itemsEl.innerText = `${cData.items ? cData.items.length : 0} items`;
    if (weightEl) weightEl.innerText = `${cData.used_weight} / ${cData.max_weight} kg`;
    if (utilEl) utilEl.innerText = `${cData.utilization}%`;
    if (fillEl) fillEl.style.width = `${Math.min(cData.utilization, 100)}%`;
  }

  renderContainerTabs() {
    const tabsContainer = document.getElementById('viewport-container-tabs');
    if (!tabsContainer) return;
    tabsContainer.innerHTML = '';

    this.containersData.forEach((c, idx) => {
      const btn = document.createElement('button');
      btn.className = `container-tab-btn ${idx === this.currentContainerIndex ? 'active' : ''}`;
      btn.innerText = c.name || `Container ${c.id}`;
      btn.onclick = () => {
        document.querySelectorAll('.container-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentContainerIndex = idx;
        this.renderCurrentContainer();
      };
      tabsContainer.appendChild(btn);
    });
  }

  resetCamera() {
    const cData = this.containersData[this.currentContainerIndex];
    if (!cData) return;

    const maxDim = Math.max(cData.length, cData.height, cData.width);
    const dist = maxDim * 2.1;

    if (window.TWEEN) {
      new TWEEN.Tween(this.camera.position)
        .to({ x: dist, y: dist * 0.85, z: dist }, 700)
        .easing(TWEEN.Easing.Cubic.Out)
        .start();

      new TWEEN.Tween(this.controls.target)
        .to({ x: 0, y: cData.height / 2, z: 0 }, 700)
        .easing(TWEEN.Easing.Cubic.Out)
        .start();
    } else {
      this.camera.position.set(dist, dist * 0.85, dist);
      this.controls.target.set(0, cData.height / 2, 0);
    }
  }

  setExplodeFactor(factor) {
    this.explodeFactor = factor * 1.5;
    this.itemMeshes.forEach(mesh => {
      const base = mesh.userData.basePos;
      mesh.position.x = base.x + base.x * this.explodeFactor;
      mesh.position.y = base.y + base.y * this.explodeFactor * 0.8;
      mesh.position.z = base.z + base.z * this.explodeFactor;
    });
  }

  playSequenceAnimation() {
    if (!window.TWEEN || this.itemMeshes.length === 0) return;

    const explodeSlider = document.getElementById('explode-slider');
    if (explodeSlider) explodeSlider.value = 0;

    const cData = this.containersData[this.currentContainerIndex];
    const topDropHeight = cData ? cData.height + 4 : 12;

    this.itemMeshes.forEach((mesh, i) => {
      const base = mesh.userData.basePos;
      mesh.position.set(base.x, base.y + topDropHeight, base.z);
      mesh.scale.set(1, 1, 1);

      new TWEEN.Tween(mesh.position)
        .to({ x: base.x, y: base.y, z: base.z }, 450)
        .delay(i * 180)
        .easing(TWEEN.Easing.Cubic.Out)
        .start();
    });
  }

  onMouseMove(e) {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    if (this.tooltipEl) {
      this.tooltipEl.style.left = `${e.clientX}px`;
      this.tooltipEl.style.top = `${e.clientY}px`;
    }

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.itemMeshes, false);

    if (intersects.length > 0) {
      const target = intersects[0].object;
      if (this.hoveredMesh !== target) {
        if (this.hoveredMesh) this.hoveredMesh.material.emissive.setHex(0x000000);
        this.hoveredMesh = target;
        this.hoveredMesh.material.emissive.setHex(0x1e2638);

        this.showTooltip(target.userData.item);
      }
    } else {
      if (this.hoveredMesh) {
        this.hoveredMesh.material.emissive.setHex(0x000000);
        this.hoveredMesh = null;
      }
      if (this.tooltipEl) this.tooltipEl.style.display = 'none';
    }
  }

  showTooltip(it) {
    if (!this.tooltipEl || !it) return;
    document.getElementById('tt-name').innerText = it.name;
    document.getElementById('tt-pos').innerText = `(${it.x}, ${it.y}, ${it.z})`;
    document.getElementById('tt-size').innerText = `${it.length} x ${it.width} x ${it.height} m`;
    document.getElementById('tt-weight').innerText = `${it.weight} kg`;
    document.getElementById('tt-vol').innerText = `${it.volume} m³`;

    const badgeGroup = document.getElementById('tt-badges');
    badgeGroup.innerHTML = '';
    if (it.fragile) badgeGroup.innerHTML += '<span class="tag tag-fragile">Fragile</span>';
    if (it.stackable) badgeGroup.innerHTML += '<span class="tag tag-stack">Stackable</span>';
    if (it.weight >= 20) badgeGroup.innerHTML += '<span class="tag tag-heavy">Heavy</span>';
    if (it.shape) {
      const s = it.shape.toLowerCase();
      badgeGroup.innerHTML += `<span class="tag tag-${s}">${it.shape}</span>`;
    }

    this.tooltipEl.style.display = 'block';
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate(time) {
    requestAnimationFrame(this.animate);
    if (window.TWEEN) TWEEN.update(time);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

