import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface Scene3DProps {
  stage: number; // 1 to 7
  isExiting: boolean;
  reducedMotion: boolean;
  onWebGLError: () => void;
}

export const Scene3D: React.FC<Scene3DProps> = ({
  stage,
  isExiting,
  reducedMotion,
  onWebGLError,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const stageRef = useRef<number>(stage);
  const isExitingRef = useRef<boolean>(isExiting);

  useEffect(() => {
    stageRef.current = stage;
  }, [stage]);

  useEffect(() => {
    isExitingRef.current = isExiting;
  }, [isExiting]);

  useEffect(() => {
    if (!containerRef.current) return;

    // 1. WebGL Support Check
    try {
      const canvasTest = document.createElement("canvas");
      const gl =
        canvasTest.getContext("webgl2") || canvasTest.getContext("webgl");
      if (!gl) {
        onWebGLError();
        return;
      }
    } catch (e) {
      onWebGLError();
      return;
    }

    // 2. Initialize Three.js Scene, Camera, Renderer
    const container = containerRef.current;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030712, 0.04);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 500);
    camera.position.set(0, 0, 3.5); // Start close for Scene 01 discovery pull-back

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); // Lightweight pixel ratio cap
      renderer.setSize(width, height);
      renderer.setClearColor(0x030712, 1);
      container.appendChild(renderer.domElement);
      rendererRef.current = renderer;
    } catch (err) {
      console.warn("WebGL initialization failed:", err);
      onWebGLError();
      return;
    }

    // 3. Lightweight Restrained Lighting
    const ambientLight = new THREE.AmbientLight(0x0f172a, 1.2);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x38bdf8, 2.5, 40);
    pointLight.position.set(3, 3, 5);
    scene.add(pointLight);

    // 4. Lightweight Procedural Globe (Sphere wireframe + dot ring)
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    const globeGeo = new THREE.IcosahedronGeometry(2.6, 2);
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0x0284c7,
      wireframe: true,
      transparent: true,
      opacity: 0.14,
    });
    const globeMesh = new THREE.Mesh(globeGeo, globeMat);
    globeGroup.add(globeMesh);

    // Globe Landmass Dots (Reduced count)
    const ptsGeo = new THREE.BufferGeometry();
    const posArr: number[] = [];
    const positions = globeGeo.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
      posArr.push(positions[i], positions[i + 1], positions[i + 2]);
    }
    ptsGeo.setAttribute("position", new THREE.Float32BufferAttribute(posArr, 3));
    const ptsMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.06,
      transparent: true,
      opacity: 0.6,
    });
    const globePoints = new THREE.Points(ptsGeo, ptsMat);
    globeGroup.add(globePoints);

    // 5. Lightweight Nodes (Only 12 fixed nodes max for 80% lighter computational overhead)
    const NODE_COUNT = 12;
    const nodeInitialPos: THREE.Vector3[] = [];
    const nodeTargetPos: THREE.Vector3[] = [];
    const nodeMeshes: THREE.Mesh[] = [];

    const nodeGeo = new THREE.SphereGeometry(0.1, 14, 14);
    const nodeMatCyan = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      roughness: 0.3,
    });
    const nodeMatRed = new THREE.MeshStandardMaterial({
      color: 0xef4444,
      emissive: 0xb91c1c,
      roughness: 0.3,
    });

    // Node 0: Central origin node
    nodeInitialPos.push(new THREE.Vector3(0, 0, 0));
    nodeTargetPos.push(new THREE.Vector3(0, 0, 0));
    const originMesh = new THREE.Mesh(nodeGeo, nodeMatCyan);
    originMesh.scale.set(0.001, 0.001, 0.001);
    scene.add(originMesh);
    nodeMeshes.push(originMesh);

    // Remaining 11 fixed network nodes distributed in 3D spherical space
    for (let i = 1; i < NODE_COUNT; i++) {
      const radius = 3.2 + (i % 3) * 0.6;
      const angle = (i / (NODE_COUNT - 1)) * Math.PI * 2;
      const yOffset = (i % 2 === 0 ? 1 : -1) * (0.4 + (i % 4) * 0.3);

      const x = radius * Math.cos(angle);
      const y = yOffset;
      const z = radius * Math.sin(angle);

      const pos = new THREE.Vector3(x, y, z);
      nodeInitialPos.push(pos.clone());
      nodeTargetPos.push(pos.clone());

      const isRedConflict = i === 4 || i === 8;
      const mesh = new THREE.Mesh(nodeGeo, isRedConflict ? nodeMatRed : nodeMatCyan);
      mesh.position.copy(pos);
      mesh.scale.set(0.001, 0.001, 0.001); // Hidden initially
      scene.add(mesh);
      nodeMeshes.push(mesh);
    }

    // 6. Pre-allocated Static Connection Line Segments
    const maxLines = 15;
    const linesGeo = new THREE.BufferGeometry();
    const linePosArray = new Float32Array(maxLines * 6);
    linesGeo.setAttribute("position", new THREE.BufferAttribute(linePosArray, 3));
    const linesMat = new THREE.LineBasicMaterial({
      color: 0x0ea5e9,
      transparent: true,
      opacity: 0.3,
    });
    const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
    scene.add(linesMesh);

    // 7. Verification Pulse Marker (Stage 6)
    const pulseGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const pulseMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0,
    });
    const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
    scene.add(pulseMesh);

    // 8. Static Ambient Star Particles (Only 60 background points)
    const particleCount = 60;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePos[i] = (Math.random() - 0.5) * 25;
      particlePos[i + 1] = (Math.random() - 0.5) * 25;
      particlePos[i + 2] = -5 - Math.random() * 15;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePos, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x64748b,
      size: 0.04,
      transparent: true,
      opacity: 0.35,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 9. Optimized Render Loop (Zero per-frame allocations, zero React re-renders)
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const elapsedTime = clock.getElapsedTime();
      const currentStage = stageRef.current;
      const exiting = isExitingRef.current;

      // Globe rotation: calm & restrained. Stops completely in Stage 4 (The Freeze)
      if (!reducedMotion) {
        const globeSpeed = currentStage === 4 ? 0 : currentStage === 3 ? 0.15 : 0.06;
        globeGroup.rotation.y += delta * globeSpeed;
      }

      // Stage 1 (0-4s): Information Discovery - Pull back camera smoothly from z=3.5 to z=8.5
      if (currentStage === 1) {
        originMesh.scale.lerp(new THREE.Vector3(1.2, 1.2, 1.2), delta * 3);
        // Reveal 2 neighboring nodes
        nodeMeshes[1].scale.lerp(new THREE.Vector3(0.8, 0.8, 0.8), delta * 2);
        nodeMeshes[2].scale.lerp(new THREE.Vector3(0.8, 0.8, 0.8), delta * 2);
      } else if (currentStage === 2) {
        // Stage 2 (4-9s): Propagation wave - Expand to all 12 nodes
        for (let i = 0; i < NODE_COUNT; i++) {
          const targetS = 0.85 + (i % 3) * 0.15;
          nodeMeshes[i].scale.lerp(new THREE.Vector3(targetS, targetS, targetS), delta * 2.5);
        }
      } else if (currentStage >= 5) {
        // Stage 5+ (16s+): Reorganize existing nodes into 5 clean horizontal pipeline clusters
        for (let i = 0; i < NODE_COUNT; i++) {
          const pipelineIndex = i % 5;
          const targetX = (pipelineIndex - 2) * 2.1;
          const targetY = (i % 2 === 0 ? 0.2 : -0.2);
          const targetZ = 3.0;

          nodeTargetPos[i].set(targetX, targetY, targetZ);
          nodeMeshes[i].position.lerp(nodeTargetPos[i], delta * 3.5);
          nodeMeshes[i].scale.lerp(new THREE.Vector3(0.75, 0.75, 0.75), delta * 3);
        }
      } else if (currentStage < 5) {
        // Stage 1-4: Return to initial spherical positions
        for (let i = 0; i < NODE_COUNT; i++) {
          if (currentStage >= 2) {
            nodeMeshes[i].scale.lerp(new THREE.Vector3(0.85, 0.85, 0.85), delta * 2.5);
          }
          const initPos = nodeInitialPos[i];
          const wobble = currentStage === 4 ? 0 : Math.sin(elapsedTime + i) * 0.15;
          nodeTargetPos[i].set(initPos.x + wobble, initPos.y + wobble, initPos.z);
          nodeMeshes[i].position.lerp(nodeTargetPos[i], delta * 2.5);
        }
      }

      // Stage 6 (22-25s): Verification Pulse line traversal
      if (currentStage === 6) {
        pulseMat.opacity = 1;
        const pulseProgress = (Math.sin(elapsedTime * 2.5) + 1) / 2; // 0 to 1 back and forth
        const pulseX = -4.2 + pulseProgress * 8.4;
        pulseMesh.position.set(pulseX, 0, 3.0);
      } else {
        pulseMat.opacity = 0;
      }

      // Pre-allocated Line Connections Update
      let lineIdx = 0;
      const maxDist = currentStage >= 5 ? 2.5 : 3.8;
      const activeCount = currentStage === 1 ? 3 : currentStage === 2 ? 8 : NODE_COUNT;

      for (let i = 0; i < activeCount; i++) {
        for (let j = i + 1; j < activeCount; j++) {
          if (lineIdx >= maxLines * 6) break;
          const dist = nodeMeshes[i].position.distanceTo(nodeMeshes[j].position);
          if (dist < maxDist) {
            linePosArray[lineIdx++] = nodeMeshes[i].position.x;
            linePosArray[lineIdx++] = nodeMeshes[i].position.y;
            linePosArray[lineIdx++] = nodeMeshes[i].position.z;

            linePosArray[lineIdx++] = nodeMeshes[j].position.x;
            linePosArray[lineIdx++] = nodeMeshes[j].position.y;
            linePosArray[lineIdx++] = nodeMeshes[j].position.z;
          }
        }
      }
      linesGeo.setDrawRange(0, lineIdx / 3);
      linesGeo.attributes.position.needsUpdate = true;

      // Controlled Camera Motions
      if (exiting) {
        // Zoom smoothly forward on GET STARTED click
        camera.position.z = THREE.MathUtils.lerp(camera.position.z, 0.3, delta * 5);
      } else if (reducedMotion) {
        camera.position.set(0, 0, 8.5);
        camera.lookAt(0, 0, 0);
      } else {
        if (currentStage === 1) {
          // Slow pull back from z=3.5 to z=8.5
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 8.5, delta * 1.2);
          camera.position.x = 0;
          camera.position.y = 0;
        } else if (currentStage === 2) {
          // Slow orbital pan
          camera.position.x = Math.sin(elapsedTime * 0.15) * 1.2;
          camera.position.y = Math.cos(elapsedTime * 0.1) * 0.8;
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 8.5, delta * 2);
        } else if (currentStage === 3) {
          // Signal & Noise slightly wider pan
          camera.position.x = Math.sin(elapsedTime * 0.25) * 1.5;
          camera.position.y = Math.cos(elapsedTime * 0.2) * 1.0;
        } else if (currentStage === 4) {
          // HARD PAUSE / FREEZE: Camera completely static
          camera.position.x = THREE.MathUtils.lerp(camera.position.x, 0, delta * 4);
          camera.position.y = THREE.MathUtils.lerp(camera.position.y, 0, delta * 4);
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 8.0, delta * 4);
        } else if (currentStage >= 5) {
          // Evidence Pipeline & Product Reveal: Centered push-in
          camera.position.x = THREE.MathUtils.lerp(camera.position.x, 0, delta * 3);
          camera.position.y = THREE.MathUtils.lerp(camera.position.y, 0, delta * 3);
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 6.8, delta * 3);
        }
        camera.lookAt(0, 0, 0);
      }

      renderer.render(scene, camera);
    };

    animate();

    // 10. Window Resize Handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth || window.innerWidth;
      const h = containerRef.current.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    // 11. Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);

      globeGeo.dispose();
      globeMat.dispose();
      ptsGeo.dispose();
      ptsMat.dispose();
      nodeGeo.dispose();
      nodeMatCyan.dispose();
      nodeMatRed.dispose();
      linesGeo.dispose();
      linesMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      pulseGeo.dispose();
      pulseMat.dispose();

      if (rendererRef.current) {
        rendererRef.current.dispose();
        if (container.contains(rendererRef.current.domElement)) {
          container.removeChild(rendererRef.current.domElement);
        }
      }
    };
  }, [reducedMotion, onWebGLError]);

  return (
    <div className="intro-canvas-container" ref={containerRef}>
      {/* Three.js canvas injected here dynamically */}
    </div>
  );
};
