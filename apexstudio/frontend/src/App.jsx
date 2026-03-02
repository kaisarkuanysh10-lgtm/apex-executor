import { useState, useEffect, useRef } from "react";

// ── Constants ──────────────────────────────────────────────
const TAX_RATE = 0.30;
const VERIFY_THRESHOLD = 70000;
const PROFANITY_LIST = ["fuck","f_ck","fu_ck","shit","sh_t","nigger","nigga","faggot","bitch","cunt","asshole","bastard","dick","pussy","whore","slut"];

function hasProfanity(text) {
    const clean = text.toLowerCase().replace(/[^a-z0-9]/g, "");
    return PROFANITY_LIST.some(w => clean.includes(w.replace(/[^a-z]/g, "")));
}

// ── Mock Database ──────────────────────────────────────────
const DB = {
    users: {
        apexstudio: {
            username: "apexstudio", email: "admin@apexstudio.gg",
            password: "apexstudio_key4014VIP148643",
            bobux: Infinity, badge: true, followers: 1000000, banned: false, avatar: "#f59e0b"
        }
    },
    items: [
        { id:1, name:"Neon Jacket", emoji:"🧥", price:15, creator:"apexstudio" },
        { id:2, name:"Galaxy Cap",  emoji:"🧢", price:7,  creator:"apexstudio" },
        { id:3, name:"Storm Shoes", emoji:"👟", price:10, creator:"apexstudio" },
    ],
    games: [
        { id:1, name:"Neon Racers",     players:1423, thumb:"🏎️", creator:"apexstudio" },
        { id:2, name:"Zombie Survival", players:892,  thumb:"🧟", creator:"apexstudio" },
        { id:3, name:"Sky Battle",      players:567,  thumb:"✈️", creator:"apexstudio" },
        { id:4, name:"Lava Escape",     players:1105, thumb:"🌋", creator:"apexstudio" },
        { id:5, name:"Treasure Hunt",   players:234,  thumb:"🗺️", creator:"apexstudio" },
    ],
    friends: [
        { username:"BuilderX",  avatar:"#22c55e", followers:12000,  playing:"Neon Racers" },
        { username:"GamerPro",  avatar:"#3b82f6", followers:85000,  playing:"Zombie Survival" },
        { username:"PixelKing", avatar:"#a855f7", followers:142000, playing:"Sky Battle" },
        { username:"Creator99", avatar:"#ef4444", followers:500,    playing:"Lava Escape" },
    ],
    resets: {}
};

function register(username, email, password) {
    if (DB.users[username]) return { error: "Username taken" };
    if (hasProfanity(username)) return { error: "Username contains inappropriate language" };
    if (username.length < 3) return { error: "Username must be at least 3 characters" };
    const colors = ["#7c3aed","#3b82f6","#22c55e","#ef4444","#06b6d4","#f59e0b"];
    DB.users[username] = {
        username, email, password, bobux: 100,
        badge: false, followers: 0, banned: false,
        avatar: colors[Math.floor(Math.random() * colors.length)]
    };
    return { success: true };
}

function login(username, password) {
    const u = DB.users[username];
    if (!u || u.password !== password) return { error: "Invalid username or password" };
    if (u.banned) return { error: "This account has been permanently banned." };
    return { success: true, user: { ...u } };
}

