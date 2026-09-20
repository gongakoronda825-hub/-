/*
 * 時代テーブル。
 *
 * この街は「TikTokのフォロワー1人 = 人口1人」で発展する。
 * 人口がどの時代に相当するかはこのテーブルだけが知っていて、
 * 描画側は era.scene を見るだけでよい、という分離にしてある。
 *
 * buildings / infrastructure / jobs / life は将来の実装用のメモ。
 * 今回のMVPでは prehistoric（人口0人）だけが scene を持つ。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});

  const ERAS = [
    {
      id: 'prehistoric',
      name: '人類誕生前',
      world: '恐竜時代',
      minPopulation: 0,
      maxPopulation: 0,
      scene: 'prehistoric',
      buildings: [],
      infrastructure: [],
      jobs: [],
      life: [],
    },
    {
      id: 'jomon',
      name: '縄文',
      world: '小さな原始集落',
      minPopulation: 1,
      maxPopulation: 10,
      scene: 'jomon',
      buildings: ['竪穴住居'],
      infrastructure: ['けもの道'],
      jobs: ['狩猟', '採集'],
      life: ['焚き火'],
    },
    {
      id: 'yayoi',
      name: '弥生',
      world: '稲作を始めた村',
      minPopulation: 11,
      maxPopulation: 50,
      scene: 'yayoi',
      buildings: ['竪穴住居', '高床倉庫', '水田'],
      infrastructure: ['小道', '用水路'],
      jobs: ['農業'],
      life: ['村'],
    },
    {
      id: 'kofun',
      name: '古墳',
      world: '共同体が発展',
      minPopulation: 51,
      maxPopulation: 100,
      scene: 'kofun',
      buildings: ['豪族の館', '古墳', '水田'],
      infrastructure: ['道', '橋'],
      jobs: ['農業', '職人'],
      life: ['共同体'],
    },
    {
      id: 'nara',
      name: '奈良',
      world: '寺・市場が生まれる',
      minPopulation: 101,
      maxPopulation: 300,
      scene: 'nara',
      buildings: ['寺', '市場', '役所'],
      infrastructure: ['街道', '水路'],
      jobs: ['農業', '職人', '商人'],
      life: ['市場'],
    },
    {
      id: 'heian',
      name: '平安',
      world: '屋敷・庭園・文化',
      minPopulation: 301,
      maxPopulation: 500,
      scene: 'heian',
      buildings: ['寝殿造の屋敷', '庭園', '寺'],
      infrastructure: ['街道', '橋'],
      jobs: ['貴族', '職人', '商人'],
      life: ['雅な暮らし'],
    },
    {
      id: 'kamakura',
      name: '鎌倉',
      world: '武家・城・城下町',
      minPopulation: 501,
      maxPopulation: 1000,
      scene: 'kamakura',
      buildings: ['武家屋敷', '城', '町家'],
      infrastructure: ['街道', '橋', '堀'],
      jobs: ['武士', '職人', '商人'],
      life: ['城下町'],
    },
    {
      id: 'muromachi',
      name: '室町',
      world: '商業都市',
      minPopulation: 1001,
      maxPopulation: 2000,
      scene: 'muromachi',
      buildings: ['町家', '市', '寺', '城'],
      infrastructure: ['街道', '水路', '橋'],
      jobs: ['商人', '職人', '武士'],
      life: ['市場', '町'],
    },
    {
      id: 'edo',
      name: '江戸',
      world: '大規模な城下町',
      minPopulation: 2001,
      maxPopulation: 3000,
      scene: 'edo',
      buildings: ['天守', '長屋', '商店', '橋'],
      infrastructure: ['街道', '堀', '水路'],
      jobs: ['武士', '商人', '職人'],
      life: ['城下町'],
    },
    {
      id: 'meiji',
      name: '明治',
      world: '鉄道・学校・近代化',
      minPopulation: 3001,
      maxPopulation: 5000,
      scene: 'meiji',
      buildings: ['レンガ倉庫', '学校', '駅'],
      infrastructure: ['鉄道', '道路', '電柱'],
      jobs: ['会社員', '工場労働者', '商人'],
      life: ['近代都市'],
    },
    {
      id: 'taisho',
      name: '大正',
      world: '百貨店・映画館・路面電車',
      minPopulation: 5001,
      maxPopulation: 7000,
      scene: 'taisho',
      buildings: ['百貨店', '映画館', '洋館'],
      infrastructure: ['路面電車', '鉄道', '電柱'],
      jobs: ['会社員', '工場労働者'],
      life: ['モダンな街'],
    },
    {
      id: 'showa',
      name: '昭和',
      world: '商店街・駅・工場・自動車',
      minPopulation: 7001,
      maxPopulation: 10000,
      scene: 'showa',
      buildings: ['商店街', '駅', '工場', '団地'],
      infrastructure: ['鉄道', '道路', '電柱', '橋'],
      jobs: ['会社員', '工場労働者'],
      life: ['昭和の都市生活'],
    },
  ];

  /** 人口から時代を求める。テーブルの範囲を超えた人口は最後の時代に丸める。 */
  function getEra(population) {
    const pop = Math.max(0, Math.floor(population || 0));
    for (let i = 0; i < ERAS.length; i++) {
      if (pop >= ERAS[i].minPopulation && pop <= ERAS[i].maxPopulation) return ERAS[i];
    }
    return ERAS[ERAS.length - 1];
  }

  /** 次の時代（最後の時代なら null）。将来「あと◯人で◯◯時代」を出すため。 */
  function getNextEra(population) {
    const i = ERAS.indexOf(getEra(population));
    return i >= 0 && i < ERAS.length - 1 ? ERAS[i + 1] : null;
  }

  /** 次の時代まであと何人か。 */
  function populationToNextEra(population) {
    const next = getNextEra(population);
    if (!next) return 0;
    return Math.max(0, next.minPopulation - Math.max(0, Math.floor(population || 0)));
  }

  FT.eras = { ERAS, getEra, getNextEra, populationToNextEra };
})(window);
