# ジブリ年表（あなたはどのジブリ作品と同い年？）のナレーション。VOICEVOX 青山龍星
# 使い方: python3 make_narration.py <保存フォルダ> [キー...]
import json,urllib.request,urllib.parse,wave,numpy as np,time,sys
SP=13; V=sys.argv[1].rstrip('/')+'/'
L=[('hook','あなたは、どのジブリ作品と、同い年？'),('hook2','生まれた年から、探してみてください。'),
('n1984','ナウシカは、お父さんお母さんと、一緒に見た人も、多いかもしれません。'),
('n1986','ジブリ最初の作品が、ラピュタ。'),
('n1988','トトロは、きっと誰もが、一度は見た作品。'),
('n1989','キキの声は、タカヤマミナミさんです。'),
('n1997','もののけ姫は、当時の興行記録を、塗り替えました。'),
('n2001','千と千尋は、映画館で見た思い出がある人も、多いのでは。'),
('n2004','ハウルの声は、キムラタクヤさんです。'),
('n2008','ポニョの歌、今でも口ずさめる人、いますよね。'),
('n2013','風立ちぬは、大人になって見ると、泣けるという声も多い作品です。'),
('n1992','クレナイのブタは、大人になってから見ると、印象が変わる作品です。'),
('n1995','耳をすませばを見て、図書カードに憧れた人も、多いはず。'),
('n2010','アリエッティは、ヨネバヤシヒロマサさんの、初監督作品です。'),
('n2016','レッドタートルは、セリフがないのに、心に残る作品です。'),
('n2023','君たちはどう生きるかは、アカデミー賞を受賞しました。'),
('end','同い年の作品は、どれでしたか？コメントで教えてください。'),
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
