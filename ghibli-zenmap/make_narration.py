import json,urllib.request,urllib.parse,wave,numpy as np,time
SP=13
L=[('zb','え、セブンのコピー機からジブリ出てきたんだけど！'),('zi','これ、禅とジブリ展のオリジナルマップ。セブンで印刷できるの。'),('z1','ジブリの禅マップが、セブンイレブンで印刷できるらしいから、行ってみる！'),('z2','完成！'),('z3','持って帰るよ〜'),
('z4','こんな感じだった！裏には禅の解説ものってる。'),
('z5','印刷方法は、禅とジブリ公式サイトの二次元コードを、マルチコピー機にかざして、'),('z6','四百円を入れるだけ。'),
('z7','全国のセブンイレブンで買えるから、ぜひ印刷してみてね！'),('z8','ジブリの最新情報を発信中。フォローしてね！')]
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for _ in range(60):
    try: op.open('http://127.0.0.1:50021/version').read(); break
    except Exception: time.sleep(2)
import sys
for k,txt in L:
    if len(sys.argv)>1 and k not in sys.argv[1:]: continue
    q=json.loads(op.open(urllib.request.Request('http://127.0.0.1:50021/audio_query?'+urllib.parse.urlencode({'text':txt,'speaker':SP}),method='POST')).read())
    q['speedScale']=1.15; q['prePhonemeLength']=0.0; q['postPhonemeLength']=0.05; q['outputSamplingRate']=44100
    for ap in q['accent_phrases']:
        if ap.get('pause_mora'): ap['pause_mora']['vowel_length']=min(ap['pause_mora']['vowel_length'],0.18)
    wav=op.open(urllib.request.Request(f'http://127.0.0.1:50021/synthesis?speaker={SP}',data=json.dumps(q).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
    p=f'zen/narr/{k}.wav'; open(p,'wb').write(wav)
    with wave.open(p) as w: sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
    nz=np.where(np.abs(a)>300)[0]; a=a[max(0,nz[0]-400):nz[-1]+2000]
    with wave.open(p,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    print(k,round(len(a)/sr,2),q.get('kana'))
