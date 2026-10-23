# 秋冬グッズ vol.1（動画）のナレーション。VOICEVOX 青山龍星
# 使い方: python3 make_narration.py <保存フォルダ> [キー...]
import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1].rstrip('/')+'/'
L=[('hook','どんぐり共和国で買える、ジブリの秋冬グッズを紹介！'),
('p1','ボタンで留めれば、ポンチョみたいに羽織れるストール。雪だるまトトロと、ノルディック柄のジジ。'),
('p2','オカリナや、フライパンから、ミストが出てくる、ちいさな加湿器。デスクの乾燥対策に。'),
('p3','背中には、花火の夜空を、コマで飛ぶトトロ。ハッピがモチーフの、カーディガン。'),
('p4','ウルスラのブランケットをイメージした、ウール100パーセントの、ハーフ毛布。'),
('p5','星空の下で、オカリナを吹くトトロたち。もふもふの、ひざ掛け。お昼寝にもぴったり。'),
('p6','荷物を入れると、まんまるになる、オオトトロの、ふわふわトート。中にはポケット付き。'),
('p7','低反発で足にやさしい、丸洗いできるスリッパ。トトロと、ネコバスの2色。'),
('p8','ジョウが長くて、色々な履き方ができる、毛布ソックス。トトロと、ジジのフタガラ。'),
('q','あなたはどれが欲しい？コメントで教えてね。'),
('cta','保存して、冬じたくの参考にしてね！'),
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
    p=f'{V}{k}.wav'; open(p,'wb').write(wav)
    with wave.open(p) as w: sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
    nz=np.where(np.abs(a)>300)[0]; a=a[max(0,nz[0]-400):nz[-1]+2000]
    with wave.open(p,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    print(k,round(len(a)/sr,2),q.get('kana'))
