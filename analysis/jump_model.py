"""Reference implementation of the jump-height estimator (mirrored in docs/jump.js).
takeoff: first |a| > TO_G after quiet stance; landing: first |a| > LD_G at least MIN_FLIGHT later.
Foot apex: rotate acc to world frame by quaternion, project on gravity direction measured in
quiet stance before the jump, double-integrate with z(takeoff)=z(landing)=0 constraint.
"""
import numpy as np, pandas as pd, sys
G=9.80665
def qrot(q,v):
    w=q[:,0:1]; u=q[:,1:]
    return v+2*np.cross(u,np.cross(u,v)+w*v)
def load(p):
    d=pd.read_csv(p); t=d.t_ms.values/1000
    Q=d[['qw','qx','qy','qz']].values; Q=Q/np.linalg.norm(Q,axis=1,keepdims=True)
    A=d[['ax_g','ay_g','az_g']].values
    return t,A,qrot(Q,A)
def detect(t,A,TO_G=6.0,LD_G=10.0,MIN_FLIGHT=0.25,MAX_FLIGHT=1.0):
    an=np.linalg.norm(A,axis=1); out=[]; i=0
    while i<len(t):
        if an[i]>TO_G:
            c=np.where((t>t[i]+MIN_FLIGHT)&(t<t[i]+MAX_FLIGHT)&(an>LD_G))[0]
            if len(c):
                out.append((i,c[0])); i=np.searchsorted(t,t[c[0]]+0.5); continue
        i+=1
    return out
def apex_cm(t,W,k,l,ref=(1.5,0.5)):
    m=(t>t[k]-ref[0])&(t<t[k]-ref[1]); gw=W[m].mean(0); gm=np.linalg.norm(gw); up=gw/gm
    tt=t[k:l+1]-t[k]; av=(W[k:l+1]@up-gm)*G
    v=np.concatenate([[0],np.cumsum((av[1:]+av[:-1])/2*np.diff(tt))])
    z=np.concatenate([[0],np.cumsum((v[1:]+v[:-1])/2*np.diff(tt))])
    return (z-z[-1]*tt/tt[-1]).max()*100
if __name__=='__main__':
    t,A,W=load(sys.argv[1]); gt=pd.read_csv(sys.argv[2]).manual_gt_cm.values
    for TO in [4,6,8]:
      for LD in [8,10,12]:
        J=detect(t,A,TO,LD)
        if len(J)!=len(gt): print(TO,LD,'n=',len(J)); continue
        ap=np.array([apex_cm(t,W,k,l) for k,l in J]); T=np.array([t[l]-t[k] for k,l in J])
        print(f"TO{TO} LD{LD} MAE {np.abs(ap-gt).mean():.2f} max {np.abs(ap-gt).max():.1f} r {np.corrcoef(ap,gt)[0,1]:.3f}")
    J=detect(t,A); ap=np.array([apex_cm(t,W,k,l) for k,l in J])
    pred=[]
    for i in range(len(gt)):
        m=np.arange(len(gt))!=i; c=np.polyfit(ap[m],gt[m],1); pred.append(np.polyval(c,ap[i]))
    pred=np.array(pred)
    print('fit (all):',np.polyfit(ap,gt,1).round(4))
    print(pd.DataFrame(dict(takeoff=[t[k] for k,l in J],flight=[t[l]-t[k] for k,l in J],gt=gt,raw=ap.round(1),loocv=pred.round(1))))
    print('raw MAE',np.abs(ap-gt).mean().round(2),' LOOCV-calibrated MAE',np.abs(pred-gt).mean().round(2))
