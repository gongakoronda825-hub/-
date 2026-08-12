/** 支払い履歴の先頭に出すアイコン。内容の文字列から推測する。 */
const RULES: { icon: string; keywords: string[] }[] = [
  { icon: '🚕', keywords: ['タクシー', 'たくしー', 'taxi', '電車', 'バス', '交通', '移動'] },
  { icon: '🍴', keywords: ['レストラン', '食事', 'ごはん', 'ランチ', 'ディナー', '朝食', '昼食', '夕食', 'food'] },
  { icon: '🏨', keywords: ['ホテル', '宿', '民泊', 'hotel'] },
  { icon: '🎟', keywords: ['観光', 'チケット', '入場', '美術館', '博物館', 'ツアー'] },
  { icon: '🛍', keywords: ['買い物', 'ショッピング', '土産', 'みやげ', 'コンビニ'] },
  { icon: '☕', keywords: ['カフェ', 'コーヒー', 'お茶', 'cafe'] },
  { icon: '🍺', keywords: ['飲み', '居酒屋', 'バー', 'ビール'] },
];

export function iconForDescription(description: string): string {
  const text = description.toLowerCase();
  for (const rule of RULES) {
    if (rule.keywords.some((k) => text.includes(k.toLowerCase()))) {
      return rule.icon;
    }
  }
  return '💳';
}
