"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

interface FragilitySurface3DProps {
  matrix?: number[][];
  spotAxis?: number[];
  volAxis?: number[];
  title?: string;
}

export default function FragilitySurface3D({
  matrix = [
    [0.01, 0.05, 0.12, 0.25, 0.42, 0.85, 1.45],
    [0.02, 0.08, 0.18, 0.35, 0.65, 1.20, 2.10],
    [0.04, 0.12, 0.28, 0.52, 0.95, 1.75, 2.95],
    [0.08, 0.20, 0.45, 0.82, 1.48, 2.50, 4.10],
    [0.15, 0.35, 0.72, 1.30, 2.25, 3.70, 5.80],
    [0.28, 0.60, 1.15, 2.05, 3.45, 5.40, 8.20],
    [0.50, 1.05, 1.90, 3.25, 5.20, 7.90, 11.50],
  ],
  spotAxis = [70, 80, 90, 100, 110, 120, 130],
  volAxis = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
  title = "Interactive 3D Adversarial Fragility Surface (WebGL)",
}: FragilitySurface3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [wireframe, setWireframe] = useState(false);
  const [autoRotate, setAutoRotate] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = 360;

    // 1. Scene, Camera, Renderer Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e0e10);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(24, 22, 28);
    camera.lookAt(0, 2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xc0c1ff, 1.2);
    dirLight1.position.set(10, 20, 15);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x4edea3, 0.8);
    dirLight2.position.set(-15, -10, -10);
    scene.add(dirLight2);

    // 3. Construct 3D Deforming Plane Surface Geometry
    const gridX = matrix[0].length; // Spot points (cols)
    const gridY = matrix.length;    // Vol points (rows)

    const geometry = new THREE.PlaneGeometry(16, 16, gridX - 1, gridY - 1);
    geometry.rotateX(-Math.PI / 2); // Lay horizontal in XZ plane

    const posAttr = geometry.attributes.position;
    const count = posAttr.count;

    // Find max error for color normalization
    let maxVal = 0.001;
    for (let r = 0; r < gridY; r++) {
      for (let c = 0; c < gridX; c++) {
        if (matrix[r][c] > maxVal) maxVal = matrix[r][c];
      }
    }

    // Colors per vertex
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const ix = i % gridX;
      const iy = Math.floor(i / gridX);
      const val = matrix[iy]?.[ix] ?? 0;

      // Height deformation in Y axis
      const heightVal = (val / maxVal) * 6.5;
      posAttr.setY(i, heightVal);

      // Color gradient mapping: Green (low error) -> Yellow -> Orange -> Crimson Red (high peak error)
      const ratio = Math.min(val / maxVal, 1.0);
      const color = new THREE.Color();
      if (ratio < 0.25) {
        color.setHSL(0.38 - ratio * 0.4, 0.85, 0.55); // Green to Cyan
      } else if (ratio < 0.65) {
        color.setHSL(0.14 - (ratio - 0.25) * 0.2, 0.95, 0.55); // Yellow to Amber
      } else {
        color.setHSL(0.0 + (1.0 - ratio) * 0.08, 0.95, 0.55); // Crimson Red
      }

      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }

    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();

    // 4. Material & Mesh
    const material = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.35,
      metalness: 0.2,
      wireframe: wireframe,
      side: THREE.DoubleSide,
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // 5. Grid Helper & Axis Labels Visuals
    const gridHelper = new THREE.GridHelper(20, 10, 0x2e2c33, 0x1f1e24);
    gridHelper.position.y = -0.05;
    scene.add(gridHelper);

    // 6. Interactive Drag Controls
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    const domEl = renderer.domElement;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaMove = {
        x: e.clientX - previousMousePosition.x,
        y: e.clientY - previousMousePosition.y,
      };

      mesh.rotation.y += deltaMove.x * 0.008;
      mesh.rotation.x += deltaMove.y * 0.008;

      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    domEl.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // 7. Animation Loop
    let reqId: number;
    const animate = () => {
      reqId = requestAnimationFrame(animate);
      if (autoRotate && !isDragging) {
        mesh.rotation.y += 0.004;
      }
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(reqId);
      window.removeEventListener("resize", handleResize);
      domEl.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
    };
  }, [matrix, wireframe, autoRotate]);

  return (
    <div className="bg-[#161519] border border-[#2e2c33] rounded-2xl p-5 space-y-3 font-sans">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#2e2c33] pb-3">
        <div>
          <h3 className="font-bold text-xs uppercase font-mono tracking-wider text-[#e5e1e4] flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#c0c1ff] animate-pulse" />
            {title}
          </h3>
          <p className="text-[11px] text-[#908fa0]">
            Drag mouse to rotate 3D pricing error topology &bull; Peaks represent maximal QuantLib divergence
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`px-3 py-1 rounded-lg border transition-all ${
              autoRotate
                ? "bg-[#c0c1ff]/10 text-[#c0c1ff] border-[#c0c1ff]/30"
                : "bg-[#0e0e10] text-[#908fa0] border-[#2e2c33]"
            }`}
          >
            {autoRotate ? "Auto-Rotate: ON" : "Auto-Rotate: OFF"}
          </button>
          <button
            onClick={() => setWireframe(!wireframe)}
            className={`px-3 py-1 rounded-lg border transition-all ${
              wireframe
                ? "bg-[#4edea3]/10 text-[#4edea3] border-[#4edea3]/30"
                : "bg-[#0e0e10] text-[#908fa0] border-[#2e2c33]"
            }`}
          >
            {wireframe ? "Wireframe" : "Shaded Surface"}
          </button>
        </div>
      </div>

      <div className="relative rounded-xl overflow-hidden border border-[#2e2c33] bg-[#0e0e10]">
        <div ref={containerRef} className="w-full h-[360px] cursor-grab active:cursor-grabbing" />

        {/* Legend Overlay */}
        <div className="absolute bottom-3 left-3 bg-[#161519]/90 backdrop-blur border border-[#2e2c33] p-2.5 rounded-lg text-[10px] font-mono text-[#908fa0] flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#4edea3]" />
            <span>Low Divergence (&lt;0.5%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffb95f]" />
            <span>Moderate Divergence</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff7878]" />
            <span>Adversarial Failure Peak</span>
          </div>
        </div>
      </div>
    </div>
  );
}
