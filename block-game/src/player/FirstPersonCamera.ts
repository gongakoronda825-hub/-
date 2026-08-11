import * as THREE from 'three';
import { PITCH_LIMIT } from '../core/config';

/**
 * 一人称カメラ。yaw（左右）と pitch（上下）を持ち、毎フレーム位置と向きを組み立てる。
 *
 * 回転順は YXZ。先に yaw、次に pitch を掛けることで、上下を向いても
 * 水平の向きが傾かない（＝ロールが出ない）。
 */
export class FirstPersonCamera {
  /** 左右。ラジアン。増える方向が左回り（Three.js の +Y 回り）。 */
  yaw = 0;
  /** 上下。ラジアン。+ が上向き。±PITCH_LIMIT でクランプされる。 */
  pitch = 0;

  private readonly forward = new THREE.Vector3();
  private readonly right = new THREE.Vector3();

  constructor(private readonly camera: THREE.PerspectiveCamera) {
    this.camera.rotation.order = 'YXZ';
  }

  /** 視点入力（画面上の移動量）を角度に反映する。 */
  rotate(deltaYaw: number, deltaPitch: number): void {
    this.yaw += deltaYaw;
    this.pitch = Math.max(-PITCH_LIMIT, Math.min(PITCH_LIMIT, this.pitch + deltaPitch));
  }

  /** 目線の位置と向きをカメラへ書き込む。 */
  apply(eyeX: number, eyeY: number, eyeZ: number): void {
    this.camera.position.set(eyeX, eyeY, eyeZ);
    this.camera.rotation.set(this.pitch, this.yaw, 0);
  }

  /**
   * 移動用の「前方」。水平面に投影した向き（pitch を無視）。
   * 上を向いたまま前進しても浮き上がらないようにするため。
   */
  getHorizontalForward(target = this.forward): THREE.Vector3 {
    return target.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
  }

  /** 移動用の「右方向」。前方を Y 軸まわりに -90° 回したもの。 */
  getHorizontalRight(target = this.right): THREE.Vector3 {
    return target.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw));
  }
}
