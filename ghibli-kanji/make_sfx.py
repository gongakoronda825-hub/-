import numpy as np, wave
SR=44100
def save(name,x):
    x=np.clip(x/ (np.max(np.abs(x))+1e-9)*0.9,-1,1)
    with wave.open(f'sfx/{name}.wav','wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes())
def t_(d): return np.arange(int(SR*d))/SR
def env(n,a=0.005,r=0.2,total=None):
    t=np.arange(n)/SR; e=np.minimum(1,t/a)*np.exp(-t/r); return e
def tone(f,d,harm=(1,.5,.3,.2),r=0.25,a=0.004,detune=0):
    t=t_(d); x=sum(h*np.sin(2*np.pi*f*(k+1)*t*(1+detune*(k%2))) for k,h in enumerate(harm))
    return x*env(len(t),a,r)
def brass(f,d,r=0.35):
    t=t_(d); x=sum((1/(k+1))*np.sin(2*np.pi*f*(k+1)*t) for k in range(10))
    x+=0.6*sum((1/(k+1))*np.sin(2*np.pi*f*1.004*(k+1)*t) for k in range(10))
    return x*env(len(t),0.01,r)
def mix(parts,d):
    out=np.zeros(int(SR*d))
    for st,x,g in parts:
        i=int(st*SR); n=min(len(x),len(out)-i); out[i:i+n]+=g*x[:n]
    return out
def noise_hit(d,r=0.08,lp=0.2):
    n=np.random.randn(int(SR*d)); 
    for _ in range(3): n=np.convolve(n,np.ones(int(1/lp))/int(1/lp),'same')
    return n*env(len(n),0.001,r)
# デデン！ (question)
C2=65.4; 
dd=mix([(0,brass(98,0.25,0.12)+0.6*brass(147,0.25,0.12)+noise_hit(0.25,0.05),1),
        (0.22,brass(92.5,0.9,0.45)+0.6*brass(138.6,0.9,0.45)+0.5*brass(185,0.9,0.45)+noise_hit(0.9,0.12),1.2)],1.3)
save('deden',dd)
# tick (countdown)
tk=tone(1600,0.12,(1,.3),r=0.03)+0.5*noise_hit(0.12,0.01,0.5)
save('tick',tk)
# ピンポーン (correct)
pp=mix([(0,tone(1318.5,0.5,(1,.2,.1),r=0.35),1),(0.28,tone(1046.5,1.2,(1,.2,.1),r=0.7),1)],1.6)
save('pinpon',pp)
# ジャジャーン fanfare (hook)
ch=[261.6,329.6,392,523.3]
ff=mix([(0,sum(brass(f,0.18,0.08) for f in ch),1),(0.2,sum(brass(f*1.122,1.2,0.6) for f in ch),1.1)],1.5)
save('fanfare',ff)
# whoosh (transition)
n=np.random.randn(int(SR*0.5)); 
for _ in range(2): n=np.convolve(n,np.ones(8)/8,'same')
t=t_(0.5); wh=n*np.sin(np.pi*t/0.5)**2
save('whoosh',wh*0.6)
# ending sparkle arpeggio
arp=[523.3,659.3,784,1046.5,1318.5,1568]
sp=mix([(i*0.07,tone(f,0.8,(1,.3),r=0.4),0.8) for i,f in enumerate(arp)],1.4)
save('sparkle',sp)
# drumroll before final reveal (optional)
dr=np.zeros(int(SR*2.8))
for i in range(int(2.8/0.045)):
    h=noise_hit(0.05,0.02,0.3)*(0.4+0.6*i/62); s=int(i*0.045*SR); dr[s:s+len(h)]+=h[:len(dr)-s]
save('drumroll',dr)
print('ok')
