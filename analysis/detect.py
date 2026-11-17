import pandas as pd, numpy as np, sys
G=9.80665
def load(p):
    d=pd.read_csv(p)
    d['t']=d.t_ms/1000
    d['an']=np.sqrt(d.ax_g**2+d.ay_g**2+d.az_g**2)
    d['gn']=np.sqrt(d.gx_dps**2+d.gy_dps**2+d.gz_dps**2)
    return d

def detect(d, hi=8.0, min_flight=0.25, max_flight=1.0):
    """takeoff = first |a|>hi spike of an event; landing = first |a|>hi spike >=min_flight later."""
    t=d.t.values; an=d.an.values
    idx=np.where(an>hi)[0]
    jumps=[]; i=0
    while i<len(idx):
        k=idx[i]; t0=t[k]
        # landing: first spike after t0+min_flight
        cand=idx[(t[idx]>t0+min_flight)&(t[idx]<t0+max_flight)]
        if len(cand)==0:
            i+=1; continue
        l=cand[0]; t1=t[l]
        jumps.append((k,l))
        # skip until landing-related spikes end (0.4s after landing)
        while i<len(idx) and t[idx[i]]<t1+0.4: i+=1
    return jumps

def qrot(q,v):
    # rotate v by quaternion q (w,x,y,z), normalized
    w,x,y,z=q
    u=np.array([x,y,z]); return v+2*np.cross(u,np.cross(u,v)+w*v)

def foot_apex(d,k,l):
    """integrate world-vertical acc during flight with z(t0)=z(t1)=0"""
    s=d.iloc[k:l+1]
    q=s[['qw','qx','qy','qz']].values; q=q/np.linalg.norm(q,axis=1,keepdims=True)
    a=s[['ax_g','ay_g','az_g']].values
    aw=np.array([qrot(qi,ai) for qi,ai in zip(q,a)])
    t=s.t.values-s.t.values[0]
    out={}
    for ax in range(3):
        az=(aw[:,ax])*G
        out[ax]=az
    return t,aw
if __name__=='__main__':
    d=load(sys.argv[1])
    for k,l in detect(d):
        print(f"takeoff {d.t[k]:.3f} landing {d.t[l]:.3f} flight {d.t[l]-d.t[k]:.3f} mid {(d.t[k]+d.t[l])/2:.3f}")
