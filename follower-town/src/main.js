/*
 * 起動と毎フレームの組み立て。
 *
 *   人口 → 時代 → その時代の世界 → 生き物 → 演出
 * という順に組み立てている。人口0人の今は「恐竜時代の自然」だけが建つ。
 */
(function (global) {
  'use strict';
  const FT = global.FT;
  const R = FT.rng;

  const dom = {
    stage: document.getElementById('stage'),
    canvas: document.getElementById('screen'),
    boot: document.getElementById('boot'),
    hud: document.getElementById('hud'),
    population: document.getElementById('pop-value'),
    followers: document.getElementById('fol-value'),
    era: document.getElementById('era-value'),
    eraWorld: document.getElementById('era-world'),
    next: document.getElementById('next-era'),
    subtitle: document.getElementById('subtitle'),
    subtitleText: document.getElementById('subtitle-text'),
    replay: document.getElementById('replay'),
  };

  const cfg = FT.config;
  const era = FT.eras.getEra(cfg.POPULATION);
  const display = FT.display.create(dom.canvas);
  const ctx = display.ctx;

  let world = null, propList = null, sprites = null, life = null, director = null;
  let clouds = [], cloudShadows = [];
  let motes = [];
  const cam = { x: 0, y: 0 };
  const base = { x: 0, y: 0 };
  let started = 0;

  function build() {
    const t0 = performance.now();
    // 今回のMVPで実装したのは人類誕生前の風景だけ。
    // 将来ここで era.scene ごとの世界の組み立てに分岐させる。
    if (era.scene !== 'prehistoric' && global.console) {
      global.console.warn(
        `[follower-town] ${era.name}時代の街はまだ未実装です。恐竜時代の地形で表示します。`
      );
    }
    const size = Math.max(900, display.w + 200, display.h + 200);
    world = FT.terrain.create({ seed: cfg.SEED, width: size, height: size });

    const catalog = FT.props.buildCatalog(cfg.SEED);
    propList = FT.props.scatter(world, catalog, cfg.SEED);
    cloudShadows = FT.props.buildCloudShadows(cfg.SEED, 4);

    sprites = FT.species.bakeAll();
    life = FT.life.createLife(world, sprites, cfg.SEED, cfg);

    // 画面中央に当たるタイルを中心に群れを置く
    const k = (world.height / 2 - world.originY) / (world.TH / 2);
    const d = (world.width / 2 - world.originX) / (world.TW / 2);
    life.populate({ tx: (k + d) / 2, ty: (k - d) / 2 });

    const rnd = R.mulberry32(cfg.SEED + 313);
    clouds = cloudShadows.map((img, i) => ({
      img,
      x: rnd() * world.width,
      y: rnd() * world.height,
      vx: 5 + rnd() * 4,
      vy: 1.4 + rnd() * 1.2,
    }));
    motes = [];
    for (let i = 0; i < 46; i++) {
      motes.push({
        x: rnd() * world.width,
        y: rnd() * world.height,
        p: rnd() * Math.PI * 2,
        s: 0.4 + rnd() * 0.8,
        a: 0.25 + rnd() * 0.5,
      });
    }

    base.x = world.width / 2 - display.w / 2;
    base.y = world.height / 2 - display.h / 2;

    director = FT.director.create({
      dom, config: cfg, era,
      onCue(name) {
        if (name === 'flyby') {
          const view = viewRect();
          life.spawnFlyer({ view, dir: 1, y: view.y + view.h * 0.30, alt: 34, speed: 46 });
          life.spawnFlyer({ view, dir: 1, y: view.y + view.h * 0.38, alt: 26, speed: 40 });
          life.spawnFlyer({ view, dir: 1, y: view.y + view.h * 0.22, alt: 44, speed: 52 });
        }
      },
    });

    dom.replay.addEventListener('click', () => director.reset());
    // 動作確認用。コンソールから世界の中身を覗ける。
    FT.debug = { world, life, display, cam, propList, sprites, director };
    dom.boot.classList.add('is-done');
    dom.stage.classList.add('is-open');

    if (global.console && global.console.info) {
      global.console.info(
        `[follower-town] 人口 ${cfg.POPULATION} / 時代 ${era.name} / 生成 ${Math.round(performance.now() - t0)}ms`
      );
    }

    // 恐竜が歩き出した状態から始めるため、少し空回しする
    for (let i = 0; i < 90; i++) life.update(1 / 30, viewRect());

    requestAnimationFrame(loop);
  }

  function viewRect() {
    return { x: cam.x, y: cam.y, w: display.w, h: display.h };
  }

  function updateCamera(t) {
    const maxX = Math.max(0, world.width - display.w);
    const maxY = Math.max(0, world.height - display.h);
    const dx = Math.sin((t / cfg.CAMERA_PERIOD_X) * Math.PI * 2) * cfg.CAMERA_DRIFT_X;
    const dy = Math.sin((t / cfg.CAMERA_PERIOD_Y) * Math.PI * 2 + 1.1) * cfg.CAMERA_DRIFT_Y;
    cam.x = Math.round(R.clamp(base.x + dx, 0, maxX));
    cam.y = Math.round(R.clamp(base.y + dy, 0, maxY));
  }

  const drawList = [];

  function render(t) {
    const w = display.w, h = display.h;
    ctx.drawImage(world.canvas, cam.x, cam.y, w, h, 0, 0, w, h);

    // 雲の影
    for (const c of clouds) {
      const x = Math.round(c.x - cam.x), y = Math.round(c.y - cam.y);
      if (x > w || y > h || x + c.img.width < 0 || y + c.img.height < 0) continue;
      ctx.drawImage(c.img, x, y);
    }

    // 水面のきらめき
    const sp = world.sparkles;
    ctx.fillStyle = '#a8dde5';
    for (let i = 0; i < sp.length; i++) {
      const s = sp[i];
      const x = s.x - cam.x, y = s.y - cam.y;
      if (x < -6 || y < -4 || x > w + 6 || y > h + 4) continue;
      const ph = (t * 0.32 + s.phase) % 1;
      if (ph > 0.22) continue;
      const k = ph / 0.22;
      const len = Math.max(1, Math.round(s.len * Math.sin(k * Math.PI)));
      ctx.globalAlpha = 0.22 + 0.34 * Math.sin(k * Math.PI);
      ctx.fillRect(Math.round(x), Math.round(y), len, 1);
    }
    ctx.globalAlpha = 1;

    life.drawFlyerShadows(ctx, cam);

    // 植物と恐竜を奥から順に
    drawList.length = 0;
    const x0 = cam.x - 40, x1 = cam.x + w + 40, y0 = cam.y - 70, y1 = cam.y + h + 40;
    for (let i = 0; i < propList.length; i++) {
      const p = propList[i];
      if (p.x < x0 || p.x > x1 || p.y < y0 || p.y > y1) continue;
      drawList.push(p);
    }
    life.collect(drawList, viewRect());
    drawList.sort((a, b) => a.depth - b.depth);
    for (let i = 0; i < drawList.length; i++) {
      const e = drawList[i];
      if (e.agent) {
        life.drawAgent(ctx, e.agent, cam);
      } else {
        const s = e.sprite;
        ctx.drawImage(s.img, Math.round(e.x - s.ax - cam.x), Math.round(e.y - s.ay - cam.y));
      }
    }

    life.drawFlyers(ctx, cam);

    // 陽に透ける小さな虫や胞子
    ctx.fillStyle = '#eef6d8';
    for (const m of motes) {
      const x = Math.round(m.x + Math.sin(t * m.s + m.p) * 9 - cam.x);
      const y = Math.round(m.y + Math.cos(t * m.s * 0.7 + m.p) * 5 - cam.y);
      if (x < 0 || y < 0 || x >= w || y >= h) continue;
      ctx.globalAlpha = m.a * (0.55 + 0.45 * Math.sin(t * 2.2 + m.p));
      ctx.fillRect(x, y, 1, 1);
    }
    ctx.globalAlpha = 1;
  }

  let last = 0;
  function loop(now) {
    if (!started) started = now;
    const t = (now - started) / 1000;
    let dt = last ? (now - last) / 1000 : 1 / 60;
    last = now;
    if (dt > 0.1) dt = 0.1;

    updateCamera(t);
    for (const c of clouds) {
      c.x += c.vx * dt;
      c.y += c.vy * dt;
      if (c.x > world.width + 40) { c.x = -c.img.width - 40; }
      if (c.y > world.height + 40) { c.y = -c.img.height - 40; }
    }
    life.update(dt, viewRect());
    director.update(dt);
    render(t);
    requestAnimationFrame(loop);
  }

  // 生成に少し時間がかかるので、まず「生成中」を描かせてから作る
  requestAnimationFrame(() => requestAnimationFrame(build));
})(window);
