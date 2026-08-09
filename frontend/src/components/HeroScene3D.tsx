"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function HeroScene3D() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const el = mountRef.current;
    let W = el.clientWidth || window.innerWidth;
    let H = el.clientHeight || 600;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, Math.max(W, 1) / Math.max(H, 1), 0.1, 1000);
    camera.position.set(0, 0, 28);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    el.innerHTML = "";
    el.appendChild(renderer.domElement);

    // Color Palette
    const palette = [
      new THREE.Color(0xc0c1ff),
      new THREE.Color(0x4edea3),
      new THREE.Color(0xffb95f),
      new THREE.Color(0xff7878),
    ];

    // 1. Quantitative Geometric Brownian Motion (GBM) Stochastic Price Path Trajectories
    const PATH_COUNT = 14;
    const STEPS_PER_PATH = 40;
    const pathGroup = new THREE.Group();
    const pathCurves: THREE.Line[] = [];

    for (let p = 0; p < PATH_COUNT; p++) {
      const points: THREE.Vector3[] = [];
      let S = 100.0;
      const mu = 0.05;
      const sigma = 0.15 + (p % 4) * 0.05;
      const dt = 1.0 / STEPS_PER_PATH;

      const startX = -18;
      const startZ = (p - PATH_COUNT / 2) * 2.2;

      for (let step = 0; step <= STEPS_PER_PATH; step++) {
        const x = startX + (step / STEPS_PER_PATH) * 36;
        if (step > 0) {
          const Z = (Math.random() * 2 - 1) + (Math.random() * 2 - 1); // Approx Gaussian
          S = S * Math.exp((mu - 0.5 * sigma * sigma) * dt + sigma * Math.sqrt(dt) * Z);
        }
        const y = ((S - 100.0) / 100.0) * 16.0;
        const z = startZ + Math.sin(step * 0.15 + p) * 0.8;
        points.push(new THREE.Vector3(x, y, z));
      }

      const pathGeo = new THREE.BufferGeometry().setFromPoints(points);
      const c = palette[p % palette.length];
      const pathMat = new THREE.LineBasicMaterial({
        color: c,
        transparent: true,
        opacity: 0.55 + (p % 3) * 0.15,
        linewidth: 1.5,
      });
      const line = new THREE.Line(pathGeo, pathMat);
      pathGroup.add(line);
      pathCurves.push(line);
    }
    scene.add(pathGroup);

    // 2. Animated Volatility Surface Mesh (Quant Surface)
    const GRID = 32;
    const surfGeo = new THREE.PlaneGeometry(38, 28, GRID, GRID);
    surfGeo.rotateX(-Math.PI / 2);
    const surfColors = new Float32Array(surfGeo.attributes.position.count * 3);
    surfGeo.setAttribute("color", new THREE.BufferAttribute(surfColors, 3));
    surfGeo.computeVertexNormals();
    const surfMat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide
    });
    const surface = new THREE.Mesh(surfGeo, surfMat);
    surface.position.set(0, -6, -3);
    scene.add(surface);

    // 3. Floating Strike & Payoff Node Markers
    const nodeGroup = new THREE.Group();
    const nodePositions: [number, number, number][] = [
      [-12, 5, -2], [12, 6, -4], [-8, -2, 3], [9, -3, 2],
      [0, 8, -5], [-14, 0, -3], [14, 2, 1], [4, -6, -2],
    ];
    nodePositions.forEach(([x, y, z], i) => {
      const geo = new THREE.OctahedronGeometry(0.55 + (i % 3) * 0.15, 0);
      const mat = new THREE.MeshStandardMaterial({
        color: palette[i % palette.length],
        emissive: palette[i % palette.length],
        emissiveIntensity: 0.6,
        wireframe: i % 2 === 0,
        transparent: true,
        opacity: 0.85,
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
    scene.add(new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ color: 0xc0c1ff, transparent: true, opacity: 0.22 })));

    // 5. Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dLight = new THREE.DirectionalLight(0xc0c1ff, 1.5);
    dLight.position.set(10, 20, 10);
    scene.add(dLight);
    const pLight = new THREE.PointLight(0x4edea3, 2.2, 60);
    pLight.position.set(-10, 5, 5);
    scene.add(pLight);

    // 6. Mouse Parallax
    let mouseX = 0, mouseY = 0;
    const onMM = (e: MouseEvent) => {
      mouseX = ((e.clientX / window.innerWidth) - 0.5) * 2;
      mouseY = ((e.clientY / window.innerHeight) - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMM, { passive: true });

    // 7. Animation Loop with Clock
    const clock = new THREE.Clock();
    let reqId: number;
    let isMounted = true;

    const animate = () => {
      if (!isMounted) return;
      reqId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const t = elapsedTime * 0.4;

      pathGroup.rotation.y = Math.sin(t * 0.3) * 0.12;

      // Update volatility surface vertices
      const sp = surfGeo.attributes.position;
      const sc = surfGeo.attributes.color as THREE.BufferAttribute;
      if (sp && sc) {
        for (let i = 0; i < sp.count; i++) {
          const x = sp.getX(i);
          const z = sp.getZ(i);
          const y = Math.sin(x * 0.2 + t * 1.6) * Math.cos(z * 0.2 + t * 1.3) * 2.2
                  + Math.sin(x * 0.1 + z * 0.12 + t * 2.2) * 1.4;
          sp.setY(i, y);
          const ratio = Math.max(0, Math.min(1, (y + 3.6) / 7.2));
          const c = new THREE.Color();
          c.setHSL(0.62 - ratio * 0.48, 0.9, 0.45 + ratio * 0.25);
          sc.setXYZ(i, c.r, c.g, c.b);
        }
        sp.needsUpdate = true;
        sc.needsUpdate = true;
        surfGeo.computeVertexNormals();
      }

      // Rotate strike nodes
      nodeGroup.children.forEach((node, i) => {
        node.rotation.x = t * (0.5 + i * 0.1);
        node.rotation.y = t * (0.4 + i * 0.08);
        (node as THREE.Mesh).position.y = nodePositions[i][1] + Math.sin(t * 2.2 + i * 0.8) * 0.45;
      });

      // Smooth camera parallax
      const targetCamX = (mouseX || 0) * 3;
      const targetCamY = -(mouseY || 0) * 2;
      camera.position.x += (targetCamX - camera.position.x) * 0.04;
      camera.position.y += (targetCamY - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);

      try {
        renderer.render(scene, camera);
      } catch (err) {
        console.warn("[HeroScene3D] WebGL render frame skipped:", err);
      }
    };
    animate();

    const onResize = () => {
      if (!el || !isMounted) return;
      W = el.clientWidth || window.innerWidth;
      H = el.clientHeight || 600;
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
      try {
        renderer.dispose();
        surfGeo.dispose();
        surfMat.dispose();
        lineGeo.dispose();
      } catch (e) {
        // ignore cleanup errors
      }
    };
  }, []);

  return <div ref={mountRef} className="absolute inset-0 w-full h-full" style={{ pointerEvents: "none" }} />;
}
