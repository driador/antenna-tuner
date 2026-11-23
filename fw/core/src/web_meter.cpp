// SPDX-FileCopyrightText: 2026 Reuben A. Popp
// SPDX-License-Identifier: GPL-3.0-or-later

// The bench meter served at /meter (§8C.4): a page for a tablet left on at the bench. Large SWR and
// forward power with bars, the state and frequency, the faults, the prompts the tuner publishes (a TUNE
// waiting for a carrier, drive over the tune window, the derate), the latest events, and only TUNE and
// ACK. The same WebSocket and protocol as the full page at /, which it links to.
#include "tuner/flashdata.hpp"
#include "tuner/web.hpp"

namespace tuner::web {

const char kMeter[] TUNER_FLASH_DATA = R"PAGE(<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<title>Tuner meter</title>
<style>
:root{--bg:#0e0e0d;--fg:#f0f0ec;--mut:#8d8d86;--panel:#1a1a19;--line:#2c2c2a;--ok:#3fbf62;--warn:#e0a030;--bad:#f0503c}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.3 system-ui,sans-serif;display:flex;flex-direction:column;
 gap:1.2vh;padding:max(1.5vh,env(safe-area-inset-top)) 2vw 1.5vh;font-variant-numeric:tabular-nums;user-select:none}
.strip{display:flex;flex-wrap:wrap;gap:.4em 1.6em;align-items:baseline;font-size:clamp(15px,2.6vw,26px)}
.meters{flex:1;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:1.2vh 2vw;min-height:0}
.m{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1.5vh 2vw;display:flex;flex-direction:column;justify-content:center}
.lab{color:var(--mut);font-size:clamp(14px,2vw,22px);display:flex;justify-content:space-between}
.scale{position:relative;height:1.4em;color:var(--mut);font-size:clamp(13px,1.8vw,20px);margin-top:.3vh}
.scale span{position:absolute;transform:translateX(-50%);white-space:nowrap}.scale .l{transform:none}.scale .r{transform:translateX(-100%)}
.num{font-size:clamp(56px,min(15vw,26vh),240px);font-weight:650;line-height:1.05}
.idle{font-size:.3em;color:var(--mut);font-weight:400}
.unit{font-size:.35em;color:var(--mut);font-weight:400;margin-left:.15em}
.bar{position:relative;height:clamp(14px,3vh,30px);background:var(--line);border-radius:8px;overflow:hidden;margin-top:1vh}
.fill{position:absolute;left:0;top:0;bottom:0;width:0;transition:width .12s linear}
.tick{position:absolute;top:0;bottom:0;width:3px;background:var(--fg);opacity:.85}
.pk{position:absolute;top:0;bottom:0;width:3px;background:var(--warn)}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.mut{color:var(--mut)}
.fill.ok{background:var(--ok)}.fill.warn{background:var(--warn)}.fill.bad{background:var(--bad)}
#say{font-size:clamp(17px,2.8vw,30px);min-height:1.4em}
#faults{font-size:clamp(17px,2.8vw,30px);border-radius:12px;padding:.3em .6em}
#faults.bad{background:var(--bad);color:#fff}#faults.blink{animation:b 1s steps(2) infinite}
@keyframes b{50%{opacity:.35}}
.keys{display:flex;flex-wrap:wrap;gap:1.2vw;align-items:center}
button{font:inherit;font-size:clamp(18px,3vw,32px);padding:.45em 1.4em;border-radius:12px;border:1px solid var(--line);
 background:var(--panel);color:var(--fg);touch-action:manipulation}
button:active{background:var(--line)}
#ev{font:clamp(12px,1.5vw,16px)/1.4 ui-monospace,monospace;color:var(--mut);white-space:pre;overflow:hidden;max-height:4.3em}
#lost{position:fixed;inset:0;background:rgba(14,14,13,.92);display:none;align-items:center;justify-content:center;text-align:center;
 font-size:clamp(20px,4vw,44px);padding:5vw}
