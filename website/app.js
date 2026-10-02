"use strict";
const sample=[
 {id:"8cb763802590",primitive:"RSA",role:"unknown",confidence:"ambiguous",decision:"abstain",file:"review_rsa_import_only.py"},
 {id:"4a2c2c871088",primitive:"RSA",role:"signature",confidence:"direct",decision:"recommend",file:"review_rsa_jwt_signing.py"},
 {id:"8477083d34c8",primitive:"RSA padding (OAEP / PKCS1v15)",role:"key_transport",confidence:"direct",decision:"recommend",file:"review_rsa_key_transport.py"},
 {id:"c74a9bcb0014",primitive:"RSA",role:"key_transport",confidence:"direct",decision:"recommend",file:"review_rsa_key_transport.py"}
];
const esc=v=>String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
function renderDemo(){const body=document.getElementById("demo-rows"),role=document.getElementById("demo-role");if(!body)return;const rows=sample.filter(x=>!role.value||x.role===role.value);document.getElementById("demo-count").textContent=rows.length+" of "+sample.length+" fixed sample findings";body.innerHTML=rows.map(x=>"<tr><td><code>"+esc(x.id)+"</code></td><td>"+esc(x.primitive)+"</td><td>"+esc(x.role)+"</td><td>"+esc(x.confidence)+"</td><td><span class=\"tag\">"+esc(x.decision)+"</span></td><td><code>"+esc(x.file)+"</code></td></tr>").join("")||'<tr><td colspan="6">No matching fixed-sample findings.</td></tr>';role.onchange=renderDemo}renderDemo();
