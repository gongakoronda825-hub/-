import sys; sys.argv=['x']
exec(open('kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ghibli-donguri-vlog/'))
from PIL import ImageFont
import numpy as np,subprocess,wave
cs=open('imax.py').read(); exec(cs[cs.index('def kf('):cs.index('def chara(')])
KF='fonts/keifont.ttf'; V='vlog/'; FPS=30; SR=44100
OUTV='/home/user/-/ghibli-donguri-vlog/donguri_vlog.mp4'; import os; os.makedirs(os.path.dirname(OUTV),exist_ok=True)
FOLLOW='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg'
# (clip, in, dur, narr, sfx)
SEG=[('0280',0,1.8,'n01','kira1'),('0285',0,2.3,'n02',None),('0305',0.3,4.0,'n03',None),('0281',1.4,1.6,None,None),
('0287',0,1.4,'n04',None),('0287',1.4,2.35,'n05','shakin2'),('0290',0,1.4,'n06',None),('0291',0,2.0,None,None),
('0297',0.3,2.4,'n17',None),('0303',0,5.0,'n07','correct2'),('0308',0,3.0,'n08',None),('0295',0,1.7,'n09',None),
('0304',0,2.0,'n10',None),('0300',0,1.28,'n21',None),('0301',0,2.6,'n18',None),('0314',0.5,3.3,'n19',None),
('0309',1.0,3.3,'n11',None),('0310',0,2.2,'n12',None),('0311',0.5,1.8,'n22',None),('0312',0,1.9,'n13',None),
('0313',0,2.1,'n14',None),('0315',0,3.4,'n15',None),('0299',0,4.0,'n20','kira1'),('FOLLOW',0,3.3,'n16',None)]
SUB={'n01':'どんぐり共和国に行ってきた！','n02':'入ってすぐ、カルシファーがお出迎え','n03':'店頭には、かわいい柄の\nブランケットが置いてあった！',
'n04':'カーテンをくぐると…','n05':'千と千尋の神隠しのグッズがいっぱい！','n06':'湯婆婆やカオナシのぬいぐるみも、ずらり',
'n07':'前回紹介したパンリースも！\n実物もかわいい','n08':'ゴブラントートも見つけた','n09':'魔女宅グッズも充実',
'n10':'キキのお部屋みたいなディスプレイ','n11':'まっくろくろすけ、ふわふわすぎる','n12':'ポニョのグッズも',
'n13':'もののけ姫のキーホルダーも','n14':'トトロのバス停まで！','n15':'食器までかわいくて、\n全部ほしくなる',
'n17':'ハウルのサンキャッチャーも、キラキラ','n18':'クリアファイルも、かわいい柄ばっかり','n19':'マスキングテープも、種類がいっぱい',
'n20':'そして、ラピュタのポスター\n買っちゃいました！','n21':'ノートもかわいい','n22':'キーホルダーもたくさん'}
def wdur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
def telop(t):
    L=layer(); ls=t.split('\n')
    for j,l in enumerate(ls): kf(L,l,54,H/2+(j-(len(ls)-1)/2)*78,WHITE,inner=(35,35,35),outer=(35,35,35),si=9,so=9,cx=W/2,maxw=860)
    return L.crop(L.getbbox())
TAG=layer(); pill(TAG,W/2,290,'どんぐり共和国 vlog',30,(255,255,255,215),GREEN,30)
TAG=Image.fromarray(np.array(TAG)); 
def frames(seg):
    c,t0,d=seg[0],seg[1],seg[2]; n=int(round(d*FPS))
    if c=='FOLLOW':
        im=np.array(Image.open(FOLLOW).convert('RGB').resize((W,H))); return [im]*n
    p=subprocess.run(['ffmpeg','-v','error','-ss',str(t0),'-i',f'{V}sdr/IMG_{c}.mp4','-t',str(d),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    a=np.frombuffer(p,np.uint8).reshape(-1,H,W,3); fr=list(a[:n])
    while len(fr)<n: fr.append(fr[-1])
    return fr
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',V+'v.mp4'],stdin=subprocess.PIPE)
POP=[0.6,0.9,1.08,1.03,1.0]
tt=0; SUBS=[]
for seg in SEG:
    if seg[3] and seg[3] in SUB: SUBS.append((tt+0.05,tt+0.08+wdur(f'{V}narr/{seg[3]}.wav')+0.35,telop(SUB[seg[3]])))
    tt+=round(seg[2]*FPS)/FPS
total=0; starts=[]
for si,seg in enumerate(SEG):
    starts.append(total); fr=frames(seg)
    for k,f in enumerate(fr):
        im=Image.fromarray(f).convert('RGBA')
        if seg[0]!='FOLLOW': im.alpha_composite(TAG)
        g=(total+k)/FPS
        for (t0,t1,T) in SUBS:
            if t0<=g<t1 and seg[0]!='FOLLOW': im.alpha_composite(T,(int(510-T.width/2),int(960-T.height/2)))
        enc.stdin.write(np.array(im.convert('RGB')).tobytes())
    total+=len(fr)
enc.stdin.close(); enc.wait()
N=int(total/FPS*SR)+SR; mix=np.zeros(N,np.float32)
def add(a,t,g):
    i=int(t*SR); a=a[:N-i]; mix[i:i+len(a)]+=a*g
for seg,st in zip(SEG,starts):
    t=st/FPS
    if seg[0]!='FOLLOW':
        amb=subprocess.run(['ffmpeg','-v','error','-ss',str(seg[1]),'-i',f'{V}sdr/IMG_{seg[0]}.mp4','-t',str(seg[2]),'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout
        a=np.frombuffer(amb,np.float32).copy(); fl=int(0.03*SR)
        if len(a)>2*fl: a[:fl]*=np.linspace(0,1,fl); a[-fl:]*=np.linspace(1,0,fl)
        add(a,t,0.18)
    if seg[3]: add(rd(f'{V}narr/{seg[3]}.wav'),t+0.08,1.0)
    if seg[4]: add(rd(f'labsfx/{seg[4]}.wav'),t,0.32)
mix=mix[:int(total/FPS*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(V+'a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',V+'v.mp4','-i',V+'a.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',total/FPS)
