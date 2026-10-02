import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface Scene3DProps {
  stage: number; // 1 to 6
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

  // Keep refs up to date for animation loop without re-instantiating scene
  useEffect(() => {
    stageRef.current = stage;
  }, [stage]);

  useEffect(() => {
    isExitingRef.current = isExiting;
  }, [isExiting]);

  useEffect(() => {
    if (!containerRef.current) return;

    // 1. Test WebGL context availability
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

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(0, 0, 10);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(width, height);
      renderer.setClearColor(0x030712, 1);
      container.appendChild(renderer.domElement);
      rendererRef.current = renderer;
    } catch (err) {
      console.warn("WebGL initialization failed:", err);
      onWebGLError();
      return;
    }

    // 3. Create Lighting
    const ambientLight = new THREE.AmbientLight(0x0f172a, 1.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x38bdf8, 3, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const redNoiseLight = new THREE.PointLight(0xef4444, 0, 40);
    redNoiseLight.position.set(-5, -2, 5);
    scene.add(redNoiseLight);

    // 4. Create Procedural Globe (Icosahedron wireframe + point cloud)
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    const globeGeo = new THREE.IcosahedronGeometry(3, 3);
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0x0284c7,
      wireframe: true,
      transparent: true,
      opacity: 0.25,
    });
    const globeMesh = new THREE.Mesh(globeGeo, globeMat);
    globeGroup.add(globeMesh);

    // Globe surface dot landmass representation
    const ptsGeo = new THREE.BufferGeometry();
    const posArr: number[] = [];
    const positions = globeGeo.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
      posArr.push(positions[i], positions[i + 1], positions[i + 2]);
    }
    ptsGeo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(posArr, 3)
    );
    const ptsMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.08,
      transparent: true,
      opacity: 0.8,
    });
    const globePoints = new THREE.Points(ptsGeo, ptsMat);
    globeGroup.add(globePoints);

    // Atmosphere Glow Shell
    const atmoGeo = new THREE.SphereGeometry(3.35, 32, 32);
    const atmoMat = new THREE.MeshBasicMaterial({
      color: 0x0ea5e9,
      transparent: true,
      opacity: 0.08,
      side: THREE.BackSide,
    });
    const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    globeGroup.add(atmoMesh);

    // 5. Create Floating Network Nodes & Connections
    const nodeCount = 30;
    const nodeInitialPositions: THREE.Vector3[] = [];
    const nodeTargetPositions: THREE.Vector3[] = [];
    const nodeMeshes: THREE.Mesh[] = [];

    const nodeGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const nodeMatCyan = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      roughness: 0.2,
    });
    const nodeMatRed = new THREE.MeshStandardMaterial({
      color: 0xef4444,
      emissive: 0xb91c1c,
      roughness: 0.2,
    });

    // Generate 3D positions in spherical space around the globe
    for (let i = 0; i < nodeCount; i++) {
      const radius = 4.2 + Math.random() * 2.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      const initPos = new THREE.Vector3(x, y, z);
      nodeInitialPositions.push(initPos.clone());
      nodeTargetPositions.push(initPos.clone());

      const isRedNoiseNode = i % 5 === 0;
      const mesh = new THREE.Mesh(
        nodeGeo,
        isRedNoiseNode ? nodeMatRed : nodeMatCyan
      );
      mesh.position.copy(initPos);
      scene.add(mesh);
      nodeMeshes.push(mesh);
    }

    // Dynamic Line Connections Geometry
    const linesGeo = new THREE.BufferGeometry();
    const linesMat = new THREE.LineBasicMaterial({
      color: 0x0ea5e9,
      transparent: true,
      opacity: 0.35,
    });
    const linePositions = new Float32Array(nodeCount * nodeCount * 6);
    linesGeo.setAttribute(
      "position",
      new THREE.BufferAttribute(linePositions, 3)
    );
    const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
    scene.add(linesMesh);

    // 6. Ambient Particle Stars
    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePos[i] = (Math.random() - 0.5) * 30;
      particlePos[i + 1] = (Math.random() - 0.5) * 30;
      particlePos[i + 2] = (Math.random() - 0.5) * 30;
    }
    particleGeo.setAttribute(
      "position",
      new THREE.BufferAttribute(particlePos, 3)
    );
    const particleMat = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.05,
      transparent: true,
      opacity: 0.5,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 7. Animation Loop with Stage-Driven Camera & Node Behavior
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const elapsedTime = clock.getElapsedTime();
      const currentStage = stageRef.current;
      const exiting = isExitingRef.current;

      // Rotate Globe smoothly
      if (!reducedMotion) {
        globeGroup.rotation.y +=
          delta * (currentStage === 3 ? 0.35 : currentStage === 4 ? 0.02 : 0.12);
        particles.rotation.y -= delta * 0.02;
      }

      // Handle Stage 3 Noise Light intensity
      if (currentStage === 3) {
        redNoiseLight.intensity = THREE.MathUtils.lerp(
          redNoiseLight.intensity,
          4,
          0.05
        );
      } else {
        redNoiseLight.intensity = THREE.MathUtils.lerp(
          redNoiseLight.intensity,
          0,
          0.05
        );
      }

      // Stage 5 Pipeline Alignment vs Stage 1-4 Floating Space
      for (let i = 0; i < nodeCount; i++) {
        const mesh = nodeMeshes[i];

        if (currentStage >= 5) {
          // Calculate linear pipeline positions: CLAIM -> WEB -> SOURCE -> COMPARISON -> VERIFY
          const pipelineIndex = i % 5;
          const targetX = (pipelineIndex - 2) * 2.2;
          const targetY = 0;
          const targetZ = 3.5;

          nodeTargetPositions[i].set(
            targetX + (Math.random() - 0.5) * 0.2,
            targetY + (Math.random() - 0.5) * 0.2,
            targetZ
          );
        } else {
          // Floating orbit around globe
          const initPos = nodeInitialPositions[i];
          const phase = elapsedTime * (currentStage === 3 ? 2.5 : 0.8) + i;
          nodeTargetPositions[i].set(
            initPos.x + Math.sin(phase) * 0.4,
            initPos.y + Math.cos(phase) * 0.4,
            initPos.z
          );
        }

        mesh.position.lerp(nodeTargetPositions[i], delta * 3);
      }

      // Update Connection Lines between nearest nodes
      let lineIdx = 0;
      const linePosArray = linesGeo.attributes.position.array as Float32Array;
      const maxDistance = currentStage === 5 ? 3.0 : 4.5;

      for (let i = 0; i < nodeCount; i++) {
        for (let j = i + 1; j < nodeCount; j++) {
          const dist = nodeMeshes[i].position.distanceTo(
            nodeMeshes[j].position
          );
          if (dist < maxDistance) {
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

      // Stage-specific Camera Motion
      if (exiting) {
        // Zoom forward through center on transition to analyzer
        camera.position.z = THREE.MathUtils.lerp(camera.position.z, 0.5, delta * 4);
      } else if (reducedMotion) {
        camera.position.set(0, 0, 10);
        camera.lookAt(0, 0, 0);
      } else {
        if (currentStage === 1) {
          camera.position.x = Math.sin(elapsedTime * 0.15) * 1.5;
          camera.position.y = Math.cos(elapsedTime * 0.1) * 1.0;
          camera.position.z = 10;
        } else if (currentStage === 2) {
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 8.5, delta * 2);
        } else if (currentStage === 3) {
          camera.position.x = (Math.random() - 0.5) * 0.15;
          camera.position.y = (Math.random() - 0.5) * 0.15;
        } else if (currentStage === 4) {
          camera.position.set(0, 0, 9);
        } else if (currentStage >= 5) {
          camera.position.x = THREE.MathUtils.lerp(camera.position.x, 0, delta * 3);
          camera.position.y = THREE.MathUtils.lerp(camera.position.y, 0, delta * 3);
          camera.position.z = THREE.MathUtils.lerp(camera.position.z, 7.5, delta * 3);
        }
        camera.lookAt(0, 0, 0);
      }

      renderer.render(scene, camera);
    };

    animate();

    // 8. Handle Window Resize
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth || window.innerWidth;
      const h = containerRef.current.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    // 9. Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);

      globeGeo.dispose();
      globeMat.dispose();
      ptsGeo.dispose();
      ptsMat.dispose();
      atmoGeo.dispose();
      atmoMat.dispose();
      nodeGeo.dispose();
      nodeMatCyan.dispose();
      nodeMatRed.dispose();
      linesGeo.dispose();
      linesMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();

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
