import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1]
L=[('hook','これから行けるジブリイベント、全部まとめた！'),
('e1','まずは横須賀。ジブリパーク展が、来年2月11日から5月14日まで、横須賀美術館で開催！'),
('e2','舞台、千と千尋の神隠しが全国ツアー！来年3月の東京、明治座から、愛知、大阪、福岡、北海道へ。千尋役は、なんとナナニン！'),
('e3','10月23日から、耳をすませばと、借りぐらしのアリエッティが、アイマックスに！30日からは、全国で拡大上映。'),
('e4','ジブリパークは、30日から、秋のどんどこ祭り。魔女の谷と、もののけの里は、夜7時まで開いてます。'),
('e5','京都の、禅とジブリ展は、12月6日まで。君たちはどう生きるかの世界観が中心です。'),
('e6','佐賀では初めての、金曜ロードショーとジブリ展。11月3日スタート！'),
('e7','京都では12月17日から、ハクインさんのゼン。禅のお坊さん、ハクインの作品を、映像と一緒に見られる展示です。'),
('q','あなたはどれに行く？コメントで教えてね。'),
('cta','一緒に行く人に送ってね。保存して、予定に入れておこう！'),
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
    print(k,round(len(a)/sr,2),q.get('kana'))
