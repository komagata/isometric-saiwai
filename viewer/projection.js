// Heights passed to project are absolute metres above Tokyo Bay MSL.
// Ground pins use heightAt; search cards add an explicit above-ground marker offset.
const SaiwaiProjection = (() => {
  const cos30=Math.cos(Math.PI/6);
  function project(x,z,elevation,look,map){
    const a=look*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
    return {x:(x*c+z*s)*map.scale+map.width/2,y:(map.top-((x*s-z*c)/2+elevation*cos30))*map.scale};
  }
  function intersect(px,py,heightAt,look,map){
    const a=look*Math.PI/180,c=Math.cos(a),s=Math.sin(a),u=px/map.scale-map.width/(2*map.scale),v=map.top-py/map.scale;
    // Bare-earth elevations of this extent are bounded by -4..47 m. A wider bracket
    // avoids treating sea level as the hill surface; no building roof intersection is claimed.
    let lo=-30,hi=250;
    for(let i=0;i<25;i++){
      const h=(lo+hi)/2,w=2*(v-h*cos30),x=u*c+w*s,z=u*s-w*c;
      if(h>heightAt(x,z))hi=h;else lo=h;
    }
    const w=2*(v-(lo+hi)/2*cos30);
    return {x:u*c+w*s,z:u*s-w*c};
  }
  return {project,intersect};
})();
