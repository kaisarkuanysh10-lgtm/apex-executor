import { useState, useEffect, useRef, useCallback } from "react";
import * as THREE from "three";

/* ═══════════════════════════════════════════════════════════
   CONSTANTS & CONFIGURATION
═══════════════════════════════════════════════════════════ */

const ADMIN_CREDENTIALS = {
  id: "admin_001",
  username: "apexstudio",
  password: "apexstudio_key4014VIP148643",
  email: "admin@apexstudio.gg",
  bobux: 999999999,
  verified: true,
  isAdmin: true,
  avatar: "🔷",
  followers: 999999,
  bio: "Official ApexStudio Platform",
  friends: ["u1", "u2", "u3"],
  banned: false,
};

const PROFANITY = [
  "fuck","fu_ck","f**k","f.uck","fuk","fvck","sh1t","shit","ass","bitch",
  "nigger","nigga","faggot","fag","retard","cunt","slut","whore","dick","cock",
  "pussy","bastard","motherfucker","asshole","dumbass","jackass",
];

const PLATFORM_TAX = 0.30;

const INIT_USERS = [
  { id:"u1", username:"CoolGamer99",  email:"cool@test.com",  password:"test123", bobux:250,  verified:false, isAdmin:false, avatar:"🎮", followers:85000, friends:["u2","u3"], banned:false, currentGame:"Neon Racers", inventory:[] },
  { id:"u2", username:"StarBuilder",  email:"star@test.com",  password:"test123", bobux:480,  verified:false, isAdmin:false, avatar:"⭐", followers:12000, friends:["u1"],       banned:false, currentGame:"Sky Wars",    inventory:[] },
  { id:"u3", username:"PixelKnight", email:"pixel@test.com", password:"test123", bobux:90,   verified:false, isAdmin:false, avatar:"⚔️", followers:3400,  friends:["u1"],       banned:false, currentGame:null,          inventory:[] },
  { id:"u4", username:"NeonDrifter", email:"neon@test.com",  password:"test123", bobux:1200, verified:false, isAdmin:false, avatar:"🌊", followers:72000, friends:[],            banned:false, currentGame:"Dragon Quest", inventory:[] },
];

const INIT_ITEMS = [
  { id:"i1", name:"Crimson Jacket",   creator:"CoolGamer99",  price:15, thumbnail:"🧥", sales:234, category:"Tops",        createdAt:"2025-01-10" },
  { id:"i2", name:"Galaxy Pants",     creator:"StarBuilder",  price:8,  thumbnail:"👖", sales:89,  category:"Bottoms",     createdAt:"2025-02-01" },
  { id:"i3", name:"Neon Shades",      creator:"PixelKnight", price:6,  thumbnail:"🕶️", sales:412, category:"Accessories", createdAt:"2025-01-20" },
  { id:"i4", name:"Cyber Hoodie",     creator:"NeonDrifter",  price:20, thumbnail:"🫲", sales:55,  category:"Tops",        createdAt:"2025-03-05" },
  { id:"i5", name:"Shadow Cape",      creator:"apexstudio",  price:50, thumbnail:"🦸", sales:1024,category:"Full Body",   createdAt:"2024-12-01" },
  { id:"i6", name:"Pixel Boots",      creator:"CoolGamer99",  price:12, thumbnail:"👢", sales:188, category:"Footwear",    createdAt:"2025-02-14" },
];

const GAMES = [
  { id:"g1", name:"Neon Racers",       players:1203, thumbnail:"🏎️", genre:"Racing",   rating:4.7, desc:"High-speed neon racing across futuristic tracks." },
  { id:"g2", name:"Sky Wars",          players:8741, thumbnail:"⚔️", genre:"Battle",   rating:4.9, desc:"Epic PvP battles in the clouds." },
  { id:"g3", name:"Builder's Paradise",players:3421, thumbnail:"🏗️", genre:"Creative", rating:4.5, desc:"Build anything you can imagine." },
  { id:"g4", name:"Dragon Quest",      players:567,  thumbnail:"🐉", genre:"RPG",      rating:4.3, desc:"Embark on an epic dragon-slaying adventure." },
  { id:"g5", name:"Zombie Defense",    players:2109, thumbnail:"🧟", genre:"Survival", rating:4.6, desc:"Defend your base from endless zombie waves." },
  { id:"g6", name:"Apex Parkour",      players:890,  thumbnail:"🏃", genre:"Parkour",  rating:4.4, desc:"Free-run through impossible obstacle courses." },
];

/* ═══════════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════════ */

const hasProfanity = (text) => {
  const n = text.toLowerCase().replace(/[_\*\.\-\s0-9]/g,"");
  return PROFANITY.some(w => n.includes(w.replace(/[_\*\.\-]/g,"")));
};

const rateLimiter = (() => {
  const store = {};
  return {
    check(key, limit=5, window=60000) {
      const now = Date.now();
      if (!store[key]) store[key] = [];
      store[key] = store[key].filter(t => now - t < window);
      if (store[key].length >= limit) return false;
      store[key].push(now); return true;
    }
  };
})();

