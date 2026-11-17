import numpy as np, pandas as pd, sys
sys.path.insert(0,'analysis')
from detect import load, detect, qrot, G
d=load('orphe_raw_20261115_193327_samples.csv')
gt=pd.read_csv('manual-gt-2026-11-15T11-17-27.csv')
J=detect(d)
rows=[]
for (k,l),g in zip(J,gt.manual_gt_cm):
    s=d.iloc[k:l+1]; t=s.t.values; T=t[-1]-t[0]
    q=s[['qw','qx','qy','qz']].values; q/=np.linalg.norm(q,axis=1,keepdims=True)
    a=s[['ax_g','ay_g','az_g']].values
    aw=np.array([qrot(qi,ai) for qi,ai in zip(q,a)])
    # gyro integrated rotation amount during flight
    rot=np.trapezoid(s.gn.values,t)
    # pitch-ish swing: max gyro
    # double integrate each world axis with z(0)=z(T)=0
    tt=t-t[0]; apex=[]
    for ax in range(3):
        acc=(aw[:,ax]-np.median(aw[:,ax]) )*0  # placeholder
    # find axis aligned with gravity at rest (pre-takeoff 1s)
    pre=d[(d.t>t[0]-1.5)&(d.t<t[0]-0.8)]
    qp=pre[['qw','qx','qy','qz']].values; qp/=np.linalg.norm(qp,axis=1,keepdims=True)
    gw=np.mean([qrot(qi,ai) for qi,ai in zip(qp,pre[['ax_g','ay_g','az_g']].values)],axis=0)
    up=gw/np.linalg.norm(gw)
    av=(aw@up - np.linalg.norm(gw))*G
    v=np.concatenate([[0],np.cumsum((av[1:]+av[:-1])/2*np.diff(tt))])
    z=np.concatenate([[0],np.cumsum((v[1:]+v[:-1])/2*np.diff(tt))])
    v0=-z[-1]/T; zz=z+v0*tt
    rows.append(dict(T=T,h_ft=G*T**2/8*100,rot=rot,gmax=s.gn.max(),amean=s.an.mean(),
                     apex_int=zz.max()*100,gw=np.linalg.norm(gw),gt=g,ndi=None))
f=pd.DataFrame(rows); f['ndi']=gt.ndi_height_cm.values
pd.set_option('display.width',200); print(f.round(3))
print(f.corr()['gt'].round(3))
