import * as THREE from 'three';
import { CAMERA_FAR, FOG_FAR, FOG_NEAR, FOV, SKY_COLOR } from './config';

/**
 * Three.js のシーン・カメラ・レンダラーとリサイズ処理。
 *
 * 影は落とさない。ローポリの箱だけの街なので、環境光と平行光の陰影で十分
 * 立体に見えるうえ、スマホでシャドウマップを焼くのは高くつく。
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

    this.camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, CAMERA_FAR);

    // 空の色を弱く回り込ませて、影側が真っ黒にならないようにする
    const hemi = new THREE.HemisphereLight(0xffffff, 0xa89c88, 1.35);
    const sun = new THREE.DirectionalLight(0xfff4e0, 1.0);
    sun.position.set(0.5, 1, 0.3);
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
