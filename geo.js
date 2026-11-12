// WGS84 / UTM54N (central meridian 141 E), standard Transverse Mercator series.
// Kept local so shared pin links also work under GitHub Pages subpaths.
const SaiwaiGeo = (() => {
  const a=6378137,e=.0066943799901413165,k=.9996,ep=e/(1-e),rad=Math.PI/180;
  function forward(lat,lon){
    const p=lat*rad,l=(lon-141)*rad,s=Math.sin(p),c=Math.cos(p),t=Math.tan(p)**2,C=ep*c*c,N=a/Math.sqrt(1-e*s*s),A=c*l;
    const M=a*((1-e/4-3*e**2/64-5*e**3/256)*p-(3*e/8+3*e**2/32+45*e**3/1024)*Math.sin(2*p)+(15*e**2/256+45*e**3/1024)*Math.sin(4*p)-35*e**3/3072*Math.sin(6*p));
    return [500000+k*N*(A+(1-t+C)*A**3/6+(5-18*t+t*t+72*C-58*ep)*A**5/120),k*(M+N*Math.tan(p)*(A*A/2+(5-t+9*C+4*C*C)*A**4/24+(61-58*t+t*t+600*C-330*ep)*A**6/720))];
  }
  function inverse(x,y){
    const m=y/k,mu=m/(a*(1-e/4-3*e**2/64-5*e**3/256)),e1=(1-Math.sqrt(1-e))/(1+Math.sqrt(1-e));
    const p=mu+(3*e1/2-27*e1**3/32)*Math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*Math.sin(4*mu)+151*e1**3/96*Math.sin(6*mu)+1097*e1**4/512*Math.sin(8*mu);
    const s=Math.sin(p),c=Math.cos(p),t=Math.tan(p)**2,C=ep*c*c,N=a/Math.sqrt(1-e*s*s),R=a*(1-e)/(1-e*s*s)**1.5,D=(x-500000)/(N*k);
    return [(p-N*Math.tan(p)/R*(D*D/2-(5+3*t+10*C-4*C*C-9*ep)*D**4/24+(61+90*t+298*C+45*t*t-252*ep-3*C*C)*D**6/720))/rad,141+(D-(1+2*t+C)*D**3/6+(5-2*C+28*t-3*C*C+8*ep+24*t*t)*D**5/120)/c/rad];
  }
  return {forward,inverse};
})();
