import numpy as np, pandas as pd, sys
sys.path.insert(0,'analysis')
from detect import load, detect, qrot, G
d=load('orphe_raw_20261115_193327_samples.csv')
gt=pd.read_csv('manual-gt-2026-11-15T11-17-27.csv').manual_gt_cm.values
Q=d[['qw','qx','qy','qz']].values; Q=Q/np.linalg.norm(Q,axis=1,keepdims=True)
A=d[['ax_g','ay_g','az_g']].values
W=np.array([qrot(q,a) for q,a in zip(Q,A)])
t=d.t.values
rest=(d.gn.values<5)
print('world acc at rest mean', W[rest].mean(0).round(3))
def apex(k,l,gmag):
    tt=t[k:l+1]-t[k]; av=(W[k:l+1,2]-gmag)*G
    v=np.concatenate([[0],np.cumsum((av[1:]+av[:-1])/2*np.diff(tt))])
    z=np.concatenate([[0],np.cumsum((v[1:]+v[:-1])/2*np.diff(tt))])
    zz=z-z[-1]*tt/tt[-1]; return zz.max()*100
gmag=W[rest,2].mean()
for hi in [4,6,8,10]:
    J=detect(d,hi=hi); print('hi',hi,'n',len(J),[round(t[k],2) for k,l in J])
J=detect(d,hi=8)
for sk in [-2,-1,0,1,2]:
  for sl in [-2,0,2]:
    ap=np.array([apex(k+sk,l+sl,gmag) for k,l in J]); e=ap-gt
    print(f"shift to{sk:+d} ld{sl:+d}: MAE {np.abs(e).mean():.2f} bias {e.mean():+.2f}")
ap=np.array([apex(k,l,gmag) for k,l in J])
# LOOCV linear calibration
pred=[]
for i in range(len(gt)):
    m=np.arange(len(gt))!=i; a,b=np.polyfit(ap[m],gt[m],1); pred.append(a*ap[i]+b)
pred=np.array(pred); print('raw',ap.round(1)); print('gt ',gt)
print('LOOCV linear MAE',np.abs(pred-gt).mean().round(2),'raw MAE',np.abs(ap-gt).mean().round(2))
print('full fit', np.polyfit(ap,gt,1))
T=np.array([t[l]-t[k] for k,l in J])
pred=[]
for i in range(len(gt)):
    m=np.arange(len(gt))!=i; c=np.polyfit(T[m],gt[m],1); pred.append(np.polyval(c,T[i]))
print('flight-time LOOCV MAE',np.abs(np.array(pred)-gt).mean().round(2))
