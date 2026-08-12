import * as THREE from 'three';
import { FOG_FAR, FOG_NEAR } from './config';

const SKY_COLOR = 0x87ceeb;

/**
 * Three.js のシーン・カメラ・レンダラーとリサイズ処理をまとめたもの。
 */
export class Renderer {
  readonly scene = new THREE.Scene();
  readonly camera: THREE.PerspectiveCamera;
  readonly renderer: THREE.WebGLRenderer;

  constructor(private readonly canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.scene.background = new THREE.Color(SKY_COLOR);
    this.scene.fog = new THREE.Fog(SKY_COLOR, FOG_NEAR, FOG_FAR);

    this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 260);

    // 影は使わない（小規模ワールドなので陰影だけで十分に立体に見える）
    const hemi = new THREE.HemisphereLight(0xffffff, 0x6b6b6b, 1.1);
    const sun = new THREE.DirectionalLight(0xffffff, 0.9);
    sun.position.set(0.6, 1, 0.35);
    this.scene.add(hemi, sun);

    this.resize();
    window.addEventListener('resize', this.resize);
    window.addEventListener('orientationchange', this.resize);
    // iOS Safari はアドレスバーの伸縮で resize が来ないことがある
    window.visualViewport?.addEventListener('resize', this.resize);
  }

  private readonly resize = (): void => {
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  };

  render(): void {
    this.renderer.render(this.scene, this.camera);
  }
}
