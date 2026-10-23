# 商品写真を切り抜いて透過PNGにする（biref.py と同じ isnet_gen モデル）
# 使い方: python3 cut_products.py <作業フォルダ(setup.shのW)> <入力フォルダ> <出力フォルダ> 名前...
import sys,numpy as np,onnxruntime as ort
from PIL import Image
W,I,O=[a.rstrip('/')+'/' for a in sys.argv[1:4]]
sess=ort.InferenceSession(W+'models/isnet_gen.onnx',providers=['CPUExecutionProvider'])
def bmask(img):
    w,h=img.size; a=np.asarray(img.convert('RGB').resize((1024,1024),Image.BILINEAR)).astype(np.float32)/255
    a=(a-0.5)/1.0; out=sess.run(None,{sess.get_inputs()[0].name:a.transpose(2,0,1)[None]})[0][0,0]
    out=(out-out.min())/(out.max()-out.min()+1e-6); return Image.fromarray((out*255).astype(np.uint8)).resize((w,h),Image.BILINEAR)
for n in sys.argv[4:]:
    img=Image.open(I+n+'.jpg').convert('RGB'); m=bmask(img); r=img.copy(); r.putalpha(m)
    r=r.crop(m.point(lambda v:255 if v>60 else 0).getbbox()); r.save(O+n+'.png'); print(n,r.size)