a{color:var(--mut)}
</style></head><body>
<div class="strip"><b id="state">-</b><span id="mhz">-</span><span id="path" class="mut">-</span>
<span id="permit" class="mut">-</span><span id="tank" class="mut"></span></div>
<div class="meters">
<div class="m"><div class="lab"><span>SWR</span><span id="swrnote"></span></div><div class="num" id="swr">-</div>
<div class="bar"><div class="fill" id="swrbar"></div><div class="tick" style="left:36.9%"></div><div class="tick" style="left:63.1%"></div></div>
<div class="scale"><span class="l" style="left:0">1</span><span style="left:36.9%">1.5</span><span style="left:63.1%">2</span>
<span class="r" style="left:100%">3+</span></div></div>
<div class="m"><div class="lab"><span>forward</span><span id="peak"></span></div><div class="num" id="fwd">-</div>
<div class="bar"><div class="fill" id="fwdbar"></div><div class="pk" id="pkbar"></div>
<div class="tick" style="left:90.9%"></div><div class="tick" id="limtick" style="display:none"></div></div>
<div class="scale"><span class="l" style="left:0">0</span><span style="left:30.3%">500</span><span style="left:60.6%">1000</span>
<span style="left:90.9%">1500 W</span></div></div>
</div>
<div id="say"></div>
<div id="faults" class="mut">no faults</div>
<div class="keys"><button data-c="TUNE">Tune</button><button data-c="ACK">Acknowledge</button>
<button id="snd">Sound: off</button><a href="/">full page</a></div>
<div id="ev"></div>
<div id="lost">LINK LOST<br><span class="mut">The tuner carries on; its protection is at the box.</span></div>
<script>
const F=["over-temperature","carrier lost","no solution","tune failed","over-SWR trip","limit switch hit","encoder mismatch","self-test failure","K1/K2 relay mismatch","built-in test","tune power too high","forward power over rating","output over-voltage","output trip (arc or imbalance)"];
const FS=1650;let ws=null,pk=0,pkt=0,ac=null,on=false,lv=0,tm=null,evs=[];const $=id=>document.getElementById(id);
function cs(s){let c=0;for(const ch of s)c^=ch.charCodeAt(0);return c.toString(16).toUpperCase().padStart(2,"0")}
function send(s){if(ws&&ws.readyState==1)ws.send(s+"*"+cs(s))}
function kv(s){const o={};for(const p of s.split(" ")){const i=p.indexOf("=");if(i>0)o[p.slice(0,i)]=p.slice(i+1)}return o}
function names(m,c){const o=[];for(let i=0;i<F.length;i++)if(m&(1<<i))o.push(c+" "+F[i]);return o}
function bar(id,f,c){const e=$(id);e.style.width=Math.max(0,Math.min(1,f))*100+"%";e.className="fill "+c}
function beep(hz,ms){if(!on||!ac||ac.state!="running")return;const o=ac.createOscillator(),g=ac.createGain();
 o.type="square";o.frequency.value=hz;g.gain.value=0.12;o.connect(g);g.connect(ac.destination);o.start();o.stop(ac.currentTime+ms/1000)}
function alarm(l){if(l==lv)return;lv=l;clearInterval(tm);if(!l)return;
 const p=[null,[1200,60,15000],[660,150,2000],[880,150,300]][l];beep(p[0],p[1]);tm=setInterval(()=>beep(p[0],p[1]),p[2])}