const sanitize = (s) => s.replace(/[<>'"`;\\]/g,"").trim();

const fmt = (n) => {
  if (n >= 999999999) return "∞";
  if (n >= 1e6) return (n/1e6).toFixed(1)+"M";
  if (n >= 1e3) return (n/1e3).toFixed(1)+"K";
  return n.toString();
};

const creatorRevenue = (price) => Math.round(price * (1 - PLATFORM_TAX));

/* ═══════════════════════════════════════════════════════════
   STYLES
═══════════════════════════════════════════════════════════ */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg0:#030811;--bg1:#080f1e;--bg2:#0e1628;--bg3:#121d32;--bg4:#1a2540;
  --b1:#1e2d4a;--b2:#2d4270;--b3:#3a5590;
  --cyan:#00d4ff;--cyan2:#00a8cc;--purple:#7c3aed;--purple2:#5b21b6;
  --amber:#f59e0b;--green:#10b981;--red:#ef4444;--pink:#ec4899;
  --txt1:#e8f0fe;--txt2:#8b9dc3;--txt3:#4a5a7a;
  --gold:#fbbf24;--admin:#00ffff;--vblue:#1d9bf0;
  --ff:'Exo 2',sans-serif;--fm:'JetBrains Mono',monospace;
  --r:8px;--rl:14px;
}
body{background:var(--bg0);color:var(--txt1);font-family:var(--ff);overflow:hidden}
#root{height:100vh;overflow:hidden}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg0)}
::-webkit-scrollbar-thumb{background:var(--b2);border-radius:3px}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:9px 18px;border-radius:var(--r);border:none;cursor:pointer;font-family:var(--ff);font-weight:600;font-size:13px;transition:all .18s ease;white-space:nowrap}
.btn-primary{background:linear-gradient(135deg,var(--cyan) 0%,var(--purple) 100%);color:#fff;box-shadow:0 0 20px rgba(0,212,255,.2)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 0 30px rgba(0,212,255,.4)}
.btn-secondary{background:transparent;color:var(--cyan);border:1px solid var(--cyan)}
.btn-secondary:hover{background:rgba(0,212,255,.1)}
.btn-danger{background:var(--red);color:#fff}
.btn-danger:hover{background:#dc2626}
.btn-ghost{background:var(--bg3);color:var(--txt2);border:1px solid var(--b1)}
.btn-ghost:hover{border-color:var(--b2);color:var(--txt1)}
.btn-sm{padding:6px 12px;font-size:12px}
.btn:disabled{opacity:.45;cursor:not-allowed;transform:none!important}
.btn-amber{background:rgba(245,158,11,.15);color:var(--amber);border:1px solid rgba(245,158,11,.3)}
.btn-amber:hover{background:rgba(245,158,11,.25)}
.btn-green{background:rgba(16,185,129,.15);color:var(--green);border:1px solid rgba(16,185,129,.3)}
.btn-green:hover{background:rgba(16,185,129,.25)}

/* INPUTS */
.inp{width:100%;padding:11px 14px;background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);color:var(--txt1);font-family:var(--ff);font-size:13px;transition:all .18s;outline:none}
.inp:focus{border-color:var(--cyan);box-shadow:0 0 0 3px rgba(0,212,255,.1)}
.inp::placeholder{color:var(--txt3)}
.inp.err{border-color:var(--red)!important;box-shadow:0 0 0 3px rgba(239,68,68,.1)}

/* AUTH */
.auth-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;background:var(--bg0);background-image:radial-gradient(ellipse at 25% 45%,rgba(124,58,237,.12) 0%,transparent 55%),radial-gradient(ellipse at 75% 55%,rgba(0,212,255,.08) 0%,transparent 55%)}
.auth-card{width:100%;max-width:410px;background:var(--bg1);border:1px solid var(--b2);border-radius:18px;padding:38px;box-shadow:0 24px 64px rgba(0,0,0,.55),0 0 0 1px rgba(0,212,255,.04),inset 0 1px 0 rgba(255,255,255,.03)}
.auth-logo{font-size:26px;font-weight:900;letter-spacing:-1px;text-align:center;margin-bottom:6px;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.auth-sub{text-align:center;color:var(--txt2);font-size:12px;margin-bottom:28px;letter-spacing:.3px}
.auth-form{display:flex;flex-direction:column;gap:14px}
.fg{display:flex;flex-direction:column;gap:5px}
.fl{font-size:12px;font-weight:600;color:var(--txt2);letter-spacing:.4px;text-transform:uppercase}
.err-txt{color:var(--red);font-size:12px;font-weight:500;margin-top:2px}
.ok-txt{color:var(--green);font-size:12px;font-weight:500}
.auth-ft{text-align:center;margin-top:18px;font-size:12px;color:var(--txt2)}
.alink{color:var(--cyan);cursor:pointer;font-weight:600}
.alink:hover{text-decoration:underline}

/* DASHBOARD LAYOUT */
.dash{display:flex;height:100vh;overflow:hidden}

/* SIDEBAR */
.sidebar{width:210px;flex-shrink:0;background:var(--bg1);border-right:1px solid var(--b1);display:flex;flex-direction:column;overflow:hidden}
.sb-logo{padding:18px 16px 14px;font-size:18px;font-weight:900;letter-spacing:-.5px;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent;border-bottom:1px solid var(--b1);flex-shrink:0}
.sb-avatar{padding:14px 12px;display:flex;flex-direction:column;align-items:center;gap:7px;border-bottom:1px solid var(--b1);flex-shrink:0}
.av-circle{width:54px;height:54px;background:linear-gradient(135deg,var(--purple),var(--cyan));border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;box-shadow:0 0 18px rgba(124,58,237,.4)}
.av-name{font-size:13px;font-weight:700;display:flex;align-items:center;gap:4px}
.av-bobux{font-size:11px;color:var(--gold);font-family:var(--fm);font-weight:700}
.sb-nav{padding:10px 8px;flex:1;overflow-y:auto}
.ni{display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:var(--r);cursor:pointer;color:var(--txt2);font-size:13px;font-weight:500;transition:all .14s;margin-bottom:1px;border:none;background:transparent;width:100%;text-align:left}
.ni:hover{background:var(--bg4);color:var(--txt1)}
.ni.act{background:rgba(0,212,255,.1);color:var(--cyan);border-left:2px solid var(--cyan);padding-left:8px}
.ni-ico{font-size:15px;width:18px;text-align:center;flex-shrink:0}

/* MAIN */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* HEADER */
.hdr{height:52px;flex-shrink:0;background:var(--bg1);border-bottom:1px solid var(--b1);display:flex;align-items:center;justify-content:space-between;padding:0 18px;gap:14px;position:relative}
.srch-wrap{display:flex;align-items:center;background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);overflow:hidden;flex:1;max-width:440px;transition:border-color .18s}
.srch-wrap:focus-within{border-color:var(--b2)}
.srch-tog{display:flex;flex-shrink:0}
.stbtn{padding:8px 12px;font-size:11px;font-weight:700;cursor:pointer;border:none;font-family:var(--ff);transition:all .14s;letter-spacing:.3px}
.stbtn.on{background:var(--cyan);color:#000}
.stbtn:not(.on){background:transparent;color:var(--txt3)}
.srch-inp{flex:1;padding:8px 10px;background:transparent;border:none;color:var(--txt1);font-family:var(--ff);font-size:12px;outline:none}
.srch-inp::placeholder{color:var(--txt3)}
.hdr-r{display:flex;align-items:center;gap:10px}
.bobux-pill{display:flex;align-items:center;gap:5px;background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.25);border-radius:var(--r);padding:5px 11px;font-family:var(--fm);font-size:12px;font-weight:700;color:var(--gold);cursor:default}
.notif-btn{width:32px;height:32px;background:var(--bg3);border:1px solid var(--b1);border-radius:var(--r);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;transition:all .14s;color:var(--txt2)}
.notif-btn:hover{background:var(--bg4);color:var(--txt1)}

/* SEARCH DROPDOWN */
.srch-drop{position:absolute;top:52px;left:18px;right:18px;background:var(--bg1);border:1px solid var(--b2);border-top:none;border-radius:0 0 var(--r) var(--r);z-index:100;max-height:280px;overflow-y:auto;box-shadow:0 12px 32px rgba(0,0,0,.5)}
.sr-item{display:flex;align-items:center;gap:10px;padding:10px 16px;cursor:pointer;border-bottom:1px solid var(--b1);transition:background .12s;font-size:13px}
.sr-item:hover{background:var(--bg4)}
.sr-item:last-child{border-bottom:none}

/* CONTENT AREA */
.cont{flex:1;overflow-y:auto;padding:18px}

/* SECTION */
.sec-title{font-size:16px;font-weight:800;color:var(--txt1);margin-bottom:14px;display:flex;align-items:center;gap:8px;letter-spacing:-.3px}

/* FRIEND ACTIVITY */
.fa-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:10px;margin-bottom:22px}
.fc{background:var(--bg2);border:1px solid var(--b1);border-radius:var(--rl);padding:12px;display:flex;align-items:center;gap:9px;cursor:pointer;transition:all .15s}
.fc:hover{border-color:var(--b2);background:var(--bg4);transform:translateY(-1px)}
.fc-av{font-size:22px;flex-shrink:0}
.fc-inf{flex:1;min-width:0}
.fc-name{font-size:12px;font-weight:700;display:flex;align-items:center;gap:3px}
.fc-game{font-size:10px;color:var(--txt3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.dot-on{width:7px;height:7px;background:var(--green);border-radius:50%;flex-shrink:0}
.dot-off{width:7px;height:7px;background:var(--txt3);border-radius:50%;flex-shrink:0}

/* GAMES GRID */
.games-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
.gc{background:var(--bg2);border:1px solid var(--b1);border-radius:var(--rl);overflow:hidden;cursor:pointer;transition:all .18s}
.gc:hover{border-color:var(--cyan);transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,212,255,.1)}
.gc-thumb{height:96px;background:linear-gradient(135deg,var(--bg4),var(--b1));display:flex;align-items:center;justify-content:center;font-size:38px}
.gc-info{padding:10px}
.gc-name{font-size:12px;font-weight:700;margin-bottom:3px}
.gc-meta{font-size:10px;color:var(--txt3);display:flex;justify-content:space-between}

/* MARKETPLACE */
.mkt-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:12px}
.ic{background:var(--bg2);border:1px solid var(--b1);border-radius:var(--rl);overflow:hidden;cursor:pointer;transition:all .18s}
.ic:hover{border-color:var(--purple);transform:translateY(-2px);box-shadow:0 6px 20px rgba(124,58,237,.15)}
.ic-thumb{height:110px;background:linear-gradient(135deg,rgba(124,58,237,.2),rgba(0,212,255,.1));display:flex;align-items:center;justify-content:center;font-size:44px}
.ic-info{padding:9px}
.ic-name{font-size:11px;font-weight:700;margin-bottom:2px}
.ic-creator{font-size:10px;color:var(--txt3)}
.ic-price{font-size:12px;font-weight:700;color:var(--gold);font-family:var(--fm);margin-top:6px;display:flex;align-items:center;gap:3px}

