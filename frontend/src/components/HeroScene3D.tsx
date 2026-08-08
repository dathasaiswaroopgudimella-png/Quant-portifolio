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

    // 1. Particle Field
    const PARTICLE_COUNT = 1800;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(PARTICLE_COUNT * 3);
    const pCol = new Float32Array(PARTICLE_COUNT * 3);
    const palette = [
      new THREE.Color(0xc0c1ff),
      new THREE.Color(0x4edea3),
      new THREE.Color(0xffb95f),
      new THREE.Color(0xff7878),
    ];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      pPos[i * 3] = (Math.random() - 0.5) * 110;
      pPos[i * 3 + 1] = (Math.random() - 0.5) * 75;
      pPos[i * 3 + 2] = (Math.random() - 0.5) * 90;
      const c = palette[Math.floor(Math.random() * palette.length)];
      pCol[i * 3] = c.r; pCol[i * 3 + 1] = c.g; pCol[i * 3 + 2] = c.b;
    }
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    pGeo.setAttribute("color", new THREE.BufferAttribute(pCol, 3));
    const pMat = new THREE.PointsMaterial({ size: 0.16, vertexColors: true, transparent: true, opacity: 0.75, sizeAttenuation: true });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    // 2. Animated Deforming Wave Surface
    const GRID = 40;
    const surfGeo = new THREE.PlaneGeometry(36, 28, GRID, GRID);
    surfGeo.rotateX(-Math.PI / 2);
    const surfColors = new Float32Array(surfGeo.attributes.position.count * 3);
    surfGeo.setAttribute("color", new THREE.BufferAttribute(surfColors, 3));
    surfGeo.computeVertexNormals();
    const surfMat = new THREE.MeshStandardMaterial({ vertexColors: true, wireframe: true, transparent: true, opacity: 0.30 });
    const surface = new THREE.Mesh(surfGeo, surfMat);
    surface.position.set(0, -7, -4);
    scene.add(surface);

    // 3. Floating 3D Geometric Nodes
    const nodeGroup = new THREE.Group();
    const nodePositions: [number, number, number][] = [
      [-10, 4, -2], [10, 5, -4], [-6, -3, 3], [7, -4, 2],
      [0, 7, -6], [-13, -1, -3], [13, 1, 1], [3, -7, -3],
    ];
    nodePositions.forEach(([x, y, z], i) => {
      const geo = new THREE.IcosahedronGeometry(0.55 + (i % 3) * 0.15, 1);
      const mat = new THREE.MeshStandardMaterial({
        color: palette[i % palette.length],
        emissive: palette[i % palette.length],
        emissiveIntensity: 0.45,
        wireframe: i % 2 === 0,
        transparent: true,
        opacity: 0.85,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(x, y, z);
      nodeGroup.add(mesh);
    });
    scene.add(nodeGroup);

    // 4. Edge Lines Between Nodes
    const linePts: THREE.Vector3[] = [];
    [[0,1],[1,4],[2,3],[0,5],[3,6],[4,7],[2,7],[5,2]].forEach(([a, b]) => {
      linePts.push(
        new THREE.Vector3(...nodePositions[a]),
        new THREE.Vector3(...nodePositions[b])
      );
    });
    const lineGeo = new THREE.BufferGeometry().setFromPoints(linePts);
    scene.add(new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ color: 0xc0c1ff, transparent: true, opacity: 0.18 })));

    // 5. Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dLight = new THREE.DirectionalLight(0xc0c1ff, 1.4);
    dLight.position.set(10, 20, 10);
    scene.add(dLight);
    const pLight = new THREE.PointLight(0x4edea3, 2, 60);
    pLight.position.set(-10, 5, 5);
    scene.add(pLight);

    // 6. Mouse Parallax
    let mouseX = 0, mouseY = 0;
    const onMM = (e: MouseEvent) => {
      mouseX = ((e.clientX / window.innerWidth) - 0.5) * 2;
      mouseY = ((e.clientY / window.innerHeight) - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMM, { passive: true });

    // 7. Animation Loop with Clock to prevent time overflow / drift crash
    const clock = new THREE.Clock();
    let reqId: number;
    let isMounted = true;

    const animate = () => {
      if (!isMounted) return;
      reqId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const t = elapsedTime * 0.4;

      particles.rotation.y = t * 0.12;
      particles.rotation.x = t * 0.04;

      // Update wave surface vertices safely
      const sp = surfGeo.attributes.position;
      const sc = surfGeo.attributes.color as THREE.BufferAttribute;
      if (sp && sc) {
        for (let i = 0; i < sp.count; i++) {
          const x = sp.getX(i);
          const z = sp.getZ(i);
          const y = Math.sin(x * 0.22 + t * 1.5) * Math.cos(z * 0.22 + t * 1.2) * 2.0
                  + Math.sin(x * 0.11 + z * 0.15 + t * 2.0) * 1.2;
          sp.setY(i, y);
          const ratio = Math.max(0, Math.min(1, (y + 3.2) / 6.4));
          const c = new THREE.Color();
          c.setHSL(0.62 - ratio * 0.45, 0.9, 0.45 + ratio * 0.25);
          sc.setXYZ(i, c.r, c.g, c.b);
        }
        sp.needsUpdate = true;
        sc.needsUpdate = true;
        surfGeo.computeVertexNormals();
      }

      // Rotate nodes safely
      nodeGroup.children.forEach((node, i) => {
        node.rotation.x = t * (0.4 + i * 0.1);
        node.rotation.y = t * (0.3 + i * 0.08);
        (node as THREE.Mesh).position.y = nodePositions[i][1] + Math.sin(t * 2.0 + i * 0.8) * 0.4;
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
        pGeo.dispose();
        surfGeo.dispose();
        pMat.dispose();
        surfMat.dispose();
        lineGeo.dispose();
      } catch (e) {
        // ignore cleanup errors
      }
    };
  }, []);

  return <div ref={mountRef} className="absolute inset-0 w-full h-full" style={{ pointerEvents: "none" }} />;
}
