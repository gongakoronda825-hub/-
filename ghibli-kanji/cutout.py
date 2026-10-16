import sys,numpy as np,onnxruntime as ort
from PIL import Image
sess=ort.InferenceSession('models/isnetis.onnx',providers=['CPUExecutionProvider'])
def mask(img,s=1024):
    a=np.asarray(img.convert('RGB')).astype(np.float32)/255
    h,w=a.shape[:2]; r=s/max(h,w); nh,nw=int(h*r),int(w*r)
    im=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((nw,nh),Image.BILINEAR)).astype(np.float32)/255
    pad=np.zeros((s,s,3),np.float32); ph,pw=(s-nh)//2,(s-nw)//2; pad[ph:ph+nh,pw:pw+nw]=im
    out=sess.run(None,{sess.get_inputs()[0].name:pad.transpose(2,0,1)[None]})[0][0,0]
    m=out[ph:ph+nh,pw:pw+nw]; m=Image.fromarray((np.clip(m,0,1)*255).astype(np.uint8)).resize((w,h),Image.BILINEAR)
    return m
for n in sys.argv[1:]:
    img=Image.open(f'gb/{n}.jpg').convert('RGB'); m=mask(img)
    rgba=img.copy(); rgba.putalpha(m); bb=m.point(lambda v:255 if v>40 else 0).getbbox()
    if bb: rgba=rgba.crop(bb)
    rgba.save(f'cut/{n}.png'); print(n,bb)