/* CREATOR */
.cr-hero{text-align:center;padding:36px 20px;background:linear-gradient(135deg,rgba(124,58,237,.1),rgba(0,212,255,.05));border:1px solid var(--b1);border-radius:var(--rl);margin-bottom:20px}
.cr-title{font-size:32px;font-weight:900;letter-spacing:-1px;margin-bottom:8px;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.cr-desc{color:var(--txt2);font-size:14px;max-width:480px;margin:0 auto 20px;line-height:1.6}
.code-box{background:#000;border:1px solid var(--b2);border-radius:var(--r);padding:14px 16px;font-family:var(--fm);font-size:11px;color:#7ee787;overflow-x:auto;white-space:pre;line-height:1.6;margin-top:10px}
.linux-box{background:var(--bg2);border:1px solid var(--b2);border-radius:var(--r);padding:14px;margin-top:12px}
.lbox-title{font-size:12px;font-weight:700;color:var(--amber);margin-bottom:8px;display:flex;align-items:center;gap:5px}

/* TUTORIAL */
.tut-step{background:var(--bg2);border:1px solid var(--b1);border-left:3px solid var(--cyan);border-radius:var(--r);padding:14px 18px;margin-bottom:10px}
.tut-num{font-size:10px;color:var(--cyan);font-weight:700;font-family:var(--fm);margin-bottom:3px;text-transform:uppercase;letter-spacing:.5px}
.tut-title{font-size:14px;font-weight:700;margin-bottom:5px}
.tut-desc{font-size:12px;color:var(--txt2);line-height:1.65}
.vid-ph{background:var(--bg2);border:2px dashed var(--b2);border-radius:var(--rl);height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;color:var(--txt3);margin-bottom:20px;cursor:pointer;transition:all .18s}
.vid-ph:hover{border-color:var(--cyan);color:var(--cyan)}

/* GAME ENGINE */
.game-view{position:relative;width:100%;height:100vh;overflow:hidden;background:#000}
.game-canvas{width:100%;height:100%;display:block;cursor:crosshair}
.game-hud{position:absolute;top:0;left:0;right:0;height:50px;background:rgba(3,8,17,.92);border-bottom:1px solid rgba(30,45,74,.7);display:flex;align-items:center;padding:0 16px;gap:14px;z-index:10;backdrop-filter:blur(4px)}
.hud-player{font-size:13px;font-weight:700;display:flex;align-items:center;gap:6px}
.hud-ctrl{font-size:10px;color:var(--txt3);font-family:var(--fm)}
.chat-wrap{position:absolute;bottom:16px;left:16px;width:300px;z-index:10}
.chat-msgs{height:150px;overflow-y:auto;background:rgba(3,8,17,.85);border:1px solid rgba(30,45,74,.7);border-radius:var(--r) var(--r) 0 0;padding:8px;backdrop-filter:blur(4px)}
.cmsg{font-size:11px;margin-bottom:4px;line-height:1.4}
.cmsg .cu{font-weight:700;color:var(--cyan)}
.cmsg .ca{font-weight:700;color:var(--admin)}
.cmsg .cs{color:var(--amber);font-style:italic}
.chat-row{display:flex;border:1px solid rgba(30,45,74,.7);border-top:none;border-radius:0 0 var(--r) var(--r);overflow:hidden}
.ci{flex:1;padding:7px 9px;background:rgba(3,8,17,.9);border:none;color:var(--txt1);font-family:var(--ff);font-size:11px;outline:none}
.csend{padding:7px 12px;background:var(--cyan);border:none;color:#000;font-weight:700;cursor:pointer;font-size:11px;transition:background .14s}
.csend:hover{background:var(--cyan2)}
.admin-tools{position:absolute;top:60px;right:14px;background:rgba(3,8,17,.92);border:1px solid rgba(0,255,255,.25);border-radius:var(--r);padding:10px 14px;z-index:10;min-width:170px;backdrop-filter:blur(4px)}
.at-title{color:var(--admin);font-size:11px;font-weight:700;margin-bottom:7px;display:flex;align-items:center;gap:5px;letter-spacing:.5px}
.at-row{font-size:11px;color:var(--txt2);margin-bottom:4px;display:flex;align-items:center;gap:5px}
.at-key{background:var(--bg2);color:var(--cyan);padding:1px 5px;border-radius:3px;font-family:var(--fm);font-size:10px}
.fly-on{color:var(--green)!important}

/* MODAL */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.72);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:1000;padding:20px}
.modal{background:var(--bg1);border:1px solid var(--b2);border-radius:var(--rl);padding:26px;max-width:440px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.6);animation:fadeIn .2s ease}
.modal-title{font-size:16px;font-weight:800;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between}
.modal-x{background:none;border:none;color:var(--txt3);cursor:pointer;font-size:18px;line-height:1;transition:color .14s}
.modal-x:hover{color:var(--txt1)}

/* TOAST */
.toast{position:fixed;bottom:18px;right:18px;background:var(--bg1);border:1px solid var(--b2);border-radius:var(--r);padding:11px 18px;font-size:12px;font-weight:600;z-index:2000;animation:fadeIn .25s ease;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.toast.ok{border-color:var(--green);color:var(--green)}
.toast.er{border-color:var(--red);color:var(--red)}
.toast.in{border-color:var(--cyan);color:var(--cyan)}
.toast.wa{border-color:var(--amber);color:var(--amber)}

/* ADMIN TABLE */
.atbl{width:100%;border-collapse:collapse}
.atbl th,.atbl td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--b1);font-size:12px}
.atbl th{color:var(--txt3);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.5px;background:var(--bg2)}
.atbl tr:hover td{background:rgba(26,37,64,.4)}
.banned-row td{opacity:.5}
.badge{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700}
.badge-admin{background:rgba(0,255,255,.1);color:var(--admin);border:1px solid rgba(0,255,255,.2)}
.badge-ver{background:rgba(29,155,240,.1);color:var(--vblue);border:1px solid rgba(29,155,240,.2)}
.badge-ban{background:rgba(239,68,68,.1);color:var(--red);border:1px solid rgba(239,68,68,.2)}
.badge-ok{background:rgba(16,185,129,.1);color:var(--green);border:1px solid rgba(16,185,129,.2)}

/* TABS */
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--b1);margin-bottom:18px}
.tab{padding:9px 14px;cursor:pointer;font-size:12px;font-weight:600;color:var(--txt3);border-bottom:2px solid transparent;transition:all .14s;margin-bottom:-1px;letter-spacing:.2px}
.tab.on{color:var(--cyan);border-bottom-color:var(--cyan)}
.tab:hover:not(.on){color:var(--txt1)}

