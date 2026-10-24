import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1]
L=[('hook','アリエッティ、アイマックスで観る意味ある？'),
('c1','迷ってた人も、没入感がすごくて、ちゃんとコビトになってたらしい。'),
('c2','アリエッティは、小さい音と、細かい絵が主役。アイマックスで変わるのが、ちょうどその2つ。'),
('c3','スクリーンが大きくて、ゆるく湾曲してるから、コビトから見た部屋の広さが、そのまま伝わる。'),
('c4','横と上にもスピーカーがあって、雨、風、虫の声が、まわりから聞こえる。ニーヤのゴロゴロまで、って声も。'),
('c5','ジブリ監修のヨンケーリマスター版を、レーザー映写機で映すから、明るくて色が深い。水のつぶや、花の色まで見えたらしい。'),
('c6','セシル・コルベルの歌も、アイマックスの音で。これ目当てでもいいと思う。'),
('c7','アリエッティの側で観てたはずが、自分はショウの側だって気づいて、ちょっとしんどい。でも、小さい世界ってきれいだなって思える。'),
('c8','アイマックスで観られるのは、11月2日まで。30日からの全国拡大上映は、アイマックスじゃないので注意。迷ってる人に、送ってあげて。'),
('fol','ジブリの最新情報を発信中。フォローしてね！')]
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for _ in range(90):
    try: op.open('http://127.0.0.1:50021/version').read(); break
    except Exception: time.sleep(2)
for k,txt in L:
    if len(sys.argv)>2 and k not in sys.argv[2:]: continue
    q=json.loads(op.open(urllib.request.Request('http://127.0.0.1:50021/audio_query?'+urllib.parse.urlencode({'text':txt,'speaker':SP}),method='POST')).read())
    q['speedScale']=1.15; q['prePhonemeLength']=0.0; q['postPhonemeLength']=0.05; q['outputSamplingRate']=44100
    for ap in q['accent_phrases']:
        if ap.get('pause_mora'): ap['pause_mora']['vowel_length']=min(ap['pause_mora']['vowel_length'],0.18)
    wav=op.open(urllib.request.Request(f'http://127.0.0.1:50021/synthesis?speaker={SP}',data=json.dumps(q).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
    p=f'{V}narr/{k}.wav'; open(p,'wb').write(wav)
    with wave.open(p) as w: sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
    nz=np.where(np.abs(a)>300)[0]; a=a[max(0,nz[0]-400):nz[-1]+2000]
    with wave.open(p,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    # 話している部分を目立たせるため、アクセント句ごとの読み始め・終わり（秒）を保存
    lead=max(0,nz[0]-400)/sr; tt=q['prePhonemeLength']/q['speedScale']-lead; ph=[]
    for ap in q['accent_phrases']:
        st=tt
        for m in ap['moras']: tt+=((m.get('consonant_length') or 0)+m['vowel_length'])/q['speedScale']
        ph.append([''.join(m['text'] for m in ap['moras']),round(st,3),round(tt,3)])
        if ap.get('pause_mora'): tt+=ap['pause_mora']['vowel_length']/q['speedScale']
    json.dump(ph,open(f'{V}narr/{k}.json','w'),ensure_ascii=False)
    print(k,round(len(a)/sr,2),q.get('kana'))
