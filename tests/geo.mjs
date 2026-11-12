import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const context=vm.createContext({});vm.runInContext(readFileSync('viewer/geo.js','utf8')+';globalThis.geo=SaiwaiGeo;',context);
const geo=context.geo;
// Independent PROJ reference at opposite envelope corners.
for(const [lat,lon,x,y] of [[35.5261645,139.654139,377975.6126668628,3932228.1085351985],[35.5620586,139.704239,382570.6081960889,3936148.458726131]]){
 const m=geo.forward(lat,lon);assert.ok(Math.hypot(m[0]-x,m[1]-y)<.01);
 const q=geo.inverse(x,y);assert.ok(Math.hypot(q[0]-lat,q[1]-lon)<1e-7);
}
console.log('viewer UTM54N: PROJ-reference conversions and roundtrip pass');
vm.runInContext(readFileSync('viewer/projection.js','utf8')+';globalThis.projection=SaiwaiProjection;',context);
const projection=context.projection,map={scale:2,width:14142,top:1987.76695};
// A 32m hill with non-flat slopes. A pin at the hill must survive cursor inversion
// and rotation without sliding to a sea-level projection. Search h is absolute.
const ground=(x,z)=>32+.05*x-.04*z;
for(const look of [45,135,225,315]){
 const x=50,z=-80,h=ground(x,z);
 const p=projection.project(x,z,h,look,map);
 const g=projection.intersect(p.x,p.y,ground,look,map);
 assert.ok(Math.hypot(g.x-x,g.z-z)<.001,`hill intersection look ${look}`);
 const next=projection.project(g.x,g.z,ground(g.x,g.z),(look+90)%360,map);
 const expected=projection.project(x,z,h,(look+90)%360,map);
 assert.ok(Math.hypot(next.x-expected.x,next.y-expected.y)<.001,`hill rotation look ${look}`);
 const marker=projection.project(x,z,h+2,look,map);
 assert.ok(Math.abs((p.y-marker.y)-2*Math.cos(Math.PI/6)*map.scale)<1e-6);
}
console.log('terrain projection: elevated pins, absolute search offsets and all four rotations pass');