/* MISC */
.row{display:flex;gap:8px;align-items:center}
.flex1{flex:1}
.divider{height:1px;background:var(--b1);margin:14px 0}
.pill{padding:3px 9px;border-radius:20px;font-size:10px;font-weight:700;display:inline-flex;align-items:center;gap:3px}
.pill-cyan{background:rgba(0,212,255,.1);color:var(--cyan);border:1px solid rgba(0,212,255,.2)}
.pill-purple{background:rgba(124,58,237,.1);color:#a78bfa;border:1px solid rgba(124,58,237,.2)}
.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.info-box{background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);padding:12px}
.info-box-label{font-size:10px;color:var(--txt3);font-weight:600;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px}
.info-box-val{font-size:18px;font-weight:800;color:var(--txt1)}
@keyframes fadeIn{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideIn{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.fade-in{animation:fadeIn .3s ease}
.pulse{animation:pulse 2s infinite}
`;

/* ═══════════════════════════════════════════════════════════
   TINY COMPONENTS
═══════════════════════════════════════════════════════════ */
const VBadge = ({isAdmin}) => (
  <span title={isAdmin?"Administrator":"Verified"} style={{color:isAdmin?"#00ffff":"#1d9bf0",fontSize:"13px",lineHeight:1}}>
    {isAdmin?"🔷":"✓"}
  </span>
);

const BobuxIcon = () => <span style={{color:"#fbbf24"}}>◈</span>;

function Toast({msg,type,clear}){
  useEffect(()=>{const t=setTimeout(clear,3200);return()=>clearTimeout(t)},[]);
  return <div className={`toast ${type}`}>{msg}</div>;
}

/* ═══════════════════════════════════════════════════════════
   AUTH VIEWS
═══════════════════════════════════════════════════════════ */
function LoginView({onLogin,nav}){
  const [u,setU]=useState("");const [p,setP]=useState("");const [err,setErr]=useState("");const [ld,setLd]=useState(false);
  const go=()=>{
    if(!rateLimiter.check("login",5)){setErr("Too many attempts. Wait 1 minute.");return;}
    setLd(true);
    setTimeout(()=>{const r=onLogin(sanitize(u),p);if(r.err)setErr(r.err);setLd(false);},380);
  };
  return(
    <div className="auth-wrap">
      <div className="auth-card fade-in">
        <div className="auth-logo">⬡ ApexStudio</div>
        <div className="auth-sub">The next-generation game platform</div>
        <div className="auth-form">
          <div className="fg"><label className="fl">Username</label>
            <input className={`inp${err?" err":""}`} placeholder="Your username" value={u} onChange={e=>{setU(e.target.value);setErr("");}} onKeyDown={e=>e.key==="Enter"&&go()}/>
          </div>
          <div className="fg"><label className="fl">Password</label>
            <input className={`inp${err?" err":""}`} type="password" placeholder="Your password" value={p} onChange={e=>{setP(e.target.value);setErr("");}} onKeyDown={e=>e.key==="Enter"&&go()}/>
          </div>
          {err&&<div className="err-txt">⚠ {err}</div>}
          <button className="btn btn-primary" style={{width:"100%",padding:"12px"}} onClick={go} disabled={ld}>{ld?"Signing in…":"Sign In"}</button>
          <div style={{textAlign:"center"}}><span className="alink" onClick={()=>nav("forgot")}>Forgot Password?</span></div>
        </div>
        <div className="auth-ft">No account? <span className="alink" onClick={()=>nav("register")}>Create one</span></div>
      </div>
    </div>
  );
}

function RegisterView({onRegister,nav,users}){
  const [f,setF]=useState({username:"",email:"",password:"",confirm:""});
  const [errs,setErrs]=useState({});const [ld,setLd]=useState(false);
  const set=(k,v)=>{setF(prev=>({...prev,[k]:v}));setErrs(prev=>({...prev,[k]:"",global:""}));};
  const validate=()=>{
    const e={};
    if(!f.username)e.username="Username required";
    else if(f.username.length<3)e.username="At least 3 characters";
    else if(hasProfanity(f.username))e.username="Username contains prohibited words";
    else if(users.find(u=>u.username.toLowerCase()===f.username.toLowerCase()))e.username="Username taken";
    if(!f.email||!f.email.includes("@"))e.email="Valid email required";
    if(!f.password||f.password.length<6)e.password="At least 6 characters";
    if(f.password!==f.confirm)e.confirm="Passwords do not match";
    return e;
  };
  const go=()=>{
    if(!rateLimiter.check("register",3)){setErrs({global:"Too many attempts."});return;}
    const e=validate();if(Object.keys(e).length){setErrs(e);return;}
    setLd(true);setTimeout(()=>{const r=onRegister(sanitize(f.username),f.email,f.password);if(r.err)setErrs({global:r.err});setLd(false);},480);
  };
  return(
    <div className="auth-wrap">
      <div className="auth-card fade-in">
        <div className="auth-logo">⬡ ApexStudio</div>
        <div className="auth-sub">Create your account</div>
        <div className="auth-form">
          {[["username","Username","text","Choose a username"],["email","Email","email","your@email.com"],["password","Password","password","Min. 6 characters"],["confirm","Confirm Password","password","Repeat password"]].map(([k,label,type,ph])=>(
            <div className="fg" key={k}>
              <label className="fl">{label}</label>
              <input className={`inp${errs[k]?" err":""}`} type={type} placeholder={ph} value={f[k]} onChange={e=>set(k,e.target.value)} onKeyDown={e=>e.key==="Enter"&&go()}/>
              {errs[k]&&<div className="err-txt" style={k==="username"&&errs[k]==="Username taken"?{color:"var(--red)",fontWeight:700}:{}}>{errs[k]==="Username taken"?"⚠ Username taken":("⚠ "+errs[k])}</div>}
            </div>
          ))}
          {errs.global&&<div className="err-txt">⚠ {errs.global}</div>}
          <button className="btn btn-primary" style={{width:"100%",padding:"12px"}} onClick={go} disabled={ld}>{ld?"Creating…":"Create Account"}</button>
        </div>
        <div className="auth-ft">Already registered? <span className="alink" onClick={()=>nav("login")}>Sign In</span></div>
      </div>
    </div>
  );
}

function ForgotView({nav}){
  const [step,setStep]=useState(1);const [email,setEmail]=useState("");const [np,setNp]=useState("");const [cp,setCp]=useState("");const [err,setErr]=useState("");const [ok,setOk]=useState("");
  const sendLink=()=>{if(!email.includes("@")){setErr("Enter a valid email address");return;}setOk("Verification link sent! Check your inbox.");setTimeout(()=>{setStep(2);setOk("");},1600);};
  const reset=()=>{if(np.length<6){setErr("Password must be at least 6 characters");return;}if(np!==cp){setErr("Passwords do not match");return;}setOk("Password updated successfully!");setTimeout(()=>nav("login"),1500);};
  return(
    <div className="auth-wrap">
      <div className="auth-card fade-in">
        <div className="auth-logo">⬡ ApexStudio</div>
        <div className="auth-sub">{step===1?"Reset your password":"Set a new password"}</div>
        <div className="auth-form">
          {step===1?(
            <>
              <div className="fg"><label className="fl">Email Address</label><input className={`inp${err?" err":""}`} placeholder="your@email.com" value={email} onChange={e=>{setEmail(e.target.value);setErr("");}} onKeyDown={e=>e.key==="Enter"&&sendLink()}/></div>
              {err&&<div className="err-txt">⚠ {err}</div>}
              {ok&&<div className="ok-txt">✓ {ok}</div>}
              <button className="btn btn-primary" style={{width:"100%"}} onClick={sendLink}>Send Verification Link</button>
            </>
          ):(
            <>
              <div className="fg"><label className="fl">New Password</label><input className={`inp${err?" err":""}`} type="password" placeholder="Min. 6 characters" value={np} onChange={e=>{setNp(e.target.value);setErr("");}}/></div>
              <div className="fg"><label className="fl">Confirm New Password</label><input className={`inp${err?" err":""}`} type="password" placeholder="Repeat new password" value={cp} onChange={e=>{setCp(e.target.value);setErr("");}}/></div>
              {err&&<div className="err-txt">⚠ {err}</div>}
              {ok&&<div className="ok-txt">✓ {ok}</div>}
              <button className="btn btn-primary" style={{width:"100%"}} onClick={reset}>Update Password</button>
            </>
          )}
        </div>
        <div className="auth-ft"><span className="alink" onClick={()=>nav("login")}>← Back to Login</span></div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   GAME ENGINE (THREE.JS)
═══════════════════════════════════════════════════════════ */
function GameEngine({user,users,onBan,onExit}){
  const canvasRef=useRef(null);
  const sceneRef=useRef(null);
  const [chat,setChat]=useState([
    {id:0,user:"System",msg:"Welcome to ApexStudio World!",isSystem:true},
    {id:1,user:"CoolGamer99",msg:"Hey everyone! 👋",isAdmin:false},
    {id:2,user:"StarBuilder",msg:"Anyone want to race?",isAdmin:false},
  ]);
  const [chatInput,setChatInput]=useState("");
  const [flying,setFlying]=useState(false);
  const [banHammer,setBanHammer]=useState(false);
  const flyRef=useRef(false);
  const banRef=useRef(false);
  const keys=useRef({});
  const playerRef=useRef(null);
  const npcsRef=useRef([]);
  const frameRef=useRef(null);
  const addMsg=(u,m,sys=false,adm=false)=>setChat(c=>[...c.slice(-30),{id:Date.now(),user:u,msg:m,isSystem:sys,isAdmin:adm}]);

  const sendChat=()=>{
    if(!chatInput.trim())return;
    const txt=chatInput.trim();
    if(hasProfanity(txt)){addMsg("System","⚠ Your message was blocked (prohibited language).",true);setChatInput("");return;}
    if(user.isAdmin&&txt.startsWith("/")){
      if(txt==="/fly"){
        flyRef.current=!flyRef.current;
        setFlying(flyRef.current);
        addMsg("System",`✈ Fly mode ${flyRef.current?"enabled":"disabled"}.`,true);
      } else if(txt.startsWith("/ban ")){
        const target=txt.replace("/ban ","").trim();
        const t=users.find(u2=>u2.username.toLowerCase()===target.toLowerCase());
        if(t){onBan(t.id);addMsg("System",`🔨 ${target} has been banned by admin.`,true);}
        else addMsg("System",`⚠ Player "${target}" not found.`,true);
      } else addMsg("System","⚠ Unknown command.",true);
      setChatInput("");return;
    }
    addMsg(user.username,txt,false,user.isAdmin);
    setChatInput("");
  };

  useEffect(()=>{
    const canvas=canvasRef.current;
    const W=canvas.clientWidth,H=canvas.clientHeight;

    // Scene
    const scene=new THREE.Scene();
    scene.fog=new THREE.FogExp2(0x0a1020,0.025);
    scene.background=new THREE.Color(0x0a1020);

    // Camera
    const cam=new THREE.PerspectiveCamera(70,W/H,0.1,500);
    cam.position.set(0,6,12);

    // Renderer
    const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
    renderer.setSize(W,H);renderer.shadowMap.enabled=true;renderer.setPixelRatio(Math.min(devicePixelRatio,2));

    // Lights
    const ambient=new THREE.AmbientLight(0x334466,1.2);scene.add(ambient);
    const sun=new THREE.DirectionalLight(0x88aaff,1.5);sun.position.set(20,40,20);sun.castShadow=true;scene.add(sun);
    const pt1=new THREE.PointLight(0x00d4ff,2,30);pt1.position.set(0,5,0);scene.add(pt1);
    const pt2=new THREE.PointLight(0x7c3aed,1.5,25);pt2.position.set(-10,4,5);scene.add(pt2);

    // Ground
    const gGeo=new THREE.PlaneGeometry(120,120,30,30);
    const gMat=new THREE.MeshLambertMaterial({color:0x0e1628,wireframe:false});
    const ground=new THREE.Mesh(gGeo,gMat);ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
    const gridHelper=new THREE.GridHelper(120,40,0x1e2d4a,0x1e2d4a);gridHelper.position.y=0.01;scene.add(gridHelper);

    // Decorative blocks
    const colors=[0x7c3aed,0x00d4ff,0xf59e0b,0x10b981];
    for(let i=0;i<20;i++){
      const s=Math.random()*2+0.5;
      const bGeo=new THREE.BoxGeometry(s,s*2,s);
      const bMat=new THREE.MeshLambertMaterial({color:colors[Math.floor(Math.random()*colors.length)],transparent:true,opacity:0.7});
      const b=new THREE.Mesh(bGeo,bMat);b.castShadow=true;
      b.position.set((Math.random()-0.5)*80,(s),( Math.random()-0.5)*80);
      scene.add(b);
    }

    // Player mesh
    const pCol=user.isAdmin?0x00ffff:0x00d4ff;
    const pGeo=new THREE.BoxGeometry(0.8,1.6,0.8);
    const pMat=new THREE.MeshLambertMaterial({color:pCol});
    const player=new THREE.Mesh(pGeo,pMat);
    player.position.set(0,0.8,0);player.castShadow=true;scene.add(player);
    playerRef.current=player;

    // Player head
    const hGeo=new THREE.BoxGeometry(0.7,0.7,0.7);
    const hMat=new THREE.MeshLambertMaterial({color:pCol});
    const head=new THREE.Mesh(hGeo,hMat);head.position.y=1.15;player.add(head);

    // NPC players
    const npcColors=[0xff6b6b,0x4ecdc4,0xffe66d,0xa29bfe];
    const npcNames=["CoolGamer99","StarBuilder","PixelKnight","NeonDrifter"];
    npcsRef.current=npcNames.map((name,i)=>{
      const ng=new THREE.BoxGeometry(0.8,1.6,0.8);
      const nm=new THREE.MeshLambertMaterial({color:npcColors[i]});
      const npc=new THREE.Mesh(ng,nm);
      npc.position.set(-8+i*4,0.8,Math.sin(i)*5-5);scene.add(npc);
      const nh=new THREE.Mesh(new THREE.BoxGeometry(0.7,0.7,0.7),nm);nh.position.y=1.15;npc.add(nh);
      return {mesh:npc,name,t:Math.random()*100};
    });

    // Admin ban hammer
    if(user.isAdmin){
      const hamGeo=new THREE.CylinderGeometry(0.15,0.15,1.2,8);
      const hamMat=new THREE.MeshLambertMaterial({color:0xff4444});
      const hammer=new THREE.Mesh(hamGeo,hamMat);
      const headGeo=new THREE.BoxGeometry(0.5,0.4,0.4);
      const headM=new THREE.MeshLambertMaterial({color:0xcc0000});
      const hamHead=new THREE.Mesh(headGeo,headM);hamHead.position.y=0.8;
      hammer.add(hamHead);hammer.position.set(0.7,0.5,0);hammer.rotation.z=0.5;
      player.add(hammer);
    }

    // Resize handler
    const onResize=()=>{
      const W2=canvas.clientWidth,H2=canvas.clientHeight;
      cam.aspect=W2/H2;cam.updateProjectionMatrix();renderer.setSize(W2,H2);
    };
    window.addEventListener("resize",onResize);

    // Key handlers
    const onDown=e=>keys.current[e.code]=true;
    const onUp=e=>keys.current[e.code]=false;
    window.addEventListener("keydown",onDown);window.addEventListener("keyup",onUp);

    // Animation
    const spd=0.1,rotSpd=0.04;
    let t=0;
    const animate=()=>{
      frameRef.current=requestAnimationFrame(animate);
      t+=0.01;
      const p=playerRef.current;
      if(p){
        if(keys.current["KeyW"])p.position.z-=spd;
        if(keys.current["KeyS"])p.position.z+=spd;
        if(keys.current["KeyA"]){p.position.x-=spd;p.rotation.y=Math.PI/2;}
        else if(keys.current["KeyD"]){p.position.x+=spd;p.rotation.y=-Math.PI/2;}
        else if(keys.current["KeyW"])p.rotation.y=0;
        else if(keys.current["KeyS"])p.rotation.y=Math.PI;
        if(flyRef.current){
          if(keys.current["Space"])p.position.y+=spd;
          if(keys.current["ShiftLeft"])p.position.y-=spd;
          if(p.position.y<0.8)p.position.y=0.8;
        } else {
          p.position.y=0.8;
        }
        // Clamp to ground
        if(!flyRef.current)p.position.y=0.8;
        // Camera follow
        cam.position.x=p.position.x;
        cam.position.y=p.position.y+5.5;
        cam.position.z=p.position.z+11;
        cam.lookAt(p.position.x,p.position.y+0.5,p.position.z);
        // Light follows player
        pt1.position.set(p.position.x,p.position.y+5,p.position.z);
      }
      // Animate NPCs
      npcsRef.current.forEach((n,i)=>{
        n.t+=0.007;
        n.mesh.position.x=Math.sin(n.t*(i+1))*8-4+i*4;
        n.mesh.position.z=Math.cos(n.t*(i*0.7+0.5))*6;
      });
      // Pulse ambient
      pt2.intensity=1.2+Math.sin(t)*0.4;
      renderer.render(scene,cam);
    };
    animate();
    sceneRef.current={renderer,scene,cam};

    return()=>{
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener("resize",onResize);
      window.removeEventListener("keydown",onDown);
      window.removeEventListener("keyup",onUp);
      renderer.dispose();
    };
  },[]);

  const handleBanNearby=()=>{
    if(!user.isAdmin)return;
    // Find nearest NPC within 5 units
    const p=playerRef.current;if(!p)return;
    for(const n of npcsRef.current){
      const dx=p.position.x-n.mesh.position.x;
      const dz=p.position.z-n.mesh.position.z;
      const dist=Math.sqrt(dx*dx+dz*dz);
      if(dist<5){
        const t=users.find(u2=>u2.username===n.name);
        if(t&&!t.banned){
          onBan(t.id);
          addMsg("System",`🔨 ${t.username} was struck by the Ban Hammer!`,true);
          return;
        }
      }
    }
    addMsg("System","⚠ No players nearby to ban.",true);
  };

  return(
    <div className="game-view">
      <canvas ref={canvasRef} className="game-canvas"/>
      <div className="game-hud">
        <button className="btn btn-ghost btn-sm" onClick={onExit}>← Exit</button>
        <div className="hud-player">
          <span>{user.avatar}</span>
          <span style={{color:user.isAdmin?"#00ffff":"var(--cyan)"}}>{user.username}</span>
          {(user.verified||user.isAdmin)&&<VBadge isAdmin={user.isAdmin}/>}
        </div>
        <div className="hud-ctrl">WASD: Move{user.isAdmin&&" · /fly: Toggle fly · /ban [name]: Ban player"}</div>
        <div style={{marginLeft:"auto",display:"flex",gap:"8px",alignItems:"center"}}>
          <div className="bobux-pill"><BobuxIcon/>{fmt(user.bobux)}</div>
        </div>
      </div>
      {user.isAdmin&&(
        <div className="admin-tools">
          <div className="at-title">🔷 Admin Tools</div>
          <div className="at-row"><span className="at-key">/fly</span> Toggle fly mode</div>
          <div className="at-row"><span className="at-key">/ban name</span> Ban a player</div>
          <div className="at-row" onClick={handleBanNearby} style={{cursor:"pointer",color:"var(--red)"}}>
            <span className="at-key">E</span> Ban Hammer nearby
          </div>
          <div className="divider"/>
          <div className="at-row" style={{color:flying?"var(--green)":"var(--txt3)"}}>
            ✈ Fly: {flying?"ON":"OFF"}
          </div>
        </div>
      )}
      <div className="chat-wrap">
        <div className="chat-msgs" id="chat-scroll">
          {chat.map(m=>(
            <div className="cmsg" key={m.id}>
              {m.isSystem?(
                <span className="cs">{m.msg}</span>
              ):(
                <>
                  <span className={m.isAdmin?"ca":"cu"}>{m.user}: </span>
                  <span style={{color:"var(--txt1)"}}>{m.msg}</span>
                </>
              )}
            </div>
          ))}
        </div>
        <div className="chat-row">
          <input className="ci" placeholder="Chat… (Enter to send)" value={chatInput}
            onChange={e=>setChatInput(e.target.value)}
            onKeyDown={e=>e.key==="Enter"&&sendChat()}/>
          <button className="csend" onClick={sendChat}>Send</button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD VIEWS
═══════════════════════════════════════════════════════════ */
function HomeView({user,users,games,onPlayGame,toast}){
  const friends=users.filter(u=>user.friends?.includes(u.id));
  const online=friends.filter(u=>u.currentGame);
  return(
    <div className="fade-in">
      <div className="sec-title">👥 Friend Activity</div>
      <div className="fa-grid">
        {online.length?online.map(f=>(
          <div className="fc" key={f.id} onClick={()=>toast("Joining "+f.username+"'s game…","in")}>
            <span className="fc-av">{f.avatar}</span>
            <div className="fc-inf">
              <div className="fc-name">{f.username}{f.followers>70000&&<VBadge/>}</div>
              <div className="fc-game">🎮 {f.currentGame}</div>
            </div>
            <div className="dot-on"/>
          </div>
        )):(
          <div style={{color:"var(--txt3)",fontSize:"13px",padding:"20px 0",gridColumn:"1/-1"}}>
            No friends are currently playing. Invite them!
          </div>
        )}
        {friends.filter(u=>!u.currentGame).map(f=>(
          <div className="fc" key={f.id}>
            <span className="fc-av">{f.avatar}</span>
            <div className="fc-inf">
              <div className="fc-name">{f.username}{f.followers>70000&&<VBadge/>}</div>
              <div className="fc-game" style={{color:"var(--txt3)"}}>Offline</div>
            </div>
            <div className="dot-off"/>
          </div>
        ))}
      </div>
      <div className="divider"/>
      <div className="sec-title">🔥 Popular Games</div>
      <div className="games-grid">
        {games.map(g=>(
          <div className="gc" key={g.id} onClick={()=>onPlayGame(g)}>
            <div className="gc-thumb">{g.thumbnail}</div>
            <div className="gc-info">
              <div className="gc-name">{g.name}</div>
              <div className="gc-meta">
                <span>👥 {fmt(g.players)}</span>
                <span>⭐ {g.rating}</span>
              </div>
              <div style={{fontSize:"10px",color:"var(--txt3)",marginTop:"4px"}}>{g.genre}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketplaceView({user,items,setItems,setUsers,currentUser,toast}){
  const [tab,setTab]=useState("browse");
  const [form,setForm]=useState({name:"",price:"",category:"Tops",thumbnail:"🎽"});
  const [err,setErr]=useState("");
  const [buyModal,setBuyModal]=useState(null);

  const emojis=["🎽","🧥","👖","🕶️","👢","🎩","🧣","🦺","👗","🥿","💍","🎒"];

  const createItem=()=>{
    if(!form.name.trim()){setErr("Item name required");return;}
    if(hasProfanity(form.name)){setErr("Name contains prohibited words");return;}
    const price=parseInt(form.price);
    if(isNaN(price)||price<1||price>9999){setErr("Price must be 1-9999 Bobux");return;}
    if(currentUser.bobux<10){setErr("Need 10 Bobux to create an item");return;}
    const ni={id:"i"+Date.now(),name:sanitize(form.name),creator:currentUser.username,price,thumbnail:form.thumbnail,sales:0,category:form.category,createdAt:new Date().toISOString().split("T")[0]};
    setItems(prev=>[...prev,ni]);
    setUsers(prev=>prev.map(u=>u.id===currentUser.id?{...u,bobux:u.bobux-10}:u));
    toast("Item listed! Charged 10 Bobux listing fee.","ok");
    setForm({name:"",price:"",category:"Tops",thumbnail:"🎽"});setErr("");
    setTab("browse");
  };

  const buyItem=(item)=>{
    if(item.creator===currentUser.username){toast("You cannot buy your own item.","er");return;}
    if(currentUser.bobux<item.price){toast("Not enough Bobux!","er");return;}
    const revenue=creatorRevenue(item.price);
    const tax=item.price-revenue;
    setUsers(prev=>prev.map(u=>{
      if(u.id===currentUser.id)return{...u,bobux:u.bobux-item.price,inventory:[...(u.inventory||[]),item.id]};
      if(u.username===item.creator)return{...u,bobux:u.bobux+revenue};
      return u;
    }));
    setItems(prev=>prev.map(i=>i.id===item.id?{...i,sales:i.sales+1}:i));
    toast(`Purchased "${item.name}" for ${item.price} ◈. Creator received ${revenue} ◈ (tax: ${tax} ◈).`,"ok");
    setBuyModal(null);
  };

  return(
    <div className="fade-in">
      <div className="sec-title">🛒 Marketplace</div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"16px"}}>
        <div className="tabs" style={{marginBottom:0}}>
          {["browse","create","my-items"].map(t=>(
            <div key={t} className={`tab${tab===t?" on":""}`} onClick={()=>setTab(t)}>
              {t==="browse"?"Browse":t==="create"?"Create Item":"My Items"}
            </div>
          ))}
        </div>
        <div className="bobux-pill"><BobuxIcon/>{fmt(currentUser.bobux)}</div>
      </div>

      {tab==="browse"&&(
        <div className="mkt-grid">
          {items.map(item=>(
            <div className="ic" key={item.id} onClick={()=>setBuyModal(item)}>
              <div className="ic-thumb">{item.thumbnail}</div>
              <div className="ic-info">
                <div className="ic-name">{item.name}</div>
                <div className="ic-creator">by {item.creator}</div>
                <div className="ic-price"><BobuxIcon/>{item.price}</div>
                <div style={{fontSize:"10px",color:"var(--txt3)",marginTop:"2px"}}>{item.sales} sold</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab==="create"&&(
        <div style={{maxWidth:"420px"}}>
          <div className="card" style={{background:"var(--bg2)",border:"1px solid var(--b1)",borderRadius:"var(--rl)",padding:"20px"}}>
            <div style={{fontSize:"14px",fontWeight:700,marginBottom:"14px"}}>List a New Item</div>
            <div style={{background:"rgba(245,158,11,.08)",border:"1px solid rgba(245,158,11,.2)",borderRadius:"var(--r)",padding:"10px 14px",fontSize:"12px",color:"var(--amber)",marginBottom:"16px"}}>
              📋 Listing fee: <strong>10 Bobux</strong> · Platform takes <strong>30% tax</strong> on each sale
            </div>
            <div className="auth-form">
              <div className="fg"><label className="fl">Item Name</label><input className={`inp${err?" err":""}`} placeholder="e.g. Crimson Hoodie" value={form.name} onChange={e=>{setForm(f=>({...f,name:e.target.value}));setErr("");}}/></div>
              <div className="fg"><label className="fl">Price (Bobux)</label><input className="inp" type="number" min="1" max="9999" placeholder="e.g. 15" value={form.price} onChange={e=>setForm(f=>({...f,price:e.target.value}))}/></div>
              {form.price&&parseInt(form.price)>0&&<div style={{fontSize:"11px",color:"var(--green)"}}>Creator earns: {creatorRevenue(parseInt(form.price)||0)} ◈ per sale</div>}
              <div className="fg"><label className="fl">Category</label>
                <select className="inp" value={form.category} onChange={e=>setForm(f=>({...f,category:e.target.value}))}>
                  {["Tops","Bottoms","Accessories","Footwear","Full Body","Hats"].map(c=><option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="fg"><label className="fl">Thumbnail Emoji</label>
                <div style={{display:"flex",flexWrap:"wrap",gap:"6px",padding:"8px 0"}}>
                  {emojis.map(e=>(
                    <div key={e} onClick={()=>setForm(f=>({...f,thumbnail:e}))} style={{width:"36px",height:"36px",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"20px",cursor:"pointer",borderRadius:"6px",background:form.thumbnail===e?"rgba(0,212,255,.2)":"var(--bg3)",border:form.thumbnail===e?"1px solid var(--cyan)":"1px solid var(--b1)",transition:"all .14s"}}>
                      {e}
                    </div>
                  ))}
                </div>
              </div>
              {err&&<div className="err-txt">⚠ {err}</div>}
              <button className="btn btn-primary" onClick={createItem}>List Item (10 ◈)</button>
            </div>
          </div>
        </div>
      )}

      {tab==="my-items"&&(
        <div>
          <div className="mkt-grid">
            {items.filter(i=>i.creator===currentUser.username).length?
              items.filter(i=>i.creator===currentUser.username).map(i=>(
                <div className="ic" key={i.id}>
                  <div className="ic-thumb">{i.thumbnail}</div>
                  <div className="ic-info">
                    <div className="ic-name">{i.name}</div>
                    <div className="ic-price"><BobuxIcon/>{i.price} <span style={{color:"var(--txt3)",fontSize:"10px",fontFamily:"var(--fm)"}}>(earn {creatorRevenue(i.price)})</span></div>
                    <div style={{fontSize:"10px",color:"var(--txt3)",marginTop:"2px"}}>{i.sales} sold · {i.category}</div>
                  </div>
                </div>
              ))
            :<div style={{color:"var(--txt3)",fontSize:"13px",padding:"20px 0"}}>You haven't listed any items yet. Create one!</div>}
          </div>
        </div>
      )}

      {buyModal&&(
        <div className="modal-bg" onClick={e=>e.target===e.currentTarget&&setBuyModal(null)}>
          <div className="modal">
            <div className="modal-title">
              Purchase Item
              <button className="modal-x" onClick={()=>setBuyModal(null)}>×</button>
            </div>
            <div style={{textAlign:"center",padding:"16px 0"}}>
              <div style={{fontSize:"56px",marginBottom:"10px"}}>{buyModal.thumbnail}</div>
              <div style={{fontSize:"18px",fontWeight:800,marginBottom:"4px"}}>{buyModal.name}</div>
              <div style={{fontSize:"12px",color:"var(--txt2)",marginBottom:"12px"}}>by {buyModal.creator} · {buyModal.sales} sold</div>
              <div style={{fontSize:"28px",fontWeight:900,color:"var(--gold)",fontFamily:"var(--fm)",marginBottom:"6px"}}>◈ {buyModal.price}</div>
              <div style={{fontSize:"11px",color:"var(--txt3)",marginBottom:"20px"}}>Creator receives {creatorRevenue(buyModal.price)} ◈ (30% platform tax)</div>
            </div>
            <div style={{display:"flex",gap:"10px"}}>
              <button className="btn btn-ghost" style={{flex:1}} onClick={()=>setBuyModal(null)}>Cancel</button>
              <button className="btn btn-primary" style={{flex:1}} onClick={()=>buyItem(buyModal)}>Buy Now</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CreatorView({toast}){
  const [downloaded,setDownloaded]=useState(false);
  const handleDownload=()=>{
    setDownloaded(true);
    toast("ApexStudio Engine download starting…","in");
  };
  return(
    <div className="fade-in" style={{maxWidth:"860px"}}>
      <div className="cr-hero">
        <div className="cr-title">ApexStudio Creator</div>
        <div className="cr-desc">Build immersive 3D games and experiences. Deploy instantly to millions of players on the ApexStudio platform.</div>
        <button className="btn btn-primary" style={{padding:"13px 32px",fontSize:"15px"}} onClick={handleDownload}>
          {downloaded?"✓ Downloading…":"⬇ Download ApexStudio Engine"}
        </button>
        {downloaded&&<div className="ok-txt" style={{marginTop:"10px"}}>v2.4.1 — Windows / macOS / Linux</div>}
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px",marginBottom:"20px"}}>
        {[["🎨","Visual Scripting","Build game logic without code using our node-based editor."],
          ["⚡","Real-Time Collaboration","Work with teammates live in the same studio session."],
          ["🌍","Instant Publish","Deploy games to the platform in one click."],
          ["💰","Earn Bobux","Monetize your games and earn real currency."]].map(([icon,title,desc])=>(
          <div key={title} style={{background:"var(--bg2)",border:"1px solid var(--b1)",borderRadius:"var(--rl)",padding:"16px"}}>
            <div style={{fontSize:"24px",marginBottom:"8px"}}>{icon}</div>
            <div style={{fontSize:"13px",fontWeight:700,marginBottom:"4px"}}>{title}</div>
            <div style={{fontSize:"12px",color:"var(--txt2)",lineHeight:1.6}}>{desc}</div>
          </div>
        ))}
      </div>

      <div style={{background:"var(--bg2)",border:"1px solid var(--b1)",borderRadius:"var(--rl)",padding:"18px",marginBottom:"16px"}}>
        <div style={{fontSize:"14px",fontWeight:700,marginBottom:"12px",display:"flex",alignItems:"center",gap:"6px"}}>
          <span>🖥️</span> Studio Interface Preview
        </div>
        <div style={{background:"var(--bg0)",border:"1px solid var(--b2)",borderRadius:"var(--r)",padding:"10px",display:"flex",gap:"8px",height:"160px"}}>
          <div style={{width:"52px",background:"var(--bg1)",borderRadius:"6px",border:"1px solid var(--b1)",display:"flex",flexDirection:"column",gap:"4px",padding:"6px",alignItems:"center"}}>
            {["🔲","🔵","⬡","🌳","💡","📷","🔧"].map(t=>(
              <div key={t} title="Tool" style={{width:"32px",height:"32px",background:"var(--bg2)",borderRadius:"4px",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"14px",cursor:"pointer",transition:"background .14s"}}>{t}</div>
            ))}
          </div>
          <div style={{flex:1,background:"var(--bg3)",borderRadius:"6px",border:"1px solid var(--b1)",display:"flex",alignItems:"center",justifyContent:"center",position:"relative",overflow:"hidden"}}>
            <div style={{position:"absolute",inset:0,backgroundImage:"linear-gradient(rgba(30,45,74,.4) 1px,transparent 1px),linear-gradient(90deg,rgba(30,45,74,.4) 1px,transparent 1px)",backgroundSize:"24px 24px"}}/>
            <div style={{position:"relative",zIndex:1,textAlign:"center"}}>
              <div style={{fontSize:"28px",marginBottom:"6px"}}>🏗️</div>
              <div style={{fontSize:"11px",color:"var(--txt3)"}}>3D Viewport</div>
            </div>
          </div>
          <div style={{width:"140px",background:"var(--bg1)",borderRadius:"6px",border:"1px solid var(--b1)",padding:"8px",overflow:"hidden"}}>
            <div style={{fontSize:"10px",fontWeight:700,color:"var(--txt3)",marginBottom:"6px",textTransform:"uppercase",letterSpacing:".4px"}}>Explorer</div>
            {["🌍 Workspace","  📦 Baseplate","  🏗️ Model","  💡 Lights","  🎥 Camera"].map(i=>(
              <div key={i} style={{fontSize:"10px",color:"var(--txt2)",padding:"2px 0",fontFamily:"var(--fm)"}}>{i}</div>
            ))}
          </div>
        </div>
      </div>

      <div className="linux-box">
        <div className="lbox-title">🐧 Arch Linux Setup Instructions</div>
        <div style={{fontSize:"12px",color:"var(--txt2)",marginBottom:"10px",lineHeight:1.6}}>
          ApexStudio Engine runs on Arch Linux via Wine (for the native client) or natively via our AppImage. Follow these steps:
        </div>
        <div className="code-box">{`# Step 1: Install dependencies
sudo pacman -S --needed wine wine-mono winetricks lib32-mesa lib32-vulkan-icd-loader

# Step 2: Download ApexStudio AppImage (native Linux build)
wget https://releases.apexstudio.gg/latest/ApexStudio-x86_64.AppImage
chmod +x ApexStudio-x86_64.AppImage

# Step 3: Install FUSE for AppImage support
sudo pacman -S fuse2

# Step 4: (Optional) Install via AUR wrapper
yay -S apexstudio-bin

# Step 5: Run the studio
./ApexStudio-x86_64.AppImage

# Alternatively, for Wine-based install:
WINEARCH=win64 WINEPREFIX=~/.wine/apexstudio winecfg
wine ApexStudio-Setup.exe

# Step 6: Enable Vulkan for better 3D performance
sudo pacman -S vulkan-icd-loader vulkan-radeon    # For AMD
sudo pacman -S vulkan-icd-loader nvidia-utils     # For NVIDIA`}</div>
        <div style={{fontSize:"11px",color:"var(--txt3)",marginTop:"8px"}}>
          💡 Tip: For best performance on Arch, use the native AppImage. Enable GameMode with <code style={{color:"var(--cyan)",fontSize:"10px"}}>gamemoded</code> for extra FPS boost.
        </div>
      </div>
    </div>
  );
}

