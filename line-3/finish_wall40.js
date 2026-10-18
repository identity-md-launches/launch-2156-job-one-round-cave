'use strict';
// Transfer generated pigment only. Existing wall pixels outside this patch stay exact.
const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const {readPNG,writePNG}=require('./finish_wall36.js');
const encode=require('./tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ancestor=fs.readFileSync('artifacts/line-3/wall-v20.png');
const draftBytes=fs.readFileSync('artifacts/line-3/wall-v21.png');
const old=readPNG(ancestor),draft=readPNG(draftBytes),pixels=Buffer.from(old.pixels);
assert.deepEqual([old.width,old.height],[1254,1254]);
assert(!fs.existsSync('dist/line-3/40.json'));
const rect=[535,105,245,90];
for(let y=0;y<rect[3];y++)for(let x=0;x<rect[2];x++){
 const sx=Math.floor(x*draft.width/rect[2]),sy=Math.floor(y*draft.height/rect[3]);
 const at=((y+rect[1])*1254+x+rect[0])*3;
 const [r,g,b]=draft.pixels.subarray((sy*draft.width+sx)*3,(sy*draft.width+sx)*3+3);
 let color;
 if(r>g*1.45&&r>90&&g>b*1.12)color=[147,59,31];
 else if(r>g*1.13&&g>b*1.4&&r>110)color=[181,123,47];
 else if(r<83&&g<78&&b<72)color=[39,30,23];
 else continue;
 for(let c=0;c<3;c++)pixels[at+c]=Math.round(old.pixels[at+c]*.30+color[c]*.70);
}
let changed=0,outside=0;
for(let i=0;i<1254*1254;i++)if(!pixels.subarray(i*3,i*3+3).equals(old.pixels.subarray(i*3,i*3+3))){
 changed++;const x=i%1254,y=Math.floor(i/1254);
 if(x<rect[0]||x>=rect[0]+rect[2]||y<rect[1]||y>=rect[1]+rect[3])outside++;
}
assert(changed>0);assert.equal(outside,0);
const png=writePNG(1254,1254,pixels);assert(readPNG(png).pixels.equals(pixels));
const rgba=Buffer.alloc(512*512*4);
for(let y=0;y<512;y++)for(let x=0;x<512;x++){
 const xa=Math.floor(x*1254/512),xb=Math.floor((x+1)*1254/512),ya=Math.floor(y*1254/512),yb=Math.floor((y+1)*1254/512);
 for(let c=0;c<3;c++){
  let total=0;for(let yy=ya;yy<yb;yy++)for(let xx=xa;xx<xb;xx++)total+=pixels[(yy*1254+xx)*3+c];
  rgba[(y*512+x)*4+c]=Math.round(total/((xb-xa)*(yb-ya)));
 }
 rgba[(y*512+x)*4+3]=255;
}
const jpg=encode({data:rgba,width:512,height:512},77).data;assert(jpg.length<100000);
fs.writeFileSync('artifacts/line-3/wall-v21.png',png);
fs.unlinkSync('artifacts/line-3/wall.png');fs.symlinkSync('wall-v21.png','artifacts/line-3/wall.png');
fs.writeFileSync('dist/line-3/40.jpg',jpg,{flag:'wx'});
const record={name:'The Compared Bowls',image:'https://api.imd.fun/artifacts/'+sha(png),attributes:[
 ['Cave','Crystal'],['Wall','Line 3'],['Number',40],['Left behind','Search Compare'],
 ['Meaning','Two ochre-filled bowls reveal what a changed search keeps and loses.'],
 ['One thing','Offline document search with exact source line citations']
].map(([trait_type,value])=>({trait_type,value}))};
fs.writeFileSync('dist/line-3/40.json',JSON.stringify(record,null,2)+'\n',{flag:'wx'});
const report={wall:'artifacts/line-3/wall-v21.png',continuation:'artifacts/line-3/wall.png',
 format:'PNG',dimensions:[1254,1254],mode:'RGB',bytes:png.length,sha256:sha(png),
 ancestor_sha256:sha(ancestor),generated_motif_sha256:sha(draftBytes),new_mark_rectangle:rect,
 changed_pixels:changed,changed_pixels_outside_rectangle:outside,
 thumbnail:{path:'dist/line-3/40.jpg',format:'JPEG',dimensions:[512,512],bytes:jpg.length},
 visual_review:'Pending final inspection',
 hand_review:{new_hands:0,new_handprints:0,inherited_open_hand_visible_digits:5,inherited_gripping_hand:'Partly occluded; full count unverified and unchanged.'},
 unmet_visual_requirements:['The complete digit count of an inherited partly occluded gripping hand cannot be confirmed.']};
fs.writeFileSync('line-3/IMAGE-40.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
