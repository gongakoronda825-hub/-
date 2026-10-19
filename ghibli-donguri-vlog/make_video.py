import sys; sys.argv=['x']
exec(open('kh2.py').read().split("if len(sys.argv)>1")[0].replace('/ghibli-keyholder/vol2/','/ghibli-donguri-vlog/'))
from PIL import ImageFont
import numpy as np,subprocess,wave
cs=open('imax.py').read(); exec(cs[cs.index('def kf('):cs.index('def chara(')])
KF='fonts/keifont.ttf'; V='vlog/'; FPS=30; SR=44100
OUTV='/home/user/-/ghibli-donguri-vlog/donguri_vlog.mp4'; import os; os.makedirs(os.path.dirname(OUTV),exist_ok=True)
FOLLOW='/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg'
# (clip, in, dur, narr, telop, sfx)
SEG=[('0280',0,1.8,'n01','どんぐり共和国に行ってきた！','kira1'),
('0285',0,2.3,'n02','カルシファーがお出迎え',None),
('0305',0.3,5.5,'n03','かわいい柄のブランケット！',None),
('0286',0,3.15,'n04','カーテンをくぐると…',None),
('0287',0,3.7,'n05','千と千尋コーナー！','shakin2'),
('0290',0,1.4,'n06','ぬいぐるみがずらり',None),
('0291',0,2.0,None,'湯婆婆とカオナシも',None),
('0303',0,6.5,'n07','前回紹介したパンリース！','correct2'),
('0308',0,4.0,'n08','ゴブラントートも発見',None),
('0295',0,1.7,'n09','魔女宅グッズ',None),
('0304',0,2.45,'n10','キキのお部屋みたい',None),
('0309',0,4.3,'n11','ふわっふわ…',None),
('0310',0,3.35,'n12','ポニョも',None),
('0312',0,1.9,'n13','もののけ姫キーホルダー',None),
('0313',0,2.1,'n14','トトロのバス停！',None),
('0315',0,5.0,'n15','食器までかわいい',None),
('FOLLOW',0,3.3,'n16',None,'kira1')]
def rd(p):
    with wave.open(p) as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; ch=w.getnchannels()
    return a.reshape(-1,ch).mean(1) if ch>1 else a
def telop(t):
    L=layer(); kf(L,t,92,H/2,WHITE,inner=GREEN,outer=WHITE,si=14,so=26,cx=W/2,maxw=820)
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
total=0; starts=[]
for si,seg in enumerate(SEG):
    starts.append(total); fr=frames(seg); T=telop(seg[4]) if seg[4] else None
    for k,f in enumerate(fr):
        im=Image.fromarray(f).convert('RGBA')
        if seg[0]!='FOLLOW': im.alpha_composite(TAG)
        if T is not None:
            s=POP[k] if k<len(POP) else 1.0
            t=T.resize((max(1,int(T.width*s)),max(1,int(T.height*s))),Image.BICUBIC)
            im.alpha_composite(t,(int(500-t.width/2),int(1360-t.height/2)))
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
    if seg[5]: add(rd(f'labsfx/{seg[5]}.wav'),t,0.32)
    if seg[4]: add(rd('sfx/pop.wav'),t,0.25)
mix=mix[:int(total/FPS*SR)]; mix/=max(1.0,np.abs(mix).max()/0.95)
with wave.open(V+'a.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',V+'v.mp4','-i',V+'a.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',OUTV])
print('done',total/FPS)