function TutorialView(){
  const steps=[
    ["Getting Started","Create your free ApexStudio account and log in to access the full platform, including games, marketplace, and the creator tools."],
    ["Explore Games","Browse the Games section to find popular experiences. Click any game card to join instantly with your character."],
    ["Customize Your Avatar","Visit the Marketplace to browse thousands of player-created clothing items. Purchase items with Bobux to equip them on your avatar."],
    ["Earn Bobux","Complete in-game challenges, sell items on the Marketplace, or top up via the official store to grow your Bobux balance."],
    ["Create Your First Game","Click the Creator tab and download ApexStudio Engine. Follow the in-app wizard to set up your first game world and start placing objects."],
    ["Publish & Monetize","Once your game is ready, hit Publish from the studio. Add a Bobux entry fee or in-game shop to start earning revenue."],
    ["Build a Following","Share your game link with friends. Players who enjoy your game will follow you — once you hit 70,000 followers you earn a Verified badge!"],
    ["Join the Community","Add friends, join group builds, and collaborate in real-time using the Studio multiplayer feature."],
  ];
  return(
    <div className="fade-in" style={{maxWidth:"720px"}}>
      <div className="sec-title">📖 Getting Started Guide</div>
      <div className="vid-ph">
        <div style={{fontSize:"40px"}}>▶</div>
        <div style={{fontSize:"14px",fontWeight:700}}>Video Guide — Coming Soon</div>
        <div style={{fontSize:"12px"}}>A full walkthrough video will be available here</div>
      </div>
      <div style={{marginBottom:"14px"}}>
        {steps.map(([title,desc],i)=>(
          <div className="tut-step" key={i}>
            <div className="tut-num">Step {String(i+1).padStart(2,"0")}</div>
            <div className="tut-title">{title}</div>
            <div className="tut-desc">{desc}</div>
          </div>
        ))}
      </div>
      <div style={{background:"rgba(0,212,255,.06)",border:"1px solid rgba(0,212,255,.15)",borderRadius:"var(--rl)",padding:"16px",marginTop:"8px"}}>
        <div style={{fontSize:"13px",fontWeight:700,marginBottom:"6px",color:"var(--cyan)"}}>💬 Need Help?</div>
        <div style={{fontSize:"12px",color:"var(--txt2)",lineHeight:1.7}}>
          Join our Discord community, visit the Developer Forums, or read the full documentation at <span style={{color:"var(--cyan)"}}>docs.apexstudio.gg</span>
        </div>
      </div>
    </div>
  );
}

