import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1]
L=[('hook','東京に、ジブリの世界があった！江戸東京たてもの園。'),
('drawers','壁一面の引き出しは、文房具屋さんの、タケイサンショウドウ。カマジイのボイラー室にそっくり！'),
('izakaya','居酒屋、カギヤのカウンター。千尋のお父さんとお母さんが、夢中で食べてそう。'),
('sento','富士山の絵がある銭湯、コダカラユ。まるで、アブラヤの大浴場！'),
('engawa','長いガラス戸の縁側は、サツキとメイが走り回った、あの家みたい。'),
('bus','昔のボンネットバス。となりで、トトロが雨宿りしてそう。'),
('garden','縁側から庭をながめると、カオナシもひと休み。夏休みの、おばあちゃんちみたい。'),
('doma','大きなかまどと、囲炉裏のある土間は、もののけ姫の世界。ジコボウの雑炊が食べたくなる。'),
('kokuriko','乾物屋の、やまとや本店。俊と海が、コロッケを買った、あの商店街みたい！'),
('gate','門の奥には、こだまや、トトロがかくれてるかも。'),
('q','あなたはどの場所に行きたい？コメントで教えてね。'),
('cta','入場料は、一般400円。保存して、行くときの参考にしてね！'),
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
