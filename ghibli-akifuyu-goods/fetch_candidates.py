# どんぐり共和国の公式通販から、秋冬向けの商品をキーワード検索でまとめて取得する
# 使い方: python3 fetch_candidates.py <保存フォルダ>
import sys,re,json,time,html,os,urllib.request,urllib.parse
O=sys.argv[1].rstrip('/')+'/'; os.makedirs(O+'img',exist_ok=True)
KW=['ブランケット','ひざ掛け','ストール','マフラー','手袋','ミトン','ニット','ルームシューズ','スリッパ','湯たんぽ','ボア','もこもこ','ふわふわ','あったか',
'腹巻','レッグウォーマー','靴下','ソックス','ネックウォーマー','帽子','イヤーマフ','カイロ','ポンチョ','ルームウェア','パジャマ','クリスマス','オーナメント','スノードーム',
'ハロウィン','秋','冬','雪','紅葉','どんぐり','きのこ','マグ','カレンダー','手帳','ダイアリー','加湿器','コート','フリース']
UA={'User-Agent':'Mozilla/5.0'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30).read().decode('utf-8','ignore')
items={}
for kw in KW:
    for page in range(1,6):
        q={'keyword':kw}; 
        if page>1: q['page']=page
        s=re.sub(r'<!--.*?-->','',get('https://www.donguri-sora.com/item_list.html?'+urllib.parse.urlencode(q)),flags=re.S)
        blocks=s.split('c-productList__item"')[1:]
        for b in blocks:
            m=re.search(r'href="https://www.donguri-sora.com/item/([^"]+)\.html" title="([^"]*)"',b); im=re.search(r'<img src="([^"]+)"',b); pr=re.search(r'([\d,]+)円',b)
            if not m: continue
            iid=m.group(1); name=html.unescape(m.group(2))
            soldout='品切' in re.sub(r'<[^>]+>','',b) and 'item_soldout' in b
            if iid not in items: items[iid]={'id':iid,'name':name,'price':(pr.group(1)+'円') if pr else '','img':im.group(1) if im else '','kw':[kw],'soldout':soldout}
            elif kw not in items[iid]['kw']: items[iid]['kw'].append(kw)
        time.sleep(0.6)
        if f'page={page+1}' not in s: break
    print(kw,len(items),flush=True)
json.dump(list(items.values()),open(O+'items_all.json','w'),ensure_ascii=False,indent=1)
