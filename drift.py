"""Edge-by-edge drift of an AI render against the Blender guide (1536x1024). Each edge: slide a 1-D gradient profile +-28 px."""
import subprocess, numpy as np, json, sys, pathlib
H=pathlib.Path(__file__).resolve().parent; O=H/"out"; W,HH=1536,1024
def load(p): return np.frombuffer(subprocess.run(["magick",str(p),"-alpha","off","-colorspace","Gray","-depth","8","gray:-"],capture_output=True,check=True).stdout,np.uint8).reshape(HH,W).astype(float)
g=load(O/"color.png"); B=json.loads((O/"boxes.json").read_text())
k=1.024; f,cv,cu,vx,vy,cz=703,163,66.8,728,487,47.6
px=lambda u,v: k*(vx+(u-cu)*f/(cv-v)); py=lambda z,v: k*(vy-(z-cz)*f/(cv-v)); s=lambda v: k*f/(cv-v)
def edge(a,axis,pos,lo,hi,r=12,w=7):
    """axis 'x': vertical edge at column pos over rows lo..hi; 'y': horizontal edge at row pos over cols lo..hi"""
    pos=int(round(pos)); lo,hi=int(lo),int(hi)
    def prof(im):
        m=im[lo:hi,pos-r-w:pos+r+w+1] if axis=='x' else im[pos-r-w:pos+r+w+1,lo:hi].T
        return np.abs(np.gradient(m.mean(0)))
    G=prof(g)[r:r+2*w+1]; A=prof(a); best=[]
    for d in range(-r,r+1):
        q=A[r+d:r+d+2*w+1]; c=np.corrcoef(G,q)[0,1]*min(1,q.max()/max(G.max()*.35,1e-6)); best.append((c,d))
    return max(best)
EDGES={ # name: (v plane, [left x edge, right x edge] as (u, rows), [top, bottom] as (z, cols))
 "wall 138":  (0,[(0,(400,560)),(138,(430,560))],None),
 "Tate 64.5": (16,[(36.75,(586,604)),(101.25,(590,606))],None),
 "bookcase 22":(16,[(7.35,(400,560)),(29.35,(400,560))],None),
 "table 80":  (85,[(23,(664,674)),(103,(664,674))],None),
 "lantern 30":(66.5,[(48,(195,215)),(78,(195,215))],[(101,(690,740)),(71,(690,740))]),
}
TOPS={"Tate top z30":(30,16,(690,790)),"table top z30":(30,85,(650,780)),"table back z30":(30,48,(780,930)),"bookcase shelf z71.2":(71.2,16,(480,550)),"plate rail z85.4":(85.4,0,(860,1040)),"wainscot cap z28.8":(28.8,0,(930,960))}
for n in sys.argv[1:]:
    a=load(O/f"{n}.png"); print("==",n)
    for nm,(v,xs,ys) in EDGES.items():
        r=[edge(a,'x',px(u,v),*rows) for u,rows in xs]; w0=(xs[1][0]-xs[0][0]); dw=(r[1][1]-r[0][1])/s(v)
        print(f"{nm:14s} left {r[0][1]:+d}px (c {r[0][0]:.2f})  right {r[1][1]:+d}px (c {r[1][0]:.2f})  -> width {w0+dw:.1f} in ({100*dw/w0:+.1f}%)")
        if ys:
            q=[edge(a,'y',py(z,v),*c) for z,c in ys]; print(f"{'':14s} top {q[0][1]:+d}px  bottom {q[1][1]:+d}px -> height {ys[0][0]-ys[1][0]+(q[1][1]-q[0][1])/s(v):.1f} in")
    for nm,(z,v,c) in TOPS.items():
        q=edge(a,'y',py(z,v),*c); print(f"{nm:22s} {q[1]:+d}px (c {q[0]:.2f}) -> {-q[1]/s(v):+.1f} in")
