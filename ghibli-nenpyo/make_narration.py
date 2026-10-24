# ジブリ年表（初めて見たジブリ、何歳だった？）のナレーション。VOICEVOX 青山龍星
# 使い方: python3 make_narration.py <保存フォルダ> [キー...]
import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1].rstrip('/')+'/'
L=[('hook','初めて見たジブリ、何歳だった？'),('hook2','自分の生まれた年から、探してみて。'),
('n1984','ナウシカは、スタジオジブリができる前の作品。'),
('n1986','ラピュタは、ジブリができて、最初の作品。'),
('n1989','キキの声は、タカヤマミナミさん。'),
('n1995','耳をすませばの監督は、コンドウヨシフミさん。'),
('n1997','もののけ姫は、当時の、日本の映画の興行記録を、塗り替えた。'),
('n2004','ハウルの声は、キムラタクヤさん。'),
('n2008','ポニョの歌は、オオハシノゾミちゃんと、藤岡藤巻。'),
('n2010','アリエッティは、ヨネバヤシヒロマサさんの、初監督作品。'),
('n2013','風立ちぬは、宮崎ハヤオ監督の、引退作と言われた。'),
('n2023','君たちはどう生きるかは、アカデミー賞を受賞。'),
('n1988','トトロと、ほたるの墓は、同じ日に、2本立てで公開。'),
('n2001','千と千尋は、約19年間、日本の映画の興行収入、1位だった。'),
('end','あなたの初ジブリは？コメントで教えてね。'),
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
