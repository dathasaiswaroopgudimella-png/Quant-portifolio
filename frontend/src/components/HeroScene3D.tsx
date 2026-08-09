"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function HeroScene3D() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const el = mountRef.current;
    let W = el.clientWidth || window.innerWidth;
    let H = el.clientHeight || 700;

    const scene = new THREE.Scene();
    // Deep dark space background color
    scene.background = new THREE.Color(0x08080d);

    const camera = new THREE.PerspectiveCamera(55, Math.max(W, 1) / Math.max(H, 1), 0.1, 1000);
    camera.position.set(0, 2, 28);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x08080d, 1);
    renderer.autoClear = true;

    el.innerHTML = "";
    el.appendChild(renderer.domElement);

    // WebGL Context Loss Recovery
    const handleContextLost = (event: Event) => {
      event.preventDefault();
      console.warn("[HeroScene3D] WebGL context lost. Recovering...");
    };
    const handleContextRestored = () => {
      console.info("[HeroScene3D] WebGL context restored.");
    };
    const canvasEl = renderer.domElement;
    canvasEl.addEventListener("webglcontextlost", handleContextLost, false);
    canvasEl.addEventListener("webglcontextrestored", handleContextRestored, false);

    // Curated Vibrant Color Palette
    const palette = [
      new THREE.Color(0xc0c1ff), // Lavender/Purple
      new THREE.Color(0x4edea3), // Neon Emerald Green
      new THREE.Color(0xffb95f), // Warm Amber
      new THREE.Color(0xff7878), // Coral Red
    ];
    const tempColor = new THREE.Color();

    // 1. Quantitative Geometric Brownian Motion (GBM) Stochastic Price Path Trajectories
    const PATH_COUNT = 16;
    const STEPS_PER_PATH = 45;
    const pathGroup = new THREE.Group();

    for (let p = 0; p < PATH_COUNT; p++) {
      const points: THREE.Vector3[] = [];
      let S = 100.0;
      const mu = 0.04;
      const sigma = 0.12 + (p % 5) * 0.04;
      const dt = 1.0 / STEPS_PER_PATH;
      const startX = -20;
      const startZ = (p - PATH_COUNT / 2) * 2.0;

      for (let step = 0; step <= STEPS_PER_PATH; step++) {
        const x = startX + (step / STEPS_PER_PATH) * 40;
        if (step > 0) {
          const Z = (Math.random() * 2 - 1) + (Math.random() * 2 - 1);
          S = S * Math.exp((mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * Z);
        }
        const y = ((S - 100.0) / 100.0) * 14.0;
        const z = startZ + Math.sin(step * 0.18 + p) * 0.9;
        points.push(new THREE.Vector3(x, y, z));
      }

      // Create thick 3D TubeGeometry instead of standard thin lines for high-DPI visibility
      const curve = new THREE.CatmullRomCurve3(points);
      const tubeGeo = new THREE.TubeGeometry(curve, 60, 0.08, 8, false);
      const c = palette[p % palette.length];
      const tubeMat = new THREE.MeshStandardMaterial({
        color: c,
        emissive: c,
        emissiveIntensity: 0.45,
        roughness: 0.2,
        metalness: 0.8,
        transparent: true,
        opacity: 0.85,
      });
      const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
      pathGroup.add(tubeMesh);
    }
    scene.add(pathGroup);

    // 2. Animated Volatility Surface Mesh (Dynamic Stress Tensor Grid)
    const GRID = 36;
    const surfGeo = new THREE.PlaneGeometry(42, 30, GRID, GRID);
    surfGeo.rotateX(-Math.PI / 2.2);
    const surfColors = new Float32Array(surfGeo.attributes.position.count * 3);
    surfGeo.setAttribute("color", new THREE.BufferAttribute(surfColors, 3));
    surfGeo.computeVertexNormals();

    const surfMat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      wireframe: true,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide
    });
    const surface = new THREE.Mesh(surfGeo, surfMat);
    surface.position.set(0, -7, -2);
    scene.add(surface);

    // 3. Floating Strike & Payoff Node Markers (Octahedrons + Spheres)
    const nodeGroup = new THREE.Group();
    const nodePositions: [number, number, number][] = [
      [-14, 4, -2], [14, 5, -4], [-9, -2, 3], [10, -3, 2],
      [0, 7, -5], [-15, 0, -3], [15, 2, 1], [5, -5, -2],
    ];
    nodePositions.forEach(([x, y, z], i) => {
      const geo = new THREE.OctahedronGeometry(0.65 + (i % 3) * 0.15, 0);
      const mat = new THREE.MeshStandardMaterial({
        color: palette[i % palette.length],
        emissive: palette[i % palette.length],
        emissiveIntensity: 0.7,
        wireframe: i % 2 === 0,
        transparent: true,
        opacity: 0.9,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, y, z);
      nodeGroup.add(mesh);
    });
    scene.add(nodeGroup);

    // 4. Connecting Risk Edges
    const linePts: THREE.Vector3[] = [];
    [[0,1],[1,4],[2,3],[0,5],[3,6],[4,7],[2,7],[5,2]].forEach(([a, b]) => {
      linePts.push(
        new THREE.Vector3(...nodePositions[a]),
        new THREE.Vector3(...nodePositions[b])
      );
    });
    const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
    scene.add(new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ color: 0xc0c1ff, transparent: true, opacity: 0.3 })));

    // 5. Lighting Setup for 3D Shading
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dLight1 = new THREE.DirectionalLight(0xc0c1ff, 1.8);
    dLight1.position.set(12, 22, 15);
    scene.add(dLight1);
    const pLight1 = new THREE.PointLight(0x4edea3, 2.5, 70);
    pLight1.position.set(-12, 6, 8);
    scene.add(pLight1);

    // 6. Mouse Parallax
    let mouseX = 0, mouseY = 0;
    const onMM = (e: MouseEvent) => {
      mouseX = ((e.clientX / window.innerWidth) - 0.5) * 2;
      mouseY = ((e.clientY / window.innerHeight) - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMM, { passive: true });

    // 7. Render Loop
    const clock = new THREE.Clock();
    let reqId: number;
    let isMounted = true;

    const animate = () => {
      if (!isMounted) return;
      reqId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const t = elapsedTime * 0.4;

      pathGroup.rotation.y = Math.sin(t * 0.25) * 0.1;

      // Dynamic Surface Waves
      const sp = surfGeo.attributes.position;
      const sc = surfGeo.attributes.color as THREE.BufferAttribute;
      if (sp && sc) {
        for (let i = 0; i < sp.count; i++) {
          const x = sp.getX(i);
          const z = sp.getZ(i);
          const y = Math.sin(x * 0.18 + t * 1.5) * Math.cos(z * 0.18 + t * 1.2) * 2.4
                  + Math.sin(x * 0.08 + z * 0.1 + t * 2.0) * 1.5;
          sp.setY(i, y);
          const ratio = Math.max(0, Math.min(1, (y + 3.8) / 7.6));
          tempColor.setHSL(0.62 - ratio * 0.48, 0.9, 0.45 + ratio * 0.25);
          sc.setXYZ(i, tempColor.r, tempColor.g, tempColor.b);
        }
        sp.needsUpdate = true;
        sc.needsUpdate = true;
      }

      // Rotate Strike Nodes
      nodeGroup.children.forEach((node, i) => {
        node.rotation.x = t * (0.5 + i * 0.1);
        node.rotation.y = t * (0.4 + i * 0.08);
        (node as THREE.Mesh).position.y = nodePositions[i][1] + Math.sin(t * 2.2 + i * 0.8) * 0.45;
      });

      // Smooth Camera Movement
      const targetCamX = (mouseX || 0) * 2.2;
      const targetCamY = -(mouseY || 0) * 1.5;
      camera.position.x += (targetCamX - camera.position.x) * 0.04;
      camera.position.y += (targetCamY - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);

      try {
        renderer.render(scene, camera);
      } catch (err) {
        // Handle transient WebGL context drops
      }
    };
    animate();

    const onResize = () => {
      if (!el || !isMounted) return;
      W = el.clientWidth || window.innerWidth;
      H = el.clientHeight || 700;
      camera.aspect = Math.max(W, 1) / Math.max(H, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    };
    window.addEventListener("resize", onResize);

    return () => {
      isMounted = false;
      cancelAnimationFrame(reqId);
      window.removeEventListener("mousemove", onMM);
      window.removeEventListener("resize", onResize);
      canvasEl.removeEventListener("webglcontextlost", handleContextLost);
      canvasEl.removeEventListener("webglcontextrestored", handleContextRestored);
      try {
        renderer.dispose();
        surfGeo.dispose();
        surfMat.dispose();
        lineGeo.dispose();
      } catch (e) {
        // Ignore cleanup errors
      }
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className="absolute inset-0 w-full h-full"
      style={{ pointerEvents: "none", background: "#08080d" }}
    />
  );
}
