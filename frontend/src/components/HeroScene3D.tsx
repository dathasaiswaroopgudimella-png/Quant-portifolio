"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function HeroScene3D() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const el = mountRef.current;
    const W = el.clientWidth;
    const H = el.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 1000);
    camera.position.set(0, 0, 28);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    el.innerHTML = "";
    el.appendChild(renderer.domElement);

    // 1. Particle Field
    const PARTICLE_COUNT = 2200;
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
      pPos[i * 3] = (Math.random() - 0.5) * 120;
      pPos[i * 3 + 1] = (Math.random() - 0.5) * 80;
      pPos[i * 3 + 2] = (Math.random() - 0.5) * 100;
      const c = palette[Math.floor(Math.random() * palette.length)];
      pCol[i * 3] = c.r; pCol[i * 3 + 1] = c.g; pCol[i * 3 + 2] = c.b;
    }
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    pGeo.setAttribute("color", new THREE.BufferAttribute(pCol, 3));
    const pMat = new THREE.PointsMaterial({ size: 0.18, vertexColors: true, transparent: true, opacity: 0.75, sizeAttenuation: true });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    // 2. Animated Wave Surface
    const GRID = 48;
    const surfGeo = new THREE.PlaneGeometry(40, 32, GRID, GRID);
    surfGeo.rotateX(-Math.PI / 2);
    const surfColors = new Float32Array(surfGeo.attributes.position.count * 3);
    surfGeo.setAttribute("color", new THREE.BufferAttribute(surfColors, 3));
    surfGeo.computeVertexNormals();
    const surfMat = new THREE.MeshStandardMaterial({ vertexColors: true, wireframe: true, transparent: true, opacity: 0.28 });
    const surface = new THREE.Mesh(surfGeo, surfMat);
    surface.position.set(0, -8, -4);
    scene.add(surface);

    // 3. Floating Icosahedra Nodes
    const nodeGroup = new THREE.Group();
    const nodePositions: [number, number, number][] = [
      [-10, 4, -2], [10, 5, -4], [-6, -3, 3], [7, -4, 2],
      [0, 7, -6], [-13, -1, -3], [13, 1, 1], [3, -7, -3],
    ];
    nodePositions.forEach(([x, y, z], i) => {
      const geo = new THREE.IcosahedronGeometry(0.5 + (i % 3) * 0.18, 1);
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
    scene.add(new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({ color: 0xc0c1ff, transparent: true, opacity: 0.15 })));

    // 5. Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const dLight = new THREE.DirectionalLight(0xc0c1ff, 1.5);
    dLight.position.set(10, 20, 10);
    scene.add(dLight);
    const pLight = new THREE.PointLight(0x4edea3, 2, 60);
    pLight.position.set(-10, 5, 5);
    scene.add(pLight);

    // 6. Mouse Parallax
    let mouseX = 0, mouseY = 0;
    const onMM = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMM);

    // 7. Animate
    let frame = 0, reqId: number;
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      frame++;
      const t = frame * 0.005;

      particles.rotation.y = t * 0.06;
      particles.rotation.x = t * 0.02;

      // Update wave surface
      const sp = surfGeo.attributes.position;
      const sc = surfGeo.attributes.color as THREE.BufferAttribute;
      for (let i = 0; i < sp.count; i++) {
        const x = sp.getX(i);
        const z = sp.getZ(i);
        const y = Math.sin(x * 0.22 + t * 0.8) * Math.cos(z * 0.22 + t * 0.6) * 2.2
                + Math.sin(x * 0.11 + z * 0.15 + t * 1.1) * 1.4;
        sp.setY(i, y);
        const ratio = (y + 3.6) / 7.2;
        const c = new THREE.Color();
        c.setHSL(0.62 - ratio * 0.45, 0.9, 0.45 + ratio * 0.25);
        sc.setXYZ(i, c.r, c.g, c.b);
      }
      sp.needsUpdate = true;
      sc.needsUpdate = true;
      surfGeo.computeVertexNormals();

      nodeGroup.children.forEach((node, i) => {
        node.rotation.x += 0.008 + i * 0.002;
        node.rotation.y += 0.006 + i * 0.001;
        (node as THREE.Mesh).position.y += Math.sin(t * 1.2 + i * 0.8) * 0.006;
      });

      camera.position.x += (mouseX * 4 - camera.position.x) * 0.03;
      camera.position.y += (-mouseY * 3 - camera.position.y) * 0.03;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      if (!el) return;
      const w = el.clientWidth, h = el.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("mousemove", onMM);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
    };
  }, []);

  return <div ref={mountRef} className="absolute inset-0 w-full h-full" style={{ pointerEvents: "none" }} />;
}
