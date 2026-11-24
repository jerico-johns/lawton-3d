"""Cut a seamless-ish tile out of the Morris board image by autocorrelation; prints the period used."""
import subprocess, numpy as np, pathlib
R=pathlib.Path(__file__).resolve().parent; src=R/"refs/wp_morris.jpg"
W,H=1124,415
a=np.frombuffer(subprocess.run(["magick",str(src),"-depth","8","rgb:-"],capture_output=True,check=True).stdout,np.uint8).reshape(H,W,3).astype(float)
# flatten vignette with a wide blur
b=np.frombuffer(subprocess.run(["magick",str(src),"-blur","0x50","-depth","8","rgb:-"],capture_output=True,check=True).stdout,np.uint8).reshape(H,W,3).astype(float)
a=np.clip(a/np.maximum(b,1)*np.array([92,96,80]),0,255)     # board average, lifted a little to albedo
g=a.mean(2); g=g-g.mean()
def score(dx,dy):
    p=g[max(0,dy):H+min(0,dy), dx:]; q=g[:H-abs(dy), :W-dx]
    return (p*q).mean()/np.sqrt((p*p).mean()*(q*q).mean())
hx=max(range(200,420),key=lambda d:score(d,0)); vy=max(range(150,330),key=lambda d:(g[d:]*g[:H-d]).mean()/np.sqrt((g[d:]**2).mean()*(g[:H-d]**2).mean()))
print("period px",hx,vy,"corr",round(score(hx,0),3), "ratio h/w",round(vy/hx,3),"(Morris 17.9/20.5 = 0.873)")
def mir(x):                                   # mirror score about column x (the pattern is bilaterally symmetric)
    k=hx//2; L=g[:,x-k:x][:,::-1]; Rr=g[:,x:x+k]
    return (L*Rr).mean()/np.sqrt((L*L).mean()*(Rr*Rr).mean())
ax=max(range(hx//2,W-hx),key=mir); half=a[:, ax:ax+hx//2]
y0=min(range(0,H-vy),key=lambda y: np.abs(half[y]-half[y+vy]).mean())     # best vertical seam
half=half[y0:y0+vy]; tt=np.concatenate([half,half[:,::-1]],1)
print("axis",ax,"mirror",round(mir(ax),3),"y0",y0)
subprocess.run(["magick","-size",f"{tt.shape[1]}x{tt.shape[0]}","-depth","8","rgb:-","-filter","Lanczos","-resize","300%","-define","png:exclude-chunks=date,time",str(R/"tex/morris_tile.png")],input=np.ascontiguousarray(tt).astype(np.uint8).tobytes(),check=True)
(R/"tex/tile.txt").write_text("1")
subprocess.run(["magick",str(R/"tex/morris_tile.png"),"-quality","86","-resize","700x",str(R/"tex/morris_tile_web.jpg")],check=True)