function AdminPanel({users,setUsers,items,toast}){
  const [tab,setTab]=useState("users");
  const ban=(id)=>{setUsers(prev=>prev.map(u=>u.id===id?{...u,banned:true}:u));toast("User banned.","wa");};
  const unban=(id)=>{setUsers(prev=>prev.map(u=>u.id===id?{...u,banned:false}:u));toast("User unbanned.","ok");};
  const verify=(id)=>{setUsers(prev=>prev.map(u=>u.id===id?{...u,verified:true}:u));toast("User verified.","ok");};
  return(
    <div className="fade-in" style={{maxWidth:"900px"}}>
      <div className="sec-title">🔷 Admin Panel</div>
      <div style={{background:"rgba(0,255,255,.05)",border:"1px solid rgba(0,255,255,.15)",borderRadius:"var(--r)",padding:"10px 14px",marginBottom:"16px",fontSize:"12px",color:"var(--admin)"}}>
        ⚠ Admin access — actions are permanent. Rate limiting and SQL injection protection active.
      </div>
      <div className="tabs">
        {["users","items","stats"].map(t=><div key={t} className={`tab${tab===t?" on":""}`} onClick={()=>setTab(t)}>{t==="users"?"Users":t==="items"?"Marketplace":"Platform Stats"}</div>)}
      </div>
      {tab==="users"&&(
        <div style={{overflowX:"auto"}}>
          <table className="atbl">
            <thead><tr><th>User</th><th>Email</th><th>Bobux</th><th>Followers</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              <tr>
                <td><div style={{display:"flex",alignItems:"center",gap:"7px"}}><span>🔷</span><span style={{fontWeight:700}}>apexstudio</span><span className="badge badge-admin">ADMIN</span></div></td>
                <td style={{color:"var(--txt3)"}}>admin@apexstudio.gg</td>
                <td><span className="badge-bobux" style={{color:"var(--gold)",fontFamily:"var(--fm)",fontWeight:700}}>∞</span></td>
                <td>{fmt(999999)}</td>
                <td><span className="badge badge-ok">Active</span></td>
                <td><span style={{fontSize:"11px",color:"var(--txt3)"}}>Protected</span></td>
              </tr>
              {users.map(u=>(
                <tr key={u.id} className={u.banned?"banned-row":""}>
                  <td><div style={{display:"flex",alignItems:"center",gap:"7px"}}><span>{u.avatar}</span><span style={{fontWeight:700}}>{u.username}</span>{u.verified&&<span className="badge badge-ver">✓ VER</span>}</div></td>
                  <td style={{color:"var(--txt3)"}}>{u.email}</td>
                  <td style={{fontFamily:"var(--fm)",color:"var(--gold)"}}>{fmt(u.bobux)}</td>
                  <td>{fmt(u.followers)}</td>
                  <td>{u.banned?<span className="badge badge-ban">Banned</span>:<span className="badge badge-ok">Active</span>}</td>
                  <td style={{display:"flex",gap:"6px",flexWrap:"wrap"}}>
                    {!u.verified&&<button className="btn btn-green btn-sm" onClick={()=>verify(u.id)}>Verify</button>}
                    {u.banned?<button className="btn btn-ghost btn-sm" onClick={()=>unban(u.id)}>Unban</button>:<button className="btn btn-danger btn-sm" onClick={()=>ban(u.id)}>Ban</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {tab==="items"&&(
        <div style={{overflowX:"auto"}}>
          <table className="atbl">
            <thead><tr><th>Item</th><th>Creator</th><th>Price</th><th>Sales</th><th>Category</th><th>Revenue to Platform</th></tr></thead>
            <tbody>
              {items.map(i=>(
                <tr key={i.id}>
                  <td><div style={{display:"flex",alignItems:"center",gap:"7px"}}><span>{i.thumbnail}</span><span style={{fontWeight:700}}>{i.name}</span></div></td>
                  <td style={{color:"var(--txt2)"}}>{i.creator}</td>
                  <td style={{fontFamily:"var(--fm)",color:"var(--gold)"}}>◈ {i.price}</td>
                  <td>{i.sales}</td>
                  <td><span className="pill pill-purple">{i.category}</span></td>
                  <td style={{fontFamily:"var(--fm)",color:"var(--cyan)"}}>◈ {Math.round(i.price*0.3*i.sales)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {tab==="stats"&&(
        <div className="info-grid">
          {[["Total Users",users.length+1],["Active Games",GAMES.length],["Marketplace Items",items.length],["Total Bobux in circulation",fmt(users.reduce((a,u)=>a+u.bobux,0))],["Avg Bobux/user",fmt(Math.round(users.reduce((a,u)=>a+u.bobux,0)/users.length))],["Banned Accounts",users.filter(u=>u.banned).length]].map(([label,val])=>(
            <div className="info-box" key={label}>
              <div className="info-box-label">{label}</div>
              <div className="info-box-val" style={{fontSize:"22px"}}>{val}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   SEARCH
═══════════════════════════════════════════════════════════ */
function SearchBar({users,games,onNavigate}){
  const [query,setQuery]=useState("");const [mode,setMode]=useState("Games");const [show,setShow]=useState(false);
  const results=query.length>1?(mode==="Games"?games.filter(g=>g.name.toLowerCase().includes(query.toLowerCase())):users.filter(u=>u.username.toLowerCase().includes(query.toLowerCase()))).slice(0,6):[];
  return(
    <div style={{position:"relative",flex:1,maxWidth:"440px"}}>
      <div className="srch-wrap">
        <div className="srch-tog">
          {["Games","Players"].map(m=><button key={m} className={`stbtn${mode===m?" on":""}`} onClick={()=>setMode(m)}>{m}</button>)}
        </div>
        <input className="srch-inp" placeholder={`Search ${mode.toLowerCase()}…`} value={query}
          onChange={e=>{setQuery(e.target.value);setShow(true);}} onFocus={()=>setShow(true)} onBlur={()=>setTimeout(()=>setShow(false),200)}/>
      </div>
      {show&&results.length>0&&(
        <div className="srch-drop">
          {results.map(r=>(
            <div className="sr-item" key={r.id} onMouseDown={()=>setQuery("")}>
              <span style={{fontSize:"18px"}}>{r.thumbnail||r.avatar}</span>
              <div style={{flex:1}}>
                <div style={{fontSize:"13px",fontWeight:700,display:"flex",alignItems:"center",gap:"4px"}}>
                  {r.name||r.username}
                  {r.followers>70000&&<VBadge/>}
                  {r.isAdmin&&<VBadge isAdmin/>}
                </div>
                {r.genre&&<div style={{fontSize:"10px",color:"var(--txt3)"}}>{r.genre} · {fmt(r.players)} playing</div>}
                {r.followers!==undefined&&<div style={{fontSize:"10px",color:"var(--txt3)"}}>{fmt(r.followers)} followers</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD SHELL
═══════════════════════════════════════════════════════════ */
function Dashboard({user,users,setUsers,items,setItems,games,onLogout,onEnterGame,onBanUser,toast}){
  const [page,setPage]=useState("home");
  const currentUser=users.find(u=>u.id===user.id)||user;
  const isAdmin=user.isAdmin;

  const navItems=[
    {id:"home",icon:"🏠",label:"Home"},
    {id:"games",icon:"🎮",label:"Games"},
    {id:"marketplace",icon:"🛒",label:"Marketplace"},
    {id:"creator",icon:"🔨",label:"Creator"},
    {id:"tutorial",icon:"📖",label:"Tutorial"},
    ...(isAdmin?[{id:"admin",icon:"🔷",label:"Admin Panel"}]:[]),
  ];

  const addFriend=()=>toast("Friend request sent!","in");
  const openShop=()=>{setPage("marketplace")};

  return(
    <div className="dash">
      <div className="sidebar">
        <div className="sb-logo">⬡ ApexStudio</div>
        <div className="sb-avatar">
          <div className="av-circle">{user.avatar}</div>
          <div className="av-name">
            {user.username}
            {(user.verified||user.isAdmin)&&<VBadge isAdmin={user.isAdmin}/>}
          </div>
          <div className="av-bobux">◈ {fmt(currentUser.bobux)}</div>
          <div style={{display:"flex",gap:"6px",marginTop:"4px"}}>
            <button className="btn btn-ghost btn-sm" onClick={addFriend} title="Add Friend">➕</button>
            <button className="btn btn-ghost btn-sm" onClick={()=>setPage("creator")} title="Create">🔨</button>
            <button className="btn btn-ghost btn-sm" onClick={openShop} title="Shop">🛒</button>
          </div>
        </div>
        <div className="sb-nav">
          {navItems.map(n=>(
            <button key={n.id} className={`ni${page===n.id?" act":""}`} onClick={()=>setPage(n.id)}>
              <span className="ni-ico">{n.icon}</span>{n.label}
            </button>
          ))}
          <div className="divider"/>
          <button className="ni" onClick={onLogout}><span className="ni-ico">🚪</span>Sign Out</button>
        </div>
      </div>

      <div className="main">
        <div className="hdr">
          <SearchBar users={users} games={games}/>
          <div className="hdr-r">
            <div className="bobux-pill"><BobuxIcon/>{fmt(currentUser.bobux)}</div>
            <div className="notif-btn">🔔</div>
            <div className="notif-btn" title={user.username}>{user.avatar}</div>
          </div>
        </div>

        <div className="cont">
          {page==="home"&&<HomeView user={currentUser} users={users} games={games} onPlayGame={(g)=>{toast(`Joining ${g.name}…`,"in");setTimeout(onEnterGame,600);}} toast={toast}/>}
          {page==="games"&&(
            <div className="fade-in">
              <div className="sec-title">🎮 All Games</div>
              <div className="games-grid">
                {games.map(g=>(
                  <div className="gc" key={g.id} onClick={()=>{toast(`Joining ${g.name}…`,"in");setTimeout(onEnterGame,600);}}>
                    <div className="gc-thumb">{g.thumbnail}</div>
                    <div className="gc-info">
                      <div className="gc-name">{g.name}</div>
                      <div style={{fontSize:"11px",color:"var(--txt2)",marginBottom:"4px",lineHeight:1.4}}>{g.desc}</div>
                      <div className="gc-meta"><span>👥 {fmt(g.players)}</span><span>⭐ {g.rating}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {page==="marketplace"&&<MarketplaceView user={user} items={items} setItems={setItems} setUsers={setUsers} currentUser={currentUser} toast={toast}/>}
          {page==="creator"&&<CreatorView toast={toast}/>}
          {page==="tutorial"&&<TutorialView/>}
          {page==="admin"&&isAdmin&&<AdminPanel users={users} setUsers={setUsers} items={items} toast={toast}/>}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   ROOT APP
═══════════════════════════════════════════════════════════ */
export default function ApexStudio(){
  const [view,setView]=useState("login"); // login | register | forgot | dashboard | game
  const [currentUser,setCurrentUser]=useState(null);
  const [users,setUsers]=useState(INIT_USERS);
  const [items,setItems]=useState(INIT_ITEMS);
  const [toasts,setToasts]=useState([]);

  const toast=(msg,type="in")=>setToasts(prev=>[...prev,{id:Date.now(),msg,type}]);
  const removeToast=(id)=>setToasts(prev=>prev.filter(t=>t.id!==id));

  // Sync currentUser with users state
  const syncedUser=currentUser?.isAdmin?currentUser:(users.find(u=>u.id===currentUser?.id)||currentUser);

  const handleLogin=(username,password)=>{
    // Check admin
    if(username===ADMIN_CREDENTIALS.username&&password===ADMIN_CREDENTIALS.password){
      setCurrentUser(ADMIN_CREDENTIALS);setView("dashboard");return{};
    }
    // Check users
    const u=users.find(u2=>u2.username.toLowerCase()===username.toLowerCase());
    if(!u)return{err:"Username not found"};
    if(u.password!==password)return{err:"Incorrect password"};
    if(u.banned)return{err:"Your account has been suspended"};
    setCurrentUser(u);setView("dashboard");return{};
  };

  const handleRegister=(username,email,password)=>{
    if(users.find(u=>u.username.toLowerCase()===username.toLowerCase()))return{err:"Username taken"};
    if(users.find(u=>u.email.toLowerCase()===email.toLowerCase()))return{err:"Email already registered"};
    const nu={id:"u"+Date.now(),username,email,password,bobux:50,verified:false,isAdmin:false,avatar:"🧑",followers:0,friends:[],banned:false,currentGame:null,inventory:[]};
    setUsers(prev=>[...prev,nu]);setCurrentUser(nu);setView("dashboard");return{};
  };

  const handleBan=(userId)=>{
    setUsers(prev=>prev.map(u=>u.id===userId?{...u,banned:true}:u));
    toast("Player banned from the platform.","wa");
  };

  const handleLogout=()=>{setCurrentUser(null);setView("login");};

  return(
    <>
      <style>{CSS}</style>
      <div id="apex-root">
        {view==="login"&&<LoginView onLogin={handleLogin} nav={setView}/>}
        {view==="register"&&<RegisterView onRegister={handleRegister} nav={setView} users={users}/>}
        {view==="forgot"&&<ForgotView nav={setView}/>}
        {view==="dashboard"&&syncedUser&&(
          <Dashboard
            user={syncedUser} users={users} setUsers={setUsers}
            items={items} setItems={setItems} games={GAMES}
            onLogout={handleLogout} onEnterGame={()=>setView("game")}
            onBanUser={handleBan} toast={toast}
          />
        )}
        {view==="game"&&syncedUser&&(
          <GameEngine user={syncedUser} users={users} onBan={handleBan} onExit={()=>setView("dashboard")}/>
        )}
        {toasts.map(t=><Toast key={t.id} msg={t.msg} type={t.type} clear={()=>removeToast(t.id)}/>)}
      </div>
    </>
  );
}
