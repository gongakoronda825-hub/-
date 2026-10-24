# ジブリ年表（初めて見たジブリ、何歳だった？）のナレーション。VOICEVOX 青山龍星
# 使い方: python3 make_narration.py <保存フォルダ> [キー...]
import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1].rstrip('/')+'/'
L=[('hook','初めて見たジブリ、何歳でしたか？'),('hook2','生まれた年から、探してみてください。'),
('n1984','ナウシカは、ジブリ誕生前の作品です。'),
('n1986','ジブリ最初の作品が、ラピュタ。'),
('n1988','トトロと、ほたるの墓は、2本立てで公開されました。'),
('n1989','キキの声は、タカヤマミナミさんです。'),
('n1997','もののけ姫は、当時の興行記録を、塗り替えました。'),
('n2001','千と千尋は、19年間、興行収入1位でした。'),
('n2004','ハウルの声は、キムラタクヤさんです。'),
('n2008','ポニョの歌は、オオハシノゾミちゃんと、藤岡藤巻。'),
('n2013','風立ちぬは、引退作と言われました。'),
('n2023','君たちはどう生きるかは、アカデミー賞を受賞しました。'),
('end','あなたの初ジブリは？コメントで教えてください。'),
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
