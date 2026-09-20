/*
 * 演出。動画の頭から流れる台本をここに置く。
 *
 * 台本は時代ごとに持てる形にしてある（今は人類誕生前だけ）。
 * 人口が増えて時代が変われば、その時代の台本が流れる。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});

  const SCRIPTS = {
    prehistoric: [
      { t: 0.2, act: 'hud' },
      { t: 3.6, act: 'say', text: 'この街には、まだ誰も住んでいません。', hold: 4.4 },
      { t: 8.6, act: 'flyby' },
      { t: 13.4, act: 'say', text: '1人目の住民を待っています。', hold: 0 },
      { t: 15.6, act: 'replay' },
    ],
  };

  function create(opts) {
    const dom = opts.dom;
    const cfg = opts.config;
    const era = opts.era;
    const cues = (SCRIPTS[era.id] || []).slice().sort((a, b) => a.t - b.t);

    let t = 0;
    let next = 0;
    let hideAt = -1;

    function setSubtitle(text) {
      dom.subtitleText.textContent = text;
      dom.subtitle.classList.add('is-on');
    }
    function hideSubtitle() {
      dom.subtitle.classList.remove('is-on');
    }

    function fillHud() {
      const pop = cfg.POPULATION;
      dom.population.textContent = pop.toLocaleString('ja-JP');
      dom.followers.textContent = cfg.FOLLOWERS.toLocaleString('ja-JP');
      dom.era.textContent = era.name;
      dom.eraWorld.textContent = era.world;
      const rest = FT.eras.populationToNextEra(pop);
      const nextEra = FT.eras.getNextEra(pop);
      dom.next.textContent = nextEra
        ? `フォロワー ${rest.toLocaleString('ja-JP')}人 で ${nextEra.name}時代へ`
        : '';
    }

    function reset() {
      t = 0;
      next = 0;
      hideAt = -1;
      hideSubtitle();
      dom.replay.classList.remove('is-on');
      dom.stage.classList.remove('is-open');
      // 次のフレームで再点灯させ、フェードインをやり直す
      requestAnimationFrame(() => dom.stage.classList.add('is-open'));
    }

    function update(dt) {
      t += dt;
      while (next < cues.length && t >= cues[next].t) {
        const cue = cues[next++];
        if (cue.act === 'hud') dom.hud.classList.add('is-on');
        else if (cue.act === 'say') {
          setSubtitle(cue.text);
          hideAt = cue.hold > 0 ? t + cue.hold : -1;
        } else if (cue.act === 'flyby') opts.onCue && opts.onCue('flyby');
        else if (cue.act === 'replay') dom.replay.classList.add('is-on');
      }
      if (hideAt > 0 && t >= hideAt) {
        hideAt = -1;
        hideSubtitle();
      }
    }

    fillHud();
    return { update, reset, fillHud, get time() { return t; } };
  }

  FT.director = { create, SCRIPTS };
})(window);
