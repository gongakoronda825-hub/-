import json,urllib.request,urllib.parse,wave,numpy as np,time
SP=13
L=[('n01','秋のどんぐり共和国に行ってきた！'),('n02','入ってすぐ、カルシファーがお出迎え。'),
('n03','店頭には、かわいい柄のブランケットが置いてあった！'),('n04','のれんをくぐると…'),
('n05','千と千尋の神隠しのグッズがいっぱい！'),('n06','湯婆婆やカオナシのぬいぐるみも、ずらり。'),
('n07','前回紹介したパンリースも！実物もかわいい。'),('n08','ゴブラントートも見つけた。'),
('n09','魔女宅グッズも充実。'),('n10','キキのお部屋みたいなディスプレイ。'),
('n11','まっくろくろすけ、ふわふわすぎる。'),('n12','ポニョのグッズも。'),
('n13','もののけ姫のキーホルダーも。'),('n14','トトロのバス停まで！'),
('n15','食器までかわいくて、全部ほしくなる。'),('n16','ジブリの最新情報を発信中。フォローしてね！'),
('n17','ハウルのサンキャッチャーも、キラキラ。'),('n18','クリアファイルも、かわいい柄ばっかり。'),
('n19','マスキングテープも、種類がいっぱい。'),('n20','そして、ラピュタのポスター、買っちゃいました！'),
('n21','ノートもかわいい。'),('n22','キーホルダーもたくさん。'),
('n23','秋冬用のグッズがたくさん出てるから、'),('n24','みんなもぜひ行ってみてね！')]
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
    p=f'vlog/narr/{k}.wav'; open(p,'wb').write(wav)
    with wave.open(p) as w: sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16)
    nz=np.where(np.abs(a)>300)[0]; a=a[max(0,nz[0]-400):nz[-1]+2000]
    with wave.open(p,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    print(k,round(len(a)/sr,2),q.get('kana'))
