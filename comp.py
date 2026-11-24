"""Cut the black stair out of photo p08 (same camera) and lay it over the Blender render; also make an alignment overlay."""
import subprocess, numpy as np, pathlib
H=pathlib.Path(__file__).resolve().parent; O=H/"out"; W,HH=1536,1024
def load(p,*x): return np.frombuffer(subprocess.run(["magick",str(p),*x,"-alpha","off","-resize",f"{W}x{HH}!","-depth","8","rgb:-"],capture_output=True,check=True).stdout,np.uint8).reshape(HH,W,3).astype(float)
def save(a,p): subprocess.run(["magick","-size",f"{W}x{HH}","-depth","8","rgb:-",str(p)],input=np.clip(a+.5,0,255).astype(np.uint8).tobytes(),check=True)
ph=load(H/"refs/p08.jpg"); c=load(O/"color.png")
lum=ph.max(2); sat=ph.max(2)-ph.min(2)
m=(lum<95)&(sat<26); yy,xx=np.mgrid[0:HH,0:W]; m&=(xx>1270)&(yy<650)
m&=~((yy>560)&(yy<740)&(xx<1400))                       # dog-door flap
m&=~((yy>300)&(yy<360)&(xx>1300)&(xx<1425)); m&=~((yy>452)&(yy<490)&(xx<1400))      # dark door glass
a=m.astype(float); k=(a+np.roll(a,1,0)+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1))/5
save(c*(1-k[...,None])+ph*k[...,None],O/"guide.png"); save(np.stack([m*255]*3,2),O/"stair_mask.png")
g=c.mean(2); e=np.abs(np.gradient(g)[0])+np.abs(np.gradient(g)[1]); ov=ph.copy(); ov[e>14]=[255,0,0]; save(ov,O/"overlay.png")
