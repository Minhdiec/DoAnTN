// node render.js <drawio file> <page index> <out.html>
const fs=require("fs");const [,,f,p,o]=process.argv;
const xml=fs.readFileSync(f,"utf8");
const cfg=JSON.stringify({xml, page:Number(p), nav:false, toolbar:"", lightbox:false, resize:false});
const attr=cfg.replace(/&/g,"&amp;").replace(/'/g,"&#39;").replace(/</g,"&lt;");
fs.writeFileSync(o,`<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#fff}</style></head><body><div class="mxgraph" data-mxgraph='${attr}'></div><script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script></body></html>`);