function line(raw){const st=raw.lastIndexOf("*");if(st<0||cs(raw.slice(0,st))!=raw.slice(st+1))return;const s=raw.slice(0,st);
 if(s.startsWith("EVT ")){evs.unshift(s.slice(4).replace(/^seq=\d+ /,""));evs=evs.slice(0,3);$("ev").textContent=evs.join("\n");return}
 if(!s.startsWith("TLM "))return;
 const t=kv(s.slice(4)),car=t.carrier=="1",swr=parseFloat(t.swr),fw=t.fwd=="-"?-1:parseFloat(t.fwd),lim=parseFloat(t.lim),now=Date.now();
 const sc=swr<=1.5?"ok":swr<=2?"warn":"bad";
 $("state").textContent=t.state;$("state").className=t.state=="MATCHED"?"ok":t.state=="FAULT"?"bad":t.state=="IDLE"?"":"warn";
 $("mhz").textContent=car?t.mhz+" MHz":"no carrier";$("path").textContent=t.path+" path";
 $("permit").textContent=t.bypass=="1"?"BYPASS":"permit "+(t.permit=="1"?"up":"down");$("permit").className=t.bypass=="1"?"bad":t.permit=="1"?"ok":"warn";
 $("tank").textContent="tank "+t.tank+" °C";
 $("swr").innerHTML=car?(swr>=99?"high":swr.toFixed(2)):'<span class="idle">no carrier</span>';$("swr").className="num "+(car?sc:"");
 bar("swrbar",car?Math.log(Math.max(swr,1))/Math.log(3):0,sc);
 if(fw>pk||now-pkt>2000){pk=Math.max(fw,0);pkt=now}
 $("fwd").innerHTML=fw<0?'<span class="idle">not calibrated</span>':Math.round(fw)+'<span class="unit">W</span>';
 $("fwd").className="num "+(fw>1500?"bad":"");bar("fwdbar",fw/FS,fw>1500?"bad":fw>lim?"warn":"ok");
 $("pkbar").style.left=Math.min(pk/FS,1)*100+"%";$("peak").textContent=pk>0?"peak "+Math.round(pk)+" W":"";
 $("limtick").style.display=lim<1500?"block":"none";$("limtick").style.left=lim/FS*100+"%";
 const say=[];if(t.want=="1")say.push("Key a carrier to tune, under 100 W.");
 if(t.hold=="1")say.push("Reduce drive: the tune waits for under 100 W.");
 if(t.derate=="1")say.push("DERATE: keep under "+t.lim+" W here.");if(t.bitrun=="1")say.push("Self-test running.");
 $("say").textContent=say.join(" ");$("say").className=t.hold=="1"||t.derate=="1"?"warn":"";
 const c=parseInt(t.c,16)||0,b=parseInt(t.b,16)||0,hot=t.hot=="1";
 const f=(hot?["A over-temperature"]:[]).concat(names(c,"C"),names(b,"B"));
 $("faults").textContent=f.length?"FAULT: "+f.join(", ")+(b?" (Acknowledge)":"")+(c?" (clear at the box)":""):"no faults";
 $("faults").className=f.length?"bad"+(c?" blink":""):"mut";
 alarm(c?3:b?2:hot||t.derate=="1"?1:0)}
function connect(){ws=new WebSocket("ws://"+location.host+"/ws");
 ws.onopen=()=>{$("lost").style.display="none";send("SUBSCRIBE 10")};
 ws.onmessage=m=>{for(const l of String(m.data).split("\n"))if(l)line(l.trim())};
 ws.onclose=()=>{$("lost").style.display="flex";alarm(0);setTimeout(connect,2000)}}
document.querySelectorAll("button[data-c]").forEach(b=>b.onclick=()=>send(b.dataset.c));
$("snd").onclick=()=>{on=!on;$("snd").textContent="Sound: "+(on?"on":"off");
 if(on&&!ac){const A=window.AudioContext||window.webkitAudioContext;if(A)ac=new A()}if(ac)ac.resume();const l=lv;lv=-1;alarm(l)};
if(navigator.wakeLock)navigator.wakeLock.request("screen").catch(()=>{});
connect();
</script></body></html>
)PAGE";

const size_t kMeterLength = sizeof kMeter - 1;

}  // namespace tuner::web
