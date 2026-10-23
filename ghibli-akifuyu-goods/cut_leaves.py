# 石畳の落ち葉写真（bg_autumn_leaves.jpg）から、枯葉を1枚ずつ切り抜く（暗い石畳と色で分ける）
# 使い方: python3 cut_leaves.py <出力フォルダ>
import sys,os,cv2,numpy as np
O=sys.argv[1].rstrip('/')+'/'; os.makedirs(O,exist_ok=True)
im=cv2.imread(os.path.dirname(os.path.abspath(__file__))+'/../ghibli-toolkit/assets/bg_autumn_leaves.jpg')
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=((hsv[...,1]>70)&(hsv[...,2]>90)).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(m)
idx=sorted([i for i in range(1,n) if st[i,4]>1500 and st[i,0]>2 and st[i,1]>2 and st[i,0]+st[i,2]<im.shape[1]-2 and st[i,1]+st[i,3]<im.shape[0]-2],key=lambda i:-st[i,4])[:10]
for k,i in enumerate(idx):
    x,y,w,h,a=st[i]; a_=(lab[y:y+h,x:x+w]==i).astype(np.uint8)*255; a_=cv2.GaussianBlur(a_,(3,3),0)
    cv2.imwrite(O+f'leaf{k}.png',np.dstack([im[y:y+h,x:x+w],a_])); print(k,w,h,a)
