import numpy as np,onnxruntime as ort,sys
from PIL import Image,ImageDraw
sess=ort.InferenceSession('models/isnet_gen.onnx',providers=['CPUExecutionProvider'])
def bmask(img):
    w,h=img.size; a=np.asarray(img.convert('RGB').resize((1024,1024),Image.BILINEAR)).astype(np.float32)/255
    a=(a-0.5)/1.0
    o=sess.run(None,{sess.get_inputs()[0].name:a.transpose(2,0,1)[None].astype(np.float32)})[0][0,0]
    o=(o-o.min())/(o.max()-o.min()+1e-8); return Image.fromarray((o*255).astype(np.uint8)).resize((w,h),Image.BILINEAR)
if __name__=='__main__':
    T=260; ns=[int(x) for x in sys.argv[1:]]
    m=Image.new('RGB',(4*(T+10),2*(T+30)),'white'); d=ImageDraw.Draw(m)
    for k,n in enumerate(ns):
        img=Image.open(f'kh/big/{n}.jpg').convert('RGB'); mk=bmask(img)
        r=img.copy(); r.putalpha(mk); bb=mk.point(lambda v:255 if v>60 else 0).getbbox(); r=r.crop(bb); r.save(f'khcut/{n}.png')
        t=r.copy(); t.thumbnail((T,T)); bg=Image.new('RGBA',(T,T),(120,200,140,255)); bg.alpha_composite(t,((T-t.width)//2,(T-t.height)//2))
        x=(k%4)*(T+10); y=(k//4)*(T+30); m.paste(bg.convert('RGB'),(x,y)); d.text((x+4,y+T+6),str(n),fill='black')
    m.save('khcut_sheet.jpg')
