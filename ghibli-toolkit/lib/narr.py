import json,urllib.request,urllib.parse,wave,sys
SP=13
L={'hook':'ジブリ漢字クイズ。ぜんもん読めたら、宮崎ハヤオレベル。',
'q1':'レベル1。この漢字、なんて読む？','a1':'正解は、ユバーバ。',
'q2':'レベル2。なんて読む？','a2':'正解は、コダマ。',
'q3':'レベル3。なんて読む？','a3':'正解は、ショウキ。',
'q4':'レベル4。ここから難しくなるよ。','a4':'正解は、オッコトヌシ。',
'q5':'レベル5。アシタカの一族。なんて読む？','a5':'正解は、エミシ。',
'q6':'最終問題。宮崎ハヤオレベル。読めたら天才。','a6':'正解は、ニギハヤミコハクヌシ。ハクの本当の名前です。',
'cta':'あなたは何問読めた？コメントで教えてね。'}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for k,txt in L.items():
    q=json.loads(op.open(urllib.request.Request('http://127.0.0.1:50021/audio_query?'+urllib.parse.urlencode({'text':txt,'speaker':SP}),method='POST')).read())
    q['speedScale']=1.08; q['prePhonemeLength']=0.05; q['postPhonemeLength']=0.1; q['outputSamplingRate']=44100
    kana=q.get('kana')
    wav=op.open(urllib.request.Request(f'http://127.0.0.1:50021/synthesis?speaker={SP}',data=json.dumps(q).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
    open(f'narr/{k}.wav','wb').write(wav)
    with wave.open(f'narr/{k}.wav') as w: d=w.getnframes()/w.getframerate()
    print(k,round(d,2),kana)
