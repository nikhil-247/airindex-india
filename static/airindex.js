const API="/api/v1";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
const money=v=>"₹"+Number(v||0).toLocaleString("en-IN",{maximumFractionDigits:0});
const pct=v=>(Number(v)>=0?"+":"")+Number(v||0).toFixed(2)+"%";
const getJSON=async path=>{const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw new Error("API "+r.status);return r.json()};
function setActiveNav(){const path=location.pathname.replace(/\/$/,"")||"/";document.querySelectorAll(".navlinks a").forEach(a=>{const href=new URL(a.href).pathname.replace(/\/$/,"")||"/";if(href===path)a.classList.add("active")})}
function fmtDate(s){try{return new Date(s).toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"})}catch{return s}}
function routeRows(index){return Object.entries(index.routes).sort((a,b)=>b[1].index-a[1].index).map(([route,item])=>({route,...item}))}
async function loadOverview(){return getJSON(API+"/demo/overview")}
async function loadHealth(){return getJSON("/health")}
window.AirIndex={esc,money,pct,getJSON,setActiveNav,fmtDate,routeRows,loadOverview,loadHealth};setActiveNav();