// ── CSS ────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#0a0a0f;color:#e2e8f0;overflow:hidden}
:root{
    --bg:#0a0a0f;--bg2:#111118;--card:#16161f;--hov:#1e1e2a;
    --ac:#7c3aed;--al:#a855f7;--glow:rgba(124,58,237,.35);
    --gold:#f59e0b;--red:#ef4444;--green:#22c55e;--blue:#3b82f6;
    --t1:#e2e8f0;--t2:#94a3b8;--t3:#64748b;--bd:#1e2028;--r:12px;--rs:8px;
}
button{cursor:pointer;font-family:'Inter',sans-serif;transition:all .18s}
input{font-family:'Inter',sans-serif}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:#2d2d3a;border-radius:2px}
/* AUTH */
.abg{min-height:100vh;background:radial-gradient(ellipse at 20% 50%,rgba(124,58,237,.15) 0%,transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(168,85,247,.1) 0%,transparent 50%),#0a0a0f;display:flex;align-items:center;justify-content:center;padding:20px}
.acard{background:rgba(22,22,31,.97);border:1px solid var(--bd);border-radius:22px;padding:42px;width:100%;max-width:400px;box-shadow:0 25px 80px rgba(0,0,0,.5)}
.logo{font-size:24px;font-weight:900;background:linear-gradient(135deg,#a855f7,#7c3aed,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center}
.logosub{color:var(--t3);font-size:11px;text-align:center;margin-top:3px;margin-bottom:26px}
.ah{font-size:19px;font-weight:700;margin-bottom:5px}
.as{color:var(--t2);font-size:13px;margin-bottom:24px}
.fg{margin-bottom:14px}
.fl{display:block;font-size:11px;font-weight:500;color:var(--t2);margin-bottom:5px}
.fi{width:100%;padding:11px 13px;background:#0d0d14;border:1.5px solid var(--bd);border-radius:var(--rs);color:var(--t1);font-size:13px;outline:none;transition:all .2s}
.fi:focus{border-color:var(--ac);box-shadow:0 0 0 3px var(--glow)}
.fi::placeholder{color:var(--t3)}
.bp{width:100%;padding:12px;background:linear-gradient(135deg,var(--ac),var(--al));border:none;border-radius:var(--rs);color:#fff;font-size:14px;font-weight:600}
.bp:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 8px 20px var(--glow)}
.bp:disabled{opacity:.5;cursor:not-allowed}
.err{color:var(--red);font-size:11px;margin-top:4px}
.sw{text-align:center;margin-top:18px;font-size:12px;color:var(--t2)}
.sw span{color:var(--al);cursor:pointer;font-weight:500}
.sw span:hover{text-decoration:underline}
.succ{color:var(--green);font-size:12px;margin-top:4px}
/* DASH */
.dash{display:flex;height:100vh;overflow:hidden}
.sb{width:64px;background:var(--bg2);border-right:1px solid var(--bd);display:flex;flex-direction:column;align-items:center;padding:12px 0;gap:5px;flex-shrink:0}
.sbav{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;cursor:pointer;border:2px solid transparent;transition:all .2s;margin-bottom:4px}
.sbav:hover{border-color:var(--ac)}
.sbdiv{width:26px;height:1px;background:var(--bd);margin:3px 0}
.sbbtn{width:42px;height:42px;border-radius:var(--rs);background:transparent;border:none;color:var(--t2);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:9px}
.sbbtn:hover{background:var(--hov);color:var(--t1)}
.sbbtn.on{background:rgba(124,58,237,.2);color:var(--al)}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.hdr{height:54px;background:var(--bg2);border-bottom:1px solid var(--bd);display:flex;align-items:center;padding:0 14px;gap:10px;flex-shrink:0}
.hlogo{font-size:15px;font-weight:800;background:linear-gradient(135deg,#a855f7,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}
.sw2{display:flex;background:#0d0d14;border:1.5px solid var(--bd);border-radius:var(--rs);overflow:hidden;flex-shrink:0}
.stab{padding:5px 11px;font-size:10px;font-weight:500;color:var(--t3);background:transparent;border:none;cursor:pointer}
.stab.on{background:var(--ac);color:#fff}
.sinput{background:#0d0d14;border:1.5px solid var(--bd);border-radius:var(--rs);padding:6px 11px;color:var(--t1);font-size:12px;outline:none;width:100%;min-width:0}
.sinput:focus{border-color:var(--ac)}
.srwrap{flex:1;max-width:420px;position:relative}
.srow{display:flex;align-items:center;gap:7px}
.sres{position:absolute;top:100%;left:0;right:0;background:var(--card);border:1px solid var(--bd);border-radius:var(--rs);margin-top:3px;z-index:100;max-height:220px;overflow-y:auto}
.sri{padding:8px 11px;cursor:pointer;display:flex;align-items:center;gap:8px;font-size:12px}
.sri:hover{background:var(--hov)}
.bbx{display:flex;align-items:center;gap:5px;background:#0d0d14;border:1px solid var(--bd);border-radius:var(--rs);padding:6px 11px;margin-left:auto;white-space:nowrap}
.bamt{font-weight:700;font-size:12px;color:var(--gold)}
.blbl{font-size:9px;color:var(--t3)}
.scroll{flex:1;overflow-y:auto;padding:18px}
.stitle{font-size:16px;font-weight:700;margin-bottom:12px;display:flex;align-items:center;gap:7px}
.pill{font-size:10px;background:rgba(124,58,237,.2);color:var(--al);padding:2px 7px;border-radius:20px}
/* GAMES */
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:24px}
.gc{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);overflow:hidden;cursor:pointer;transition:all .22s}
.gc:hover{border-color:var(--ac);transform:translateY(-2px);box-shadow:0 8px 24px rgba(124,58,237,.18)}
.gth{height:100px;display:flex;align-items:center;justify-content:center;font-size:40px;background:linear-gradient(135deg,#1a1a2e,#16213e)}
.gi{padding:9px}
.gn{font-size:11px;font-weight:600;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gpl{font-size:10px;color:var(--t3);display:flex;align-items:center;gap:3px}
.odot{width:5px;height:5px;border-radius:50%;background:var(--green);flex-shrink:0}
/* FRIENDS */
.fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:9px;margin-bottom:24px}
.fc{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);padding:11px;display:flex;align-items:center;gap:9px;transition:all .18s}
.fc:hover{background:var(--hov)}
.fav{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0}
.fn{font-size:12px;font-weight:600;display:flex;align-items:center;gap:4px}
.fs{font-size:10px;color:var(--t3);margin-top:1px}
/* SHOP */
.shopg{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.si{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);overflow:hidden;transition:all .22s}
.si:hover{border-color:var(--ac);transform:translateY(-2px)}
.sith{height:80px;display:flex;align-items:center;justify-content:center;font-size:32px;background:linear-gradient(135deg,#1a1a2e,#16213e)}
.sii{padding:9px}
.sin{font-size:11px;font-weight:600;margin-bottom:3px}
.sic{font-size:9px;color:var(--t3);margin-bottom:5px}
.sip{font-size:12px;font-weight:700;color:var(--gold)}
.sie{font-size:9px;color:var(--green);margin-bottom:5px}
.buybtn{width:100%;padding:5px;background:rgba(124,58,237,.2);border:1px solid rgba(124,58,237,.3);border-radius:5px;color:var(--al);font-size:10px;font-weight:600}
.buybtn:hover{background:var(--ac);color:#fff}
/* MODAL */
.ov{position:fixed;inset:0;background:rgba(0,0,0,.8);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:1000;padding:16px}
.modal{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:26px;width:100%;max-width:420px}
.mt{font-size:17px;font-weight:700;margin-bottom:5px}
.ms{font-size:12px;color:var(--t2);margin-bottom:18px}
.mc{float:right;background:none;border:none;color:var(--t3);font-size:17px;cursor:pointer}
.mc:hover{color:var(--t1)}
.crow{display:flex;justify-content:space-between;align-items:center;background:#0d0d14;border:1px solid var(--bd);border-radius:var(--rs);padding:9px 12px;margin-bottom:12px}
.cv{font-size:14px;font-weight:700;color:var(--gold)}
/* STUDIO */
.studio{display:flex;flex-direction:column;align-items:center;text-align:center;padding:16px}
.sh{font-size:36px;font-weight:900;background:linear-gradient(135deg,#a855f7,#7c3aed,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}
.ss{font-size:15px;color:var(--t2);max-width:520px;margin:0 auto 22px}
.dlbtn{background:linear-gradient(135deg,var(--ac),var(--al));border:none;border-radius:var(--r);padding:13px 32px;color:#fff;font-size:14px;font-weight:700;display:inline-flex;align-items:center;gap:7px}
.dlbtn:hover{transform:translateY(-2px);box-shadow:0 10px 30px var(--glow)}
.tc{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:20px;text-align:left;margin-top:18px;width:100%;max-width:640px}
.tstep{display:flex;gap:9px;margin-bottom:11px}
.snum{width:24px;height:24px;border-radius:50%;background:rgba(124,58,237,.2);border:1px solid var(--ac);color:var(--al);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0}
.stit{font-size:12px;font-weight:600;margin-bottom:2px}
.sdesc{font-size:11px;color:var(--t2);line-height:1.5}
.codeblock{background:#0d0d14;border:1px solid var(--bd);border-radius:7px;padding:9px 12px;font-family:monospace;font-size:10px;color:#a5f3fc;margin:7px 0;overflow-x:auto;white-space:pre}
.vplace{background:linear-gradient(135deg,#1a1a2e,#16213e);border:2px dashed var(--bd);border-radius:var(--r);height:160px;display:flex;align-items:center;justify-content:center;margin-top:10px;color:var(--t3);font-size:12px;gap:7px}
/* PROFILE */
.pban{height:130px;background:linear-gradient(135deg,#1a0533,#0a0f2e,#051525);border-radius:var(--r);position:relative;margin-bottom:48px}
.pav{position:absolute;bottom:-40px;left:18px;width:80px;height:80px;border-radius:50%;border:3px solid var(--bg);display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:700}
.pun{font-size:20px;font-weight:700;display:flex;align-items:center;gap:7px;margin-bottom:6px}
.pst{display:flex;gap:18px;margin-bottom:10px}
.psv{font-size:17px;font-weight:700}
.psl{font-size:10px;color:var(--t3)}
/* ADMIN */
.adminbar{background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);border-radius:var(--r);padding:12px 16px;margin-bottom:18px;display:flex;align-items:center;gap:9px}
.infobar{background:rgba(124,58,237,.07);border:1px solid rgba(124,58,237,.2);border-radius:var(--rs);padding:9px 13px;margin-bottom:14px;font-size:11px;color:var(--t2)}
/* GAME VIEW */
.gview{position:fixed;inset:0;z-index:500;background:#000;overflow:hidden}
.gcanvas{width:100%;height:100%;display:block}
.ghud{position:absolute;top:0;left:0;right:0;padding:12px;display:flex;justify-content:space-between;pointer-events:none}
.hbtn{pointer-events:all;background:rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.15);border-radius:7px;color:#fff;padding:6px 12px;font-size:11px;cursor:pointer;backdrop-filter:blur(8px)}
.hbtn:hover{background:rgba(124,58,237,.4)}
.gctrl{position:absolute;bottom:82px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.08);border-radius:7px;padding:6px 12px;font-size:10px;color:rgba(255,255,255,.45);backdrop-filter:blur(8px);pointer-events:none;white-space:nowrap}
.chatbox{position:absolute;bottom:12px;left:12px;width:280px}
.chatmsgs{background:rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.09);border-radius:7px 7px 0 0;padding:7px;height:130px;overflow-y:auto;backdrop-filter:blur(8px)}
.cm{font-size:10px;margin-bottom:2px;line-height:1.4}
.cmu{color:#a855f7;font-weight:600}
.cms{color:#64748b;font-style:italic}
.cinrow{display:flex}
.cin{flex:1;background:rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.12);border-top:none;border-radius:0 0 0 7px;padding:6px 9px;color:#fff;font-size:11px;outline:none}
.csend{background:var(--ac);border:none;border-radius:0 0 7px 0;padding:6px 10px;color:#fff;font-size:11px;cursor:pointer}
.at{position:absolute;top:56px;right:12px;background:rgba(0,0,0,.75);border:1px solid rgba(245,158,11,.3);border-radius:7px;padding:9px;backdrop-filter:blur(8px);min-width:150px}
.att{font-size:9px;color:var(--gold);font-weight:600;margin-bottom:5px;text-transform:uppercase;letter-spacing:.4px}
.abtn{display:block;width:100%;padding:5px 9px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:5px;color:var(--gold);font-size:10px;margin-bottom:4px;cursor:pointer;text-align:left}
.abtn:hover{background:rgba(245,158,11,.22)}
.abtn.on{background:rgba(245,158,11,.28);border-color:var(--gold)}
/* TOAST */
.toast{position:fixed;top:14px;right:14px;z-index:2000;background:var(--card);border:1px solid var(--bd);border-radius:var(--rs);padding:10px 14px;min-width:200px;box-shadow:0 8px 28px rgba(0,0,0,.4);animation:slin .22s ease;font-size:12px}
.toast.error{border-color:var(--red);background:rgba(239,68,68,.07)}
.toast.success{border-color:var(--green);background:rgba(34,197,94,.07)}
@keyframes slin{from{transform:translateX(110%);opacity:0}to{transform:translateX(0);opacity:1}}
.empty{text-align:center;padding:40px 16px;color:var(--t3)}
.vb-gold{color:#f59e0b;font-size:11px}
.vb-blue{color:#3b82f6;font-size:11px}
`;

// ── Components ──────────────────────────────────────────────

function Toast({ message, type, onDone }) {
    useEffect(() => { const t = setTimeout(onDone, 3200); return () => clearTimeout(t); }, []);
    return <div className={`toast ${type}`}>{type==="error"?"⚠️":"✅"} {message}</div>;
}

function VBadge({ user: u }) {
    if (!u) return null;
    if (u.badge) return <span className="vb-gold" title="Admin">✓</span>;
    if (u.followers >= VERIFY_THRESHOLD) return <span className="vb-blue" title="Verified">✓</span>;
    return null;
}

// ── Auth ────────────────────────────────────────────────────

function LoginPage({ onLogin, goReg, goForgot }) {
    const [u, setU] = useState(""); const [p, setP] = useState("");
    const [err, setErr] = useState(""); const [loading, setLoading] = useState(false);
    function go() {
        setErr("");
        if (!u||!p) { setErr("Fill in all fields"); return; }
        setLoading(true);
        setTimeout(() => {
            const r = login(u, p);
            r.error ? (setErr(r.error), setLoading(false)) : onLogin(r.user);
        }, 480);
    }
    return <div className="abg"><div className="acard">
    <div className="logo">⚡ ApexStudio</div>
    <div className="logosub">Build. Play. Dominate.</div>
    <div className="ah">Welcome back</div><div className="as">Sign in to your account</div>
    <div className="fg"><label className="fl">Username</label>
    <input className="fi" placeholder="Username" value={u} onChange={e=>setU(e.target.value)} onKeyDown={e=>e.key==="Enter"&&go()} /></div>
    <div className="fg"><label className="fl">Password</label>
    <input className="fi" type="password" placeholder="Password" value={p} onChange={e=>setP(e.target.value)} onKeyDown={e=>e.key==="Enter"&&go()} />
    {err&&<div className="err">⚠ {err}</div>}</div>
    <div style={{textAlign:"right",marginBottom:14}}><span onClick={goForgot} style={{fontSize:11,color:"var(--al)",cursor:"pointer"}}>Forgot password?</span></div>
    <button className="bp" onClick={go} disabled={loading}>{loading?"Signing in...":"Sign In"}</button>
    <div className="sw">No account? <span onClick={goReg}>Create one</span></div>
    </div></div>;
}

function RegisterPage({ onLogin, goLogin }) {
    const [form, setForm] = useState({u:"",e:"",p:"",cp:""});
    const [errs, setErrs] = useState({}); const [loading, setLoading] = useState(false);
    function validate() {
        const e={};
        if (!form.u) e.u="Username required";
        else if(form.u.length<3) e.u="Min 3 characters";
        else if(hasProfanity(form.u)) e.u="Username contains inappropriate language";
        else if(DB.users[form.u]) e.u="Username taken";
        if (!form.e||!form.e.includes("@")) e.e="Valid email required";
        if (form.p.length<6) e.p="Min 6 characters";
        if (form.p!==form.cp) e.cp="Passwords do not match";
        return e;
    }
    function go() {
        const e=validate(); setErrs(e);
        if(Object.keys(e).length) return;
        setLoading(true);
        setTimeout(() => { register(form.u,form.e,form.p); onLogin({...DB.users[form.u]}); }, 560);
    }
    const F=k=>({value:form[k],onChange:e=>{setForm(p=>({...p,[k]:e.target.value}));setErrs(p=>({...p,[k]:""}));}});
    return <div className="abg"><div className="acard">
    <div className="logo">⚡ ApexStudio</div><div className="logosub">Build. Play. Dominate.</div>
    <div className="ah">Create account</div><div className="as">Join millions of creators</div>
    {[["u","Username","text"],["e","Email","email"],["p","Password","password"],["cp","Confirm Password","password"]].map(([k,l,t])=>(
        <div className="fg" key={k}><label className="fl">{l}</label>
        <input className="fi" type={t} placeholder={`Enter ${l.toLowerCase()}`} {...F(k)} onKeyDown={e=>e.key==="Enter"&&go()} />
        {errs[k]&&<div className="err">⚠ {errs[k]}</div>}</div>
    ))}
    <button className="bp" onClick={go} disabled={loading}>{loading?"Creating...":"Create Account"}</button>
    <div className="sw">Have an account? <span onClick={goLogin}>Sign in</span></div>
    </div></div>;
}

function ForgotPage({ goLogin }) {
    const [stage, setStage] = useState("email");
    const [email, setEmail] = useState(""); const [code, setCode] = useState("");
    const [pw, setPw] = useState({n:"",c:""}); const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
    return <div className="abg"><div className="acard">
    <div className="logo">⚡ ApexStudio</div><div className="logosub">Password Recovery</div>
    <div className="ah">Reset Password</div>

    {stage==="email"&&<>
        <div className="as">Enter your email address</div>
        <div className="fg"><label className="fl">Email</label>
        <input className="fi" type="email" placeholder="your@email.com" value={email} onChange={e=>{setEmail(e.target.value);setErr("");}} />
        {err&&<div className="err">⚠ {err}</div>}</div>
        <button className="bp" onClick={()=>{
            if(!email.includes("@")){setErr("Enter a valid email");return;}
            const u=Object.values(DB.users).find(u=>u.email===email);
            if(!u){setErr("No account with that email");return;}
            const token=Math.random().toString(36).slice(2,8).toUpperCase();
            DB.resets[token]=u.username;
            setMsg(`Code sent! (Demo: ${token})`); setStage("code");
        }}>Send Verification Code</button>
        </>}

        {stage==="code"&&<>
            <div style={{color:"var(--green)",fontSize:11,marginBottom:12}}>✅ {msg}</div>
            <div className="fg"><label className="fl">Verification Code</label>
            <input className="fi" placeholder="Enter code" value={code} onChange={e=>{setCode(e.target.value.toUpperCase());setErr("");}} />
            {err&&<div className="err">⚠ {err}</div>}</div>
            <button className="bp" onClick={()=>{
                if(!DB.resets[code]){setErr("Invalid code");return;}
                setStage("reset");
            }}>Verify Code</button>
            </>}

            {stage==="reset"&&<>
                <div className="as">Set your new password</div>
                {[["n","New Password"],["c","Confirm New Password"]].map(([k,l])=>(
                    <div className="fg" key={k}><label className="fl">{l}</label>
                    <input className="fi" type="password" placeholder={l} value={pw[k]} onChange={e=>{setPw(p=>({...p,[k]:e.target.value}));setErr("");}} /></div>
                ))}
                {err&&<div className="err">⚠ {err}</div>}
                <button className="bp" onClick={()=>{
                    if(pw.n.length<6){setErr("Min 6 characters");return;}
                    if(pw.n!==pw.c){setErr("Passwords do not match");return;}
                    DB.users[DB.resets[code]].password=pw.n;
                    delete DB.resets[code]; setStage("done");
                }}>Set New Password</button>
                </>}

                {stage==="done"&&<div style={{textAlign:"center",padding:"18px 0"}}>
                <div style={{fontSize:40,marginBottom:12}}>✅</div>
                <div style={{fontSize:16,fontWeight:600,marginBottom:6}}>Password Updated!</div>
                <div style={{color:"var(--t2)",fontSize:12}}>You can now sign in with your new password.</div>
                </div>}

                <div className="sw" style={{marginTop:16}}><span onClick={goLogin}>← Back to Login</span></div>
                </div></div>;
}

// ── Game Engine ─────────────────────────────────────────────

function GameView({ user, onExit }) {
    const mountRef = useRef(null);
    const keysRef = useRef({}); const flyRef = useRef(false);
    const [flying, setFlying] = useState(false);
    const [hammerOn, setHammerOn] = useState(false);
    const [chat, setChat] = useState([
        {t:"s",m:"Welcome to ApexWorld! WASD to move, Space to jump."},
        {t:"s",m:user.username==="apexstudio"?"Admin tools active — try /fly":"Have fun!"}
    ]);
    const [chatIn, setChatIn] = useState("");
    const chatEndRef = useRef(null);
    useEffect(()=>{ chatEndRef.current?.scrollIntoView({behavior:"smooth"}); },[chat]);

    function addMsg(t,m){ setChat(p=>[...p.slice(-40),{t,m}]); }
    function sendChat(){
        const msg=chatIn.trim(); if(!msg) return; setChatIn("");
        if(hasProfanity(msg)){addMsg("s","⚠️ Message blocked: inappropriate content.");return;}
        if(msg==="/fly"&&user.username==="apexstudio"){
            const n=!flyRef.current; flyRef.current=n; setFlying(n);
            addMsg("s",n?"✈️ Flying enabled.":"🚶 Flying disabled."); return;
        }
        addMsg("u",`${user.username}: ${msg}`);
    }

    useEffect(()=>{
        const canvas=mountRef.current; if(!canvas) return;
        const W=canvas.parentElement.clientWidth, H=canvas.parentElement.clientHeight;
        let raf, renderer;

        function init(THREE){
            const scene=new THREE.Scene();
            scene.background=new THREE.Color(0x080814);
            scene.fog=new THREE.Fog(0x080814,40,120);
            const camera=new THREE.PerspectiveCamera(70,W/H,0.1,500);
            camera.position.set(0,8,14);
            renderer=new THREE.WebGLRenderer({canvas,antialias:true});
            renderer.setSize(W,H); renderer.shadowMap.enabled=true;

            scene.add(new THREE.AmbientLight(0x334466,0.7));
            const sun=new THREE.DirectionalLight(0xffffff,1.2);
            sun.position.set(20,40,15); sun.castShadow=true; scene.add(sun);
            const fill=new THREE.PointLight(0x7c3aed,3,25);
            fill.position.set(-8,4,0); scene.add(fill);

            const gnd=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshLambertMaterial({color:0x151520}));
            gnd.rotation.x=-Math.PI/2; gnd.receiveShadow=true; scene.add(gnd);
            scene.add(new THREE.GridHelper(200,40,0x2d1b69,0x1a1a2e));

            const bc=[0x7c3aed,0x3b82f6,0xa855f7,0x6366f1,0x2563eb];
            for(let i=0;i<22;i++){
                const h=2+Math.random()*9;
                const m=new THREE.Mesh(new THREE.BoxGeometry(1.5+Math.random()*3,h,1.5+Math.random()*3),new THREE.MeshLambertMaterial({color:bc[i%bc.length]}));
                m.position.set((Math.random()-.5)*90,h/2,(Math.random()-.5)*90);
                m.castShadow=true; scene.add(m);
            }

            const sg=new THREE.BufferGeometry(); const sp=[];
            for(let i=0;i<1500;i++) sp.push((Math.random()-.5)*400,Math.random()*180+10,(Math.random()-.5)*400);
            sg.setAttribute("position",new THREE.Float32BufferAttribute(sp,3));
            scene.add(new THREE.Points(sg,new THREE.PointsMaterial({color:0xffffff,size:0.4})));

            const pc=parseInt((user.avatar||"#7c3aed").replace("#",""),16);
            const pg=new THREE.Group();
            const pb=new THREE.Mesh(new THREE.CylinderGeometry(.4,.4,1.4,12),new THREE.MeshLambertMaterial({color:pc}));
            const ph=new THREE.Mesh(new THREE.SphereGeometry(.45,12,12),new THREE.MeshLambertMaterial({color:pc}));
            pb.position.y=.7; ph.position.y=1.6; pg.add(pb,ph); scene.add(pg);

            if(user.username==="apexstudio"){
                const hh=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,1.1,8),new THREE.MeshLambertMaterial({color:0x5c3317}));
                const hhd=new THREE.Mesh(new THREE.BoxGeometry(.5,.35,.25),new THREE.MeshLambertMaterial({color:0xf59e0b}));
                hh.position.set(.65,1,0); hh.rotation.z=Math.PI/3; hhd.position.set(1.05,1.35,0);
                pg.add(hh,hhd);
            }

            const botC=[0x22c55e,0xef4444,0x06b6d4];
            const bots=["Player123","BuilderX","GamerPro"].map((name,i)=>{
                const bg=new THREE.Group();
                [new THREE.CylinderGeometry(.4,.4,1.4,12),new THREE.SphereGeometry(.45,12,12)].forEach((g,j)=>{
                    const m=new THREE.Mesh(g,new THREE.MeshLambertMaterial({color:botC[i]}));
                    m.position.y=j===0?.7:1.6; bg.add(m);
                });
                bg.position.set((i-1)*5+4,0,-6); scene.add(bg); return {m:bg,o:i*1.8};
            });

            const onK=(e,v)=>keysRef.current[e.code]=v;
            window.addEventListener("keydown",e=>onK(e,true));
            window.addEventListener("keyup",e=>onK(e,false));

            let t=0,vy=0;
            function animate(){
                raf=requestAnimationFrame(animate); t+=0.016;
                const k=keysRef.current; const spd=0.13;
                if(k.KeyW||k.ArrowUp)    pg.position.z-=spd;
                if(k.KeyS||k.ArrowDown)  pg.position.z+=spd;
                if(k.KeyA||k.ArrowLeft)  pg.position.x-=spd;
                if(k.KeyD||k.ArrowRight) pg.position.x+=spd;
                if(flyRef.current){
                    if(k.Space)     pg.position.y+=spd;
                    if(k.ShiftLeft) pg.position.y-=spd;
                    pg.position.y=Math.max(0,pg.position.y);
                } else {
                    if(pg.position.y<=0){vy=0;pg.position.y=0;}
                    else{vy-=0.009;pg.position.y=Math.max(0,pg.position.y+vy);}
                    if(k.Space&&pg.position.y===0) vy=0.22;
                }
                bots.forEach(b=>{
                    b.m.position.x+=Math.sin(t+b.o)*.02;
                    b.m.position.z+=Math.cos(t*.8+b.o)*.02;
                });
                camera.position.x+=(pg.position.x-camera.position.x)*.09;
                camera.position.y+=(pg.position.y+8-camera.position.y)*.09;
                camera.position.z+=(pg.position.z+14-camera.position.z)*.09;
                camera.lookAt(pg.position.x,pg.position.y+1,pg.position.z);
                fill.intensity=2+Math.sin(t*2)*.8;
                renderer.render(scene,camera);
            }
            animate();
        }

        if(window.THREE) { init(window.THREE); }
        else {
            const s=document.createElement("script");
            s.src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
            s.onload=()=>init(window.THREE); document.head.appendChild(s);
        }

        return ()=>{ cancelAnimationFrame(raf); if(renderer) renderer.dispose(); };
    },[]);

    return <div className="gview">
    <canvas ref={mountRef} className="gcanvas" />
    <div className="ghud">
    <button className="hbtn" onClick={onExit}>← Exit</button>
    <div style={{background:"rgba(0,0,0,.6)",border:"1px solid rgba(255,255,255,.14)",borderRadius:7,padding:"6px 12px",fontSize:11,color:"#f59e0b",fontWeight:700,backdropFilter:"blur(8px)"}}>
    ⚡ {user.username} {user.badge&&"✓"}
    </div>
    </div>
    {user.username==="apexstudio"&&<div className="at">
        <div className="att">⚙️ Admin</div>
        <button className={`abtn ${flying?"on":""}`} onClick={()=>{
            const n=!flyRef.current; flyRef.current=n; setFlying(n);
            addMsg("s",n?"✈️ Fly on.":"🚶 Fly off.");
        }}>✈️ {flying?"Disable Fly":"Enable Fly"}</button>
        <button className={`abtn ${hammerOn?"on":""}`} onClick={()=>{
            setHammerOn(h=>!h);
            addMsg("s",!hammerOn?"🔨 Ban Hammer equipped! Hit a player to ban.":"🔨 Hammer unequipped.");
        }}>🔨 Ban Hammer</button>
        <button className="abtn" onClick={()=>addMsg("s","📢 Broadcast sent.")}>📢 Broadcast</button>
        </div>}
        <div className="gctrl">WASD Move | Space {flying?"Fly Up":"Jump"}{flying?" | Shift Down":""} | Enter Chat</div>
        <div className="chatbox">
        <div className="chatmsgs">
        {chat.map((c,i)=><div key={i} className="cm">
        {c.t==="s"?<span className="cms">{c.m}</span>:<span><span className="cmu">{c.m.split(":")[0]}:</span>{c.m.slice(c.m.indexOf(":"))}</span>}
        </div>)}
        <div ref={chatEndRef} />
        </div>
        <div className="cinrow">
        <input className="cin" placeholder="Type a message..." value={chatIn}
        onChange={e=>setChatIn(e.target.value)} onKeyDown={e=>e.key==="Enter"&&sendChat()} />
        <button className="csend" onClick={sendChat}>→</button>
        </div>
        </div>
        </div>;
}

// ── Studio Page ─────────────────────────────────────────────

function StudioPage() {
    const [dl, setDl] = useState(false);
    function handleDL(){
        setDl(true);
        const script=`#!/bin/bash
        # ApexStudio Engine Installer — Arch Linux
        echo "Installing ApexStudio..."
        sudo pacman -Syu --noconfirm
        sudo pacman -S --noconfirm nodejs npm python python-pip git base-devel
        npm install -g electron
        pip install fastapi uvicorn sqlalchemy python-jose passlib bcrypt --break-system-packages
        mkdir -p ~/.apexstudio
        cat > /usr/local/bin/apexstudio << 'EOF'
        #!/bin/bash
        electron ~/.apexstudio
        EOF
        sudo chmod +x /usr/local/bin/apexstudio
        mkdir -p ~/.local/share/applications
        cat > ~/.local/share/applications/apexstudio.desktop << 'EOF'
        [Desktop Entry]
        Name=ApexStudio
        Exec=apexstudio
        Type=Application
        Categories=Game;Development;
        EOF
        echo "Done! Run: apexstudio"`;
        const a=Object.assign(document.createElement("a"),{href:URL.createObjectURL(new Blob([script],{type:"text/plain"})),download:"install-apexstudio-arch.sh"});
        a.click();
    }
    const steps=[
        ["Install Engine","Download and run the Arch Linux install script. Installs Node.js, Electron, Python, and FastAPI automatically."],
        ["Open Workspace","Launch ApexStudio. You'll see: Toolbar (left), 3D Viewport (center), Explorer (right), Properties (bottom-right)."],
        ["Insert Parts","Click Insert → Part or Ctrl+I. Use Move (V), Rotate (R), Scale (S). Hold Ctrl to snap to grid."],
        ["Write Scripts","Right-click Part → Insert Script. Lua-like scripting:\npart.Touched:Connect(function(hit)\n  hit.Parent:Destroy()\nend)"],
        ["Test Your Game","Press F5 to playtest locally. F6 to stop. Use Play Solo or multiplayer test modes."],
        ["Publish","File → Publish. Add title, thumbnail, genre. Your game goes live immediately!"],
    ];
    return <div className="studio">
    <div className="sh">ApexStudio Creator</div>
    <div className="ss">Build immersive worlds and share them with millions. The only limit is your imagination.</div>
    <button className="dlbtn" onClick={handleDL}>⬇️ Download Engine (Arch Linux)</button>
    {dl&&<div style={{background:"rgba(34,197,94,.07)",border:"1px solid rgba(34,197,94,.28)",borderRadius:7,padding:"9px 16px",marginTop:12,fontSize:11}}>
    ✅ Downloaded! Run: <code style={{color:"#a5f3fc"}}>bash install-apexstudio-arch.sh</code>
    </div>}
    <div className="tc">
    <div style={{fontSize:14,fontWeight:700,marginBottom:10}}>📹 Video Guide</div>
    <div className="vplace">▶️ Getting Started with ApexStudio <span style={{fontSize:10}}>(Coming Soon)</span></div>
    </div>
    <div className="tc">
    <div style={{fontSize:14,fontWeight:700,marginBottom:14}}>📖 Quick Start Tutorial</div>
    {steps.map(([t,d],i)=><div className="tstep" key={i}>
    <div className="snum">{i+1}</div>
    <div><div className="stit">{t}</div><div className="sdesc">{d}</div></div>
    </div>)}
    <div style={{marginTop:14}}>
    <div style={{fontSize:11,fontWeight:600,color:"#a5f3fc",marginBottom:6}}>🐧 Arch Linux Commands</div>
    <div className="codeblock">{`sudo pacman -S nodejs npm python python-pip git
        pip install fastapi uvicorn --break-system-packages
        bash install-apexstudio-arch.sh
        apexstudio`}</div>
        </div>
        </div>
        </div>;
}

// ── Shop ────────────────────────────────────────────────────

function ShopPage({ user, setUser, showToast }) {
    const [items, setItems] = useState([...DB.items]);
    const [show, setShow] = useState(false);
    const [ni, setNi] = useState({name:"",price:5,emoji:"👕"});
    const emojis=["👕","👖","🧢","👟","🕶️","🎩","👗","🧥","👔","🎒","🧤","🪖"];

    function buy(item){
        if(item.creator===user.username){showToast("Can't buy your own item!","error");return;}
        if(user.bobux<item.price){showToast("Not enough Bobux!","error");return;}
        const tax=Math.floor(item.price*TAX_RATE), earn=item.price-tax;
        const nb=user.bobux===Infinity?Infinity:user.bobux-item.price;
        DB.users[user.username].bobux=nb;
        if(DB.users[item.creator]) DB.users[item.creator].bobux+=earn;
        setUser({...user,bobux:nb});
        showToast(`Bought! Creator earns ${earn}B, platform fee ${tax}B (30%)`, "success");
    }

    function create(){
        if(!ni.name.trim()){showToast("Item needs a name","error");return;}
        if(hasProfanity(ni.name)){showToast("Name contains inappropriate language","error");return;}
        if(user.bobux!==Infinity&&user.bobux<10){showToast("Need 10 Bobux to create","error");return;}
        const item={id:Date.now(),...ni,name:ni.name.trim(),creator:user.username,sales:0};
        DB.items.push(item); setItems([...DB.items]);
        const nb=user.bobux===Infinity?Infinity:user.bobux-10;
        DB.users[user.username].bobux=nb;
        setUser({...user,bobux:nb});
        setShow(false); setNi({name:"",price:5,emoji:"👕"});
        showToast(`"${item.name}" listed for ${item.price}B!`,"success");
    }

    return <div>
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:16}}>
    <div className="stitle">🛍️ Marketplace <span className="pill">{items.length}</span></div>
    <button className="bp" style={{width:"auto",padding:"8px 16px",fontSize:12}} onClick={()=>setShow(true)}>+ Create Item</button>
    </div>
    <div className="infobar">💡 Create for <strong style={{color:"var(--gold)"}}>10 Bobux</strong>. Platform takes <strong style={{color:"var(--red)"}}>30% tax</strong>. You keep 70%.</div>
    {items.length===0
        ?<div className="empty"><div style={{fontSize:36,marginBottom:10}}>🛍️</div><div style={{color:"var(--t2)"}}>No items yet. Be the first!</div></div>
        :<div className="shopg">{items.map(it=><div className="si" key={it.id}>
        <div className="sith">{it.emoji}</div>
        <div className="sii">
        <div className="sin">{it.name}</div>
        <div className="sic">by {it.creator}</div>
        <div className="sip">⚡ {it.price}B</div>
        <div className="sie">Creator: {it.price-Math.floor(it.price*TAX_RATE)}B</div>
        <button className="buybtn" onClick={()=>buy(it)}>Buy Now</button>
        </div>
        </div>)}
        </div>}
        {show&&<div className="ov" onClick={e=>e.target===e.currentTarget&&setShow(false)}>
        <div className="modal">
        <button className="mc" onClick={()=>setShow(false)}>×</button>
        <div className="mt">Create Item</div><div className="ms">List your creation on the marketplace</div>
        <div className="crow"><span style={{fontSize:12,color:"var(--t2)"}}>Creation Fee</span><span className="cv">⚡ 10 Bobux</span></div>
        <div className="fg"><label className="fl">Item Name</label>
        <input className="fi" placeholder="e.g. Neon Jacket" value={ni.name} onChange={e=>setNi(p=>({...p,name:e.target.value}))} /></div>
        <div className="fg"><label className="fl">Price (Bobux)</label>
        <input className="fi" type="number" min="1" max="9999" value={ni.price} onChange={e=>setNi(p=>({...p,price:parseInt(e.target.value)||1}))} />
        <div style={{fontSize:10,color:"var(--t3)",marginTop:4}}>You earn ⚡ {ni.price-Math.floor(ni.price*TAX_RATE)}B per sale</div></div>
        <div className="fg"><label className="fl">Icon</label>
        <div style={{display:"flex",flexWrap:"wrap",gap:5,marginTop:4}}>
        {emojis.map(e=><button key={e} onClick={()=>setNi(p=>({...p,emoji:e}))}
        style={{width:36,height:36,background:ni.emoji===e?"rgba(124,58,237,.3)":"#0d0d14",border:`1.5px solid ${ni.emoji===e?"var(--ac)":"var(--bd)"}`,borderRadius:7,fontSize:17,cursor:"pointer"}}>{e}</button>)}
        </div></div>
        <button className="bp" onClick={create}>Create & List (10 Bobux)</button>
        </div>
        </div>}
        </div>;
}

// ── Dashboard ───────────────────────────────────────────────

const NAV=[
    {key:"home",icon:"🏠",label:"Home"},
{key:"games",icon:"🎮",label:"Games"},
{key:"shop",icon:"🛍️",label:"Shop"},
{key:"studio",icon:"🔨",label:"Create"},
{key:"profile",icon:"👤",label:"Profile"},
];

function Dashboard({ user, setUser, onLogout }) {
    const [tab, setTab] = useState("home");
    const [inGame, setInGame] = useState(false);
    const [toast, setToast] = useState(null);
    const [sm, setSm] = useState("Games"); const [sq, setSq] = useState(""); const [sr, setSr] = useState([]); const [showSr, setShowSr] = useState(false);

    function showToast(msg,type="success"){setToast({msg,type});}
    function search(q){
        setSq(q); if(!q.trim()){setSr([]);return;}
        setSr(sm==="Games"?DB.games.filter(g=>g.name.toLowerCase().includes(q.toLowerCase())):Object.values(DB.users).filter(u=>u.username.toLowerCase().includes(q.toLowerCase())));
    }

    const bs=user.bobux===Infinity?"∞":user.bobux?.toLocaleString();
    if(inGame) return <GameView user={user} onExit={()=>setInGame(false)} />;

    return <div className="dash">
    {toast&&<Toast message={toast.msg} type={toast.type} onDone={()=>setToast(null)} />}
    <div className="sb">
    <div className="sbav" style={{background:user.avatar||"#7c3aed",color:"#fff"}} onClick={()=>setTab("profile")} title="Profile">
    {user.username[0].toUpperCase()}
    </div>
    <div className="sbdiv" />
    {NAV.map(n=><button key={n.key} className={`sbbtn ${tab===n.key?"on":""}`} onClick={()=>setTab(n.key)} title={n.label}>
    <span style={{fontSize:17}}>{n.icon}</span><span>{n.label}</span>
    </button>)}
    <div style={{flex:1}} />
    <button className="sbbtn" onClick={onLogout} style={{color:"var(--red)"}} title="Sign Out">
    <span style={{fontSize:17}}>🚪</span><span>Exit</span>
    </button>
    </div>
    <div className="main">
    <div className="hdr">
    <div className="hlogo">⚡ ApexStudio</div>
    <div className="srwrap">
    <div className="srow">
    <div className="sw2">
    {["Games","Players"].map(m=><button key={m} className={`stab ${sm===m?"on":""}`} onClick={()=>{setSm(m);setSq("");setSr([]); }}>{m}</button>)}
    </div>
    <input className="sinput" placeholder={`Search ${sm}...`} value={sq}
    onChange={e=>search(e.target.value)} onFocus={()=>setShowSr(true)} onBlur={()=>setTimeout(()=>setShowSr(false),160)} />
    </div>
    {showSr&&sr.length>0&&<div className="sres">
        {sr.map((r,i)=><div key={i} className="sri">
        {sm==="Games"
            ?<><span style={{fontSize:16}}>{r.thumb}</span><span>{r.name}</span><span style={{color:"var(--t3)",fontSize:10}}>{r.players} online</span></>
            :<><span style={{width:22,height:22,borderRadius:"50%",background:r.avatar,display:"inline-flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:700,color:"#fff",flexShrink:0}}>{r.username[0].toUpperCase()}</span>
            <span>{r.username}</span><VBadge user={r} />
            <span style={{color:"var(--t3)",fontSize:10}}>{r.followers?.toLocaleString()} followers</span>
            </>}
            </div>)}
            </div>}
            </div>
            <div className="bbx">
            <span style={{fontSize:15}}>⚡</span>
            <div><div className="bamt">{bs}</div><div className="blbl">Bobux</div></div>
            </div>
            </div>
            <div className="scroll">
            {tab==="home"    &&<HomePage    user={user} onPlay={()=>setInGame(true)} />}
            {tab==="games"   &&<GamesPage   onPlay={()=>setInGame(true)} />}
            {tab==="shop"    &&<ShopPage    user={user} setUser={setUser} showToast={showToast} />}
            {tab==="studio"  &&<StudioPage  />}
            {tab==="profile" &&<ProfilePage user={user} />}
            </div>
            </div>
            </div>;
}

function HomePage({ user, onPlay }){
    return <>
    {user.username==="apexstudio"&&<div className="adminbar">
        <span style={{fontSize:20}}>👑</span>
        <div><div style={{fontWeight:700,color:"var(--gold)"}}>Super Admin — apexstudio</div>
        <div style={{fontSize:11,color:"var(--t2)"}}>Infinite Bobux · Admin badge · In-game admin tools active</div></div>
        </div>}
        <div className="stitle">🎮 Featured Games</div>
        <div className="cgrid">
        {DB.games.map(g=><div className="gc" key={g.id} onClick={onPlay}>
        <div className="gth">{g.thumb}</div>
        <div className="gi"><div className="gn">{g.name}</div>
        <div className="gpl"><div className="odot" />{g.players.toLocaleString()} playing</div></div>
        </div>)}
        <div className="gc" style={{display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",gap:6,color:"var(--t3)",minHeight:140}}>
        <span style={{fontSize:26}}>＋</span><span style={{fontSize:10}}>Create Game</span>
        </div>
        </div>
        <div className="stitle">👥 Friend Activity <span className="pill">Online</span></div>
        <div className="fgrid">
        {DB.friends.map(f=><div className="fc" key={f.username}>
        <div className="fav" style={{background:f.avatar,color:"#fff"}}>{f.username[0]}</div>
        <div style={{flex:1,minWidth:0}}>
        <div className="fn">{f.username}{f.followers>=VERIFY_THRESHOLD&&<span className="vb-blue">✓</span>}</div>
        <div className="fs">🎮 {f.playing}</div>
        </div>
        </div>)}
        </div>
        </>;
}

function GamesPage({ onPlay }){
    return <>
    <div className="stitle">🎮 All Games</div>
    <div className="cgrid">
    {DB.games.map(g=><div className="gc" key={g.id} onClick={onPlay}>
    <div className="gth">{g.thumb}</div>
    <div className="gi"><div className="gn">{g.name}</div>
    <div className="gpl"><div className="odot" />{g.players.toLocaleString()} playing</div>
    <div style={{fontSize:9,color:"var(--t3)",marginTop:2}}>by {g.creator}</div></div>
    </div>)}
    </div>
    </>;
}

function ProfilePage({ user }){
    return <>
    <div className="pban"><div className="pav" style={{background:user.avatar||"#7c3aed",color:"#fff"}}>{user.username[0].toUpperCase()}</div></div>
    <div>
    <div className="pun">{user.username}<VBadge user={user} style={{fontSize:18}} /></div>
    <div className="pst">
    {[["Followers",user.followers?.toLocaleString()||"0"],["Following","0"],["Bobux",user.bobux===Infinity?"∞":user.bobux?.toLocaleString()]].map(([l,v])=>(
        <div key={l} className="psv-wrap"><div className="psv">{v}</div><div className="psl">{l}</div></div>
    ))}
    </div>
    <div style={{color:"var(--t2)",fontSize:12}}>{user.username==="apexstudio"?"👑 Platform Administrator":"🎮 ApexStudio Player"}</div>
    </div>
    </>;
}

// ── Root ────────────────────────────────────────────────────

export default function App(){
    const [page, setPage] = useState("login");
    const [user, setUser] = useState(null);
    return <>
    <style>{CSS}</style>
    {!user&&page==="login"    &&<LoginPage    onLogin={u=>setUser(u)} goReg={()=>setPage("register")} goForgot={()=>setPage("forgot")} />}
    {!user&&page==="register" &&<RegisterPage onLogin={u=>setUser(u)} goLogin={()=>setPage("login")} />}
    {!user&&page==="forgot"   &&<ForgotPage   goLogin={()=>setPage("login")} />}
    {user  &&<Dashboard user={user} setUser={setUser} onLogout={()=>{setUser(null);setPage("login");}} />}
    </>;
}
