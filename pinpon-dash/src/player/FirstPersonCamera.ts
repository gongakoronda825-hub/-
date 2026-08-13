import * as THREE from 'three';
import { FOV, FOV_DASH, PITCH_LIMIT } from '../core/config';

/**
 * 一人称カメラ。yaw（左右）と pitch（上下）を持ち、毎フレーム位置と向きを組み立てる。
 *
 * 回転順は YXZ。先に yaw、次に pitch を掛けることで、上下を向いても
 * 水平の向きが傾かない（＝ロールが出ない）。
 *
 * このゲームは塀を越えられないので、上下の視点は「見上げる／足元を見る」ためだけ。
 * ±85° で止めてある。
 */
export class FirstPersonCamera {
  /** 左右。ラジアン。 */
  yaw = 0;
  /** 上下。ラジアン。+ が上向き。±PITCH_LIMIT でクランプされる。 */
  pitch = 0;

  private readonly forward = new THREE.Vector3();
  private readonly right = new THREE.Vector3();

  /** ダッシュ中に画角を広げるための、現在の視野角。 */
  private fov = FOV;

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
   * ダッシュ中は画角を広げてスピード感を出す。
   * 切り替えは補間する（一気に変えると酔う）。
   */
  updateFov(dt: number, dashing: boolean): void {
    const target = dashing ? FOV_DASH : FOV;
    this.fov += (target - this.fov) * Math.min(dt * 6, 1);
    if (Math.abs(this.camera.fov - this.fov) > 0.01) {
      this.camera.fov = this.fov;
      this.camera.updateProjectionMatrix();
    }
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
