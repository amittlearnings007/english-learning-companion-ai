from __future__ import annotations

import streamlit.components.v1 as components


SCENE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <style>
    :root { color-scheme: light; }
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: linear-gradient(145deg, #e2f7ff, #fff6dc); font-family: Nunito, sans-serif; }
    #world { width: 100%; height: 100%; position: relative; }
    .hint { position: absolute; left: 14px; bottom: 12px; z-index: 2; color: #28536c; background: rgba(255,255,255,.82); border-radius: 999px; padding: 5px 10px; font: 700 12px Nunito, sans-serif; }
    .label { position: absolute; right: 14px; top: 12px; z-index: 2; color: #136b5a; background: rgba(255,255,255,.84); border-radius: 10px; padding: 7px 10px; font: 800 12px Nunito, sans-serif; }
    .fallback-world { display: none; height: 100%; align-items: center; justify-content: center; gap: 22px; perspective: 700px; transform-style: preserve-3d; }
    .fallback-shape { display: grid; place-items: center; width: 64px; height: 64px; color: #17324d; font: 800 11px Nunito, sans-serif; cursor: pointer; box-shadow: 0 12px 18px rgba(33, 75, 93, .18); transform-style: preserve-3d; transition: transform .18s ease, box-shadow .18s ease; }
    .fallback-shape:hover { transform: translateY(-7px) rotateX(12deg) rotateY(-12deg); box-shadow: 0 18px 22px rgba(33, 75, 93, .25); }
    .fallback-red { background: #ef7d6b; border-radius: 50%; }
    .fallback-blue { background: #64b8e8; border-radius: 12px; transform: rotateX(15deg) rotateY(-22deg); }
    .fallback-ball { background: #ffd75a; border-radius: 50%; transform: rotateX(35deg) rotateY(30deg); }
    .fallback-play { background: #78c39c; border-radius: 16px; transform: rotateX(-18deg) rotateY(24deg); }
  </style>
</head>
<body>
  <div id="world"><div class="label" id="label">Tap a shape</div><div class="hint">Drag to spin the word world</div><div class="fallback-world" id="fallback"><div class="fallback-shape fallback-red" data-word="red">RED</div><div class="fallback-shape fallback-blue" data-word="blue">BLUE</div><div class="fallback-shape fallback-ball" data-word="ball">BALL</div><div class="fallback-shape fallback-play" data-word="play">PLAY</div></div></div>
  <script src="https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.min.js"></script>
  <script>
    const mount = document.getElementById('world');
    const label = document.getElementById('label');
    if (!window.THREE) {
      label.textContent = 'Tap a word';
      document.getElementById('fallback').style.display = 'flex';
      document.querySelectorAll('.fallback-shape').forEach((shape) => {
        shape.addEventListener('click', () => { label.textContent = `Say ${shape.dataset.word}!`; });
      });
    } else {
    const THREE = window.THREE;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, mount.clientWidth / mount.clientHeight, 0.1, 100);
    camera.position.set(0, 1.2, 7.5);
    const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.HemisphereLight(0xffffff, 0xb8d9df, 2.1));
    const sun = new THREE.DirectionalLight(0xffffff, 2.4);
    sun.position.set(3, 4, 5);
    scene.add(sun);
    const world = new THREE.Group();
    scene.add(world);
    const items = [
      {word: 'RED', color: 0xef7d6b, shape: 'sphere', position: [-2.0, 0.45, 0]},
      {word: 'BLUE', color: 0x64b8e8, shape: 'cube', position: [0, 1.1, 0]},
      {word: 'BALL', color: 0xffd75a, shape: 'torus', position: [2.0, 0.35, 0]},
      {word: 'PLAY', color: 0x78c39c, shape: 'sphere', position: [0, -0.75, 0.4]}
    ];
    const meshes = [];
    const materialFor = (color) => new THREE.MeshStandardMaterial({color, roughness: 0.34, metalness: 0.05});
    for (const item of items) {
      let geometry;
      if (item.shape === 'cube') geometry = new THREE.BoxGeometry(1.15, 1.15, 1.15);
      else if (item.shape === 'torus') geometry = new THREE.TorusGeometry(0.64, 0.22, 18, 42);
      else geometry = new THREE.IcosahedronGeometry(0.78, 1);
      const mesh = new THREE.Mesh(geometry, materialFor(item.color));
      mesh.position.set(...item.position);
      mesh.userData = item;
      world.add(mesh);
      meshes.push(mesh);
    }
    const floor = new THREE.Mesh(new THREE.CircleGeometry(3.9, 48), new THREE.MeshStandardMaterial({color: 0xffffff, transparent: true, opacity: 0.58}));
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -1.45;
    world.add(floor);
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let dragging = false;
    let lastX = 0;
    mount.addEventListener('pointerdown', (event) => { dragging = true; lastX = event.clientX; });
    mount.addEventListener('pointerup', () => { dragging = false; });
    mount.addEventListener('pointerleave', () => { dragging = false; });
    mount.addEventListener('pointermove', (event) => {
      if (!dragging) return;
      world.rotation.y += (event.clientX - lastX) * 0.012;
      lastX = event.clientX;
    });
    mount.addEventListener('click', (event) => {
      const bounds = mount.getBoundingClientRect();
      pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
      pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(meshes)[0];
      if (hit) label.textContent = `Say ${hit.object.userData.word.toLowerCase()}!`;
    });
    function resize() {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    }
    window.addEventListener('resize', resize);
    function animate(time) {
      world.rotation.y += 0.0015;
      meshes.forEach((mesh, index) => {
        mesh.rotation.x = time * 0.00025 * (index + 1);
        mesh.position.y += Math.sin(time * 0.001 + index) * 0.00045;
      });
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
    }
  </script>
</body>
</html>
"""


def render_word_world() -> None:
    components.html(SCENE_HTML, height=280, scrolling=False)
