// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The UI page served at / (§8C.4). It speaks the line protocol (proto.hpp) over the WebSocket at /ws:
// SUBSCRIBE for telemetry, GET_LOG for the events it has not seen (so a dropped link loses nothing,
// §8C.6), and only the commands the link may carry. The fault policy is shown, never set (§8B.4a-1).
#include "tuner/web.hpp"

namespace tuner::web {

const char kPage[] = R"PAGE(<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Antenna tuner</title>
<style>
:root{--bg:#f6f6f4;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--ok:#1d7a3a;--warn:#a66300;--bad:#b3261e;--line:#ddd}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ececea;--mut:#9b9b95;--card:#20201f;--line:#333}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif}
main{max-width:960px;margin:0 auto;padding:16px;display:grid;gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
h1{font-size:18px;margin:0}.row{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:baseline}
.big{font-size:40px;font-weight:600;font-variant-numeric:tabular-nums}.mut{color:var(--mut)}
.v{font-variant-numeric:tabular-nums}.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
button{font:inherit;padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
input{font:inherit;width:6em;padding:5px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
#log{font:12px/1.5 ui-monospace,monospace;max-height:260px;overflow:auto;white-space:pre}
.foot{font-size:12px;margin:0 4px}a{color:inherit}
input[type=radio]{width:auto}.addr{width:9em}label{white-space:nowrap}
</style></head><body><main>
<div class="card row"><h1>Antenna tuner</h1><span id="link" class="bad">connecting</span>
<span class="mut">policy <b id="mode" class="v">-</b> (set at the box)</span><span id="derate" class="bad"></span></div>
<div class="card row"><div><div class="mut">SWR</div><div id="swr" class="big">-</div></div>
<div><div class="mut">state</div><div id="state" class="v">-</div></div>
<div><div class="mut">path</div><div id="path" class="v">-</div></div>
<div><div class="mut">frequency</div><div id="mhz" class="v">-</div></div>
<div><div class="mut">forward</div><div id="fwd" class="v">-</div></div>
<div><div class="mut">permit</div><div id="permit" class="v">-</div></div></div>
<div class="card row"><span>C1 <b id="c1" class="v">-</b> pF</span><span>C2 <b id="c2" class="v">-</b> pF</span>
<span>L <b id="l" class="v">-</b> &micro;H</span><span>tank <b id="tank" class="v">-</b> &deg;C</span></div>
<div class="card"><div class="row"><b>Faults</b><span id="faults" class="v">none</span></div></div>
<div class="card row"><button data-c="TUNE">Tune</button><button data-c="ACK">Acknowledge</button>
<span class="mut">path</span><button data-c="PATH TUNE">TUNE</button><button data-c="PATH AUX">AUX</button><button data-c="PATH CAL">CAL</button></div>
<div class="card row"><b>Preset</b><span class="mut">while receiving, after a band change</span>
<button data-c="PRESET 1.900">160</button><button data-c="PRESET 3.750">80</button><button data-c="PRESET 5.368">60</button><button data-c="PRESET 7.150">40</button><button data-c="PRESET 10.125">30</button>
<button data-c="PRESET 14.175">20</button><button data-c="PRESET 18.118">17</button><button data-c="PRESET 21.225">15</button><button data-c="PRESET 24.940">12</button><button data-c="PRESET 28.850">10</button>
<span><input id="pmhz" type="number" step="0.001" placeholder="MHz"><button id="preset">preset</button></span></div>
<div class="card row"><b>Calibrate this band</b><button data-c="CAL LOAD">load</button><button data-c="CAL OPEN">open</button>
<button data-c="CAL SHORT">short</button><button data-c="CAL SAVE">save</button>
<span><input id="watts" type="number" min="1" step="1" placeholder="W"><button id="addw">add wattmeter reading</button></span>
<span id="reply" class="mut"></span></div>
<div class="card"><b>Events</b><div id="log"></div></div>
<div class="card"><div class="row"><b>Network</b><span id="netnow" class="mut"></span></div>
<div class="row"><label><input type="radio" name="nm" id="dhcp"> DHCP</label><label><input type="radio" name="nm" id="static"> static</label>
<label>hostname <input id="host" class="addr" maxlength="31"></label></div>
<div class="row"><label>address <input id="ip" class="addr"></label><label>netmask <input id="mask" class="addr"></label>
<label>gateway <input id="gw" class="addr"></label><label>DNS <input id="dns" class="addr"></label></div>
<div class="row"><button id="netsave">Save</button><span id="netmsg" class="mut">Saved settings are used from the next restart.
If the tuner cannot be reached then, hold the recovery button at power-up: DHCP as "tuner".</span></div></div>
<p class="foot mut">Source: <a href="https://github.com/driador/antenna-tuner">github.com/driador/antenna-tuner</a>
&middot; GPL-3.0-or-later, built with QNEthernet (AGPL-3.0-or-later)</p>
</main><script>
const F=["over-temperature","carrier lost","no solution","tune failed","over-SWR trip","limit switch hit","encoder mismatch","self-test failure","K1/K2 relay mismatch"];
let ws=null,next=1,netwait=false;const $=id=>document.getElementById(id);
function cs(s){let c=0;for(const ch of s)c^=ch.charCodeAt(0);return c.toString(16).toUpperCase().padStart(2,"0")}
function send(s){if(ws&&ws.readyState==1)ws.send(s+"*"+cs(s))}
function kv(s){const o={};for(const p of s.split(" ")){const i=p.indexOf("=");if(i>0)o[p.slice(0,i)]=p.slice(i+1)}return o}
function names(mask,cls){const out=[];for(let i=0;i<F.length;i++)if(mask&(1<<i))out.push(cls+" "+F[i]);return out}
function netmode(){const st=$("static").checked;for(const k of["ip","mask","gw","dns"])$(k).disabled=!st}
function netshow(n){$("dhcp").checked=n.mode=="dhcp";$("static").checked=n.mode=="static";$("host").value=n.hostname;
 $("ip").value=n.ip;$("mask").value=n.netmask;$("gw").value=n.gateway;$("dns").value=n.dns;netmode();
 $("netnow").textContent="in use now: "+n.now+(n.pending=="1"?" (the saved settings take over at the next restart)":"")}
function line(raw){const star=raw.lastIndexOf("*");if(star<0||cs(raw.slice(0,star))!=raw.slice(star+1))return;const s=raw.slice(0,star);
 if(s.startsWith("TLM ")){const t=kv(s.slice(4)),swr=parseFloat(t.swr);
  $("swr").textContent=swr>=99?"high":swr.toFixed(2);$("swr").className="big "+(swr<=1.5?"ok":swr<=2?"warn":"bad");
  $("state").textContent=t.state;$("path").textContent=t.path;$("mode").textContent=t.mode;
  $("mhz").textContent=t.carrier=="1"?t.mhz+" MHz":"no carrier";$("fwd").textContent=t.fwd=="-"?"not calibrated":t.fwd+" W";
  $("permit").textContent=(t.permit=="1"?"up":"down")+(t.bypass=="1"?" (BYPASS)":"");$("permit").className="v "+(t.bypass=="1"?"bad":t.permit=="1"?"ok":"warn");
  for(const k of["c1","c2","l","tank"])$(k).textContent=t[k];
  $("derate").textContent=t.derate=="1"?"DERATE: the RF bay averages "+t.loss+" W of loss against 200 W of cooling; keep under "+t.lim+" W here":"";
  const f=names(parseInt(t.c,16),"C").concat(names(parseInt(t.b,16),"B"));$("faults").textContent=f.length?f.join(", "):"none";
  $("faults").className="v "+(f.length?"bad":"ok");if(parseInt(t.ev)>next)send("GET_LOG "+next)}
 else if(s.startsWith("EVT ")){const e=kv(s.slice(4)),q=parseInt(e.seq);if(q<next)return;next=q+1;
  $("log").textContent=s.slice(4)+"\n"+$("log").textContent}
 else if(s.startsWith("NET "))netshow(kv(s.slice(4)))
 else if(s.startsWith("OK ")||s.startsWith("ERR ")){if(netwait){netwait=false;$("netmsg").textContent=s}else $("reply").textContent=s}}
function connect(){ws=new WebSocket("ws://"+location.host+"/ws");
 ws.onopen=()=>{$("link").textContent="connected";$("link").className="ok";send("SUBSCRIBE 10");send("GET_LOG "+next);send("NET")};
 ws.onmessage=m=>{for(const l of String(m.data).split("\n"))if(l)line(l.trim())};
 ws.onclose=()=>{$("link").textContent="link lost: the tuner carries on, protection is at the box";$("link").className="bad";setTimeout(connect,2000)}}
document.querySelectorAll("button[data-c]").forEach(b=>b.onclick=()=>send(b.dataset.c));
$("addw").onclick=()=>{const w=parseFloat($("watts").value);if(w>0)send("CAL WATTS "+w)};
$("preset").onclick=()=>{const f=parseFloat($("pmhz").value);if(f>0)send("PRESET "+f)};
$("dhcp").onchange=$("static").onchange=netmode;
$("netsave").onclick=()=>{const v=k=>$(k).value.trim(),st=$("static").checked;
 let c="NET mode="+(st?"static":"dhcp")+" hostname="+v("host");
 if(st)c+=" ip="+v("ip")+" netmask="+v("mask")+" gateway="+v("gw")+" dns="+v("dns");netwait=true;send(c)};
connect();
</script></body></html>
)PAGE";

const size_t kPageLength = sizeof kPage - 1;

}  // namespace tuner::web
