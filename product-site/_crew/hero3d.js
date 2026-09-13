/* NSE v5 — Cinematic Three.js hero: "Sovereign Neural Observatory"
   Self-contained IIFE. Reuses the existing <canvas id="torus">.
   If THREE is missing or anything throws, the canvas is hidden and a
   pure-CSS glowing orb (.hero-core .orb) remains as the fallback, so
   the page never goes blank. No DOM elements are created here. */
(function () {
  'use strict';

  var canvas = null;
  function fail() {
    if (canvas) { try { canvas.style.display = 'none'; } catch (e) { /* noop */ } }
  }

  document.addEventListener('DOMContentLoaded', function () {
    canvas = document.getElementById('torus');
    if (!canvas) return;
    if (typeof window.THREE === 'undefined' || !window.THREE) { fail(); return; }

    try {
      var THREE = window.THREE;

      // ---- palette (design tokens) ----
      var GOLD = 0xd8b45a, AMBER = 0xe79a5a, CYAN = 0x57e6d4,
          BLUE = 0x8fb4ff, VIOLET = 0xc98cff, GOLD_HOT = 0xf2d98c;

      // ---- renderer (uses the existing canvas, additive, no post FX) ----
      var renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance'
      });
      renderer.setClearColor(0x000000, 0);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(55, 16 / 9, 0.1, 100);
      camera.position.set(0, 0.15, 7.2);
      camera.lookAt(0, 0, 0);

      var group = new THREE.Group();
      scene.add(group);

      function meshMat(color, opacity) {
        return new THREE.MeshBasicMaterial({
          color: color, transparent: true, opacity: opacity,
          blending: THREE.AdditiveBlending, depthWrite: false
        });
      }

      // 1) Central core: 17 micro-spheres on a golden-angle (phyllotaxis) spiral
      var coreGroup = new THREE.Group();
      group.add(coreGroup);
      var N = 17, GA = 2.399963, CR = 0.46;
      var coreGeo = new THREE.SphereGeometry(0.085, 12, 12);
      var coreMeshes = [];
      for (var i = 0; i < N; i++) {
        var phi = i * GA;
        var fy = 1 - (2 * i) / N;
        var fr = Math.sqrt(Math.max(0, 1 - fy * fy));
        var cm = new THREE.Mesh(coreGeo, meshMat(GOLD, 0.95));
        cm.position.set(Math.cos(phi) * fr * CR, fy * CR, Math.sin(phi) * fr * CR);
        cm.userData.phase = i * 0.6;
        coreGroup.add(cm);
        coreMeshes.push(cm);
      }
      var nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 16), meshMat(GOLD_HOT, 1.0));
      coreGroup.add(nucleus);

      // 2) Symbiotic torus: 5 concentric strata rings (tilted, Y-offset)
      var strata = [
        { c: GOLD,   r: 1.35, tilt: [ 0.14, 0.00,  0.10], y: -0.16 },
        { c: AMBER,  r: 1.85, tilt: [-0.34, 0.22,  0.32], y: -0.06 },
        { c: CYAN,   r: 2.35, tilt: [ 0.52, -0.18, -0.28], y: 0.04 },
        { c: BLUE,   r: 2.85, tilt: [-0.72, 0.42,  0.46], y: 0.14 },
        { c: VIOLET, r: 3.35, tilt: [ 0.96, -0.50, -0.62], y: 0.24 }
      ];
      for (var s = 0; s < strata.length; s++) {
        var st = strata[s];
        var ring = new THREE.Mesh(new THREE.TorusGeometry(st.r, 0.018, 12, 220), meshMat(st.c, 0.30));
        ring.rotation.set(st.tilt[0], st.tilt[1], st.tilt[2]);
        ring.position.y = st.y;
        group.add(ring);
      }

      // 3) Metabolism: ~480 particles orbiting a torus band, cyan, counter-rotating
      var pCount = 480, R = 2.4, TUBE = 0.62;
      var pos = new Float32Array(pCount * 3);
      for (var p = 0; p < pCount; p++) {
        var u = Math.random() * Math.PI * 2;
        var v = Math.random() * Math.PI * 2;
        var rr = R + Math.cos(v) * TUBE;
        pos[p * 3]     = rr * Math.cos(u);
        pos[p * 3 + 1] = Math.sin(v) * TUBE * 0.55;
        pos[p * 3 + 2] = rr * Math.sin(u);
      }
      var metabGeo = new THREE.BufferGeometry();
      metabGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      var metabolism = new THREE.Points(metabGeo, new THREE.PointsMaterial({
        color: CYAN, size: 0.045, sizeAttenuation: true,
        transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false
      }));
      group.add(metabolism);

      // 4) Satellites: one node + faint halo per stratum, colored to match its ring
      var satGeo = new THREE.SphereGeometry(0.16, 16, 16);
      var haloGeo = new THREE.TorusGeometry(0.32, 0.008, 8, 80);
      var satellites = [];
      for (var k = 0; k < strata.length; k++) {
        var st2 = strata[k];
        var holder = new THREE.Group();
        var node = new THREE.Mesh(satGeo, meshMat(st2.c, 0.95));
        var halo = new THREE.Mesh(haloGeo, meshMat(st2.c, 0.35));
        halo.rotation.x = Math.PI / 2.3;
        holder.add(node); holder.add(halo);
        holder.userData = {
          radius: st2.r,
          baseAngle: k * (Math.PI * 2 / strata.length),
          speed: 0.18 + k * 0.05,
          y: st2.y
        };
        group.add(holder);
        satellites.push(holder);
      }

      // 5) Starfield: ~360 distant faint points
      var sCount = 360;
      var spos = new Float32Array(sCount * 3);
      for (var j = 0; j < sCount; j++) {
        var th = Math.random() * Math.PI * 2;
        var ph = Math.acos(2 * Math.random() - 1);
        var dr = 9 + Math.random() * 4.5;
        spos[j * 3]     = dr * Math.sin(ph) * Math.cos(th);
        spos[j * 3 + 1] = dr * Math.cos(ph) * 0.6;
        spos[j * 3 + 2] = dr * Math.sin(ph) * Math.sin(th);
      }
      var starGeo = new THREE.BufferGeometry();
      starGeo.setAttribute('position', new THREE.BufferAttribute(spos, 3));
      var stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
        color: GOLD_HOT, size: 0.03, sizeAttenuation: true,
        transparent: true, opacity: 0.5,
        blending: THREE.AdditiveBlending, depthWrite: false
      }));
      scene.add(stars);

      // 6) Layout / resize: right-offset on wide, centered below 820px
      function setLayout() {
        var w = canvas.clientWidth || window.innerWidth;
        var h = canvas.clientHeight || window.innerHeight;
        if (w <= 0) w = window.innerWidth;
        if (h <= 0) h = window.innerHeight;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        group.position.x = w >= 820 ? 1.6 : 0;
      }
      setLayout();
      window.addEventListener('resize', setLayout);

      // pointer parallax (toward cursor)
      var targetTX = 0, targetTY = 0, curTX = 0, curTY = 0;
      window.addEventListener('pointermove', function (e) {
        targetTX = (e.clientX / window.innerWidth) * 2 - 1;
        targetTY = (e.clientY / window.innerHeight) * 2 - 1;
      }, { passive: true });

      // animation loop: idle auto-rotate + scroll-linked + parallax
      var clock = new THREE.Clock();
      var autoRot = 0, last = 0;
      function animate() {
        requestAnimationFrame(animate);
        var t = clock.getElapsedTime();
        var dt = Math.min(t - last, 0.05);
        last = t;

        autoRot += dt * 0.12;                              // idle auto-rotation
        var sy = window.scrollY || window.pageYOffset || 0;
        var scrollRot = sy * 0.0009;                       // subtle scroll-linked

        curTX += (targetTX - curTX) * 0.04;                // parallax lerp
        curTY += (targetTY - curTY) * 0.04;

        group.rotation.y = autoRot + scrollRot + curTX * 0.45;
        group.rotation.x = curTY * 0.32;
        group.rotation.z = curTX * 0.08;

        metabolism.rotation.y = -autoRot * 1.5 - scrollRot * 0.5;  // counter-rotate
        metabolism.rotation.x = -curTY * 0.2;

        coreGroup.scale.setScalar(1 + Math.sin(t * 1.4) * 0.05);   // gentle pulse
        for (var ci = 0; ci < coreMeshes.length; ci++) {
          coreMeshes[ci].scale.setScalar(1 + Math.sin(t * 2 + coreMeshes[ci].userData.phase) * 0.16);
        }
        nucleus.scale.setScalar(1 + Math.sin(t * 2.4) * 0.18);
        nucleus.material.opacity = 0.85 + Math.sin(t * 2.4) * 0.15;

        for (var qi = 0; qi < satellites.length; qi++) {   // orbit their strata
          var ud = satellites[qi].userData;
          var ang = ud.baseAngle + t * ud.speed;
          satellites[qi].position.set(Math.cos(ang) * ud.radius, ud.y, Math.sin(ang) * ud.radius);
          satellites[qi].rotation.y = ang;
        }

        stars.rotation.y = autoRot * 0.15;                 // slow drift

        renderer.render(scene, camera);
      }
      animate();
    } catch (err) {
      fail();
      if (window.console && console.error) console.error('[hero3d] init failed:', err);
    }
  });
})();
