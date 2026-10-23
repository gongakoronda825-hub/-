# 元写真（キャラなし）を合成画像(1080x1920)に位置合わせし、差分からキャラ部分だけを抜き出す
# 使い方: python3 align.py <アップロードフォルダ> <出力フォルダ>
import sys,glob,cv2,numpy as np
U=sys.argv[1].rstrip('/')+'/'; O=sys.argv[2].rstrip('/')+'/'
def p(k): return glob.glob(U+k+'*')[0]
PAIRS=[('drawers','71e2dd02',['2f27ffec']),('izakaya','f15bb6bf',['cd0e8710','eda48ff8']),('sento','79333165',['c77107dc']),('engawa','1abaf17e',['88700389']),
('bus','96dbf19f',['28043832']),('garden','893cbaf9',['518a500c']),('doma','7bda5fc8',['ee52758c']),('gate','78ae0705',['f2f18809'])]
sift=cv2.SIFT_create(4000)
for name,ck,oks in PAIRS:
    C=cv2.imread(p(ck)); gc=cv2.cvtColor(C,cv2.COLOR_BGR2GRAY); kc,dc=sift.detectAndCompute(gc,None); best=None
    for ok in oks:
        Ob=cv2.imread(p(ok)); go=cv2.cvtColor(Ob,cv2.COLOR_BGR2GRAY); ko,do=sift.detectAndCompute(go,None)
        m=cv2.BFMatcher().knnMatch(do,dc,k=2); g=[a for a,b in m if a.distance<0.7*b.distance]
        M,inl=cv2.estimateAffinePartial2D(np.float32([ko[a.queryIdx].pt for a in g]),np.float32([kc[a.trainIdx].pt for a in g]),ransacReprojThreshold=3)
        n=int(inl.sum()) if inl is not None else 0
        if best is None or n>best[0]: best=(n,M,Ob,ok)
    n,M,Ob,ok=best
    W=cv2.warpAffine(Ob,M,(1080,1920),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT)
    d=cv2.absdiff(cv2.GaussianBlur(W,(7,7),0),cv2.GaussianBlur(C,(7,7),0)).max(2)
    mk=(d>38).astype(np.uint8)*255
    mk=cv2.morphologyEx(mk,cv2.MORPH_OPEN,np.ones((5,5),np.uint8)); mk=cv2.morphologyEx(mk,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    nl,lab,st,_=cv2.connectedComponentsWithStats(mk); keep=np.zeros_like(mk)
    for i in range(1,nl):
        if st[i,4]>2500: keep[lab==i]=255
    keep=cv2.dilate(keep,np.ones((7,7),np.uint8)); keep=cv2.GaussianBlur(keep,(5,5),0)
    cv2.imwrite(O+name+'_before.jpg',W,[cv2.IMWRITE_JPEG_QUALITY,95]); cv2.imwrite(O+name+'_after.jpg',C,[cv2.IMWRITE_JPEG_QUALITY,95])
    cv2.imwrite(O+name+'_chars.png',np.dstack([C,keep]))
    print(name,ok,n,'scale',round(float(np.hypot(M[0,0],M[1,0])),3))
