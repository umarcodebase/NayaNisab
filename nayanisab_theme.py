"""NayaNisab visual system.

A single place for the dark / amber theme, the animation keyframes and the
small HTML component helpers the app renders. Keeping it out of app.py means
the interface can be restyled without touching any analysis logic.
"""

ORANGE = "#FF7A18"
ORANGE_SOFT = "#FFB347"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root{
  --bg:#06060A; --bg-2:#0B0B12; --ink:#F4F4F7; --muted:#8C8CA1;
  --orange:#FF7A18; --orange-soft:#FFB347; --orange-dim:rgba(255,122,24,.16);
  --line:rgba(255,255,255,.08); --card:rgba(255,255,255,.035);
  --red:#FF5A4E; --amber:#FFB020; --green:#26C281;
  --font:'Plus Jakarta Sans',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,'Cascadia Code',monospace;
}

/* ---------- canvas ---------- */
[data-testid="stAppViewContainer"]{background:var(--bg);}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stAppViewContainer"]::before{
  content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(60vw 60vw at 12% -10%, rgba(255,122,24,.16), transparent 60%),
    radial-gradient(50vw 50vw at 92% 8%, rgba(255,179,71,.10), transparent 60%),
    radial-gradient(45vw 45vw at 50% 110%, rgba(255,122,24,.08), transparent 60%);
  animation:drift 22s ease-in-out infinite alternate;
}
[data-testid="stAppViewContainer"]::after{
  content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.35;
  background-image:radial-gradient(rgba(255,255,255,.055) 1px, transparent 1px);
  background-size:26px 26px;
  mask-image:radial-gradient(70% 60% at 50% 0%, #000 0%, transparent 85%);
}
@keyframes drift{
  0%{transform:translate3d(0,0,0) scale(1);}
  50%{transform:translate3d(-1.5%,1.5%,0) scale(1.05);}
  100%{transform:translate3d(1.5%,-1%,0) scale(1.02);}
}
.block-container{max-width:1320px;padding-top:1.4rem;padding-bottom:3.5rem;position:relative;z-index:1;}
html,body,[class*="css"]{font-family:var(--font);color:var(--ink);}
h1,h2,h3,h4,h5{font-family:var(--font);color:var(--ink);letter-spacing:-.02em;}
p,span,li,label{color:var(--ink);}
hr{border-color:var(--line);}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0A0A11 0%,#07070C 100%);border-right:1px solid var(--line);}
[data-testid="stSidebar"] .stCaption,[data-testid="stSidebar"] p{color:var(--muted);}
.side-item{display:flex;gap:10px;align-items:flex-start;padding:7px 0;color:#C9C9D6;font-size:.86rem;}
.side-item i{font-style:normal;color:var(--orange);font-weight:800;font-family:var(--mono);font-size:.74rem;padding-top:2px;}

/* ---------- entrance animations ---------- */
@keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:none;}}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
@keyframes popIn{0%{opacity:0;transform:scale(.94);}60%{transform:scale(1.015);}100%{opacity:1;transform:scale(1);}}
@keyframes sweep{0%{background-position:-220% 0;}100%{background-position:220% 0;}}
@keyframes glowPulse{0%,100%{box-shadow:0 0 0 0 rgba(255,122,24,.30);}50%{box-shadow:0 0 34px 6px rgba(255,122,24,.16);}}
@keyframes scanline{0%{transform:translateX(-100%);}100%{transform:translateX(320%);}}
@keyframes ringIn{from{--deg:0deg;}to{--deg:var(--target);}}
@keyframes barIn{from{width:0;}to{width:var(--w);}}
@keyframes blink{0%,45%{opacity:1;}50%,100%{opacity:0;}}

.anim{animation:fadeUp .7s cubic-bezier(.2,.7,.3,1) both;}
.d1{animation-delay:.05s}.d2{animation-delay:.12s}.d3{animation-delay:.19s}
.d4{animation-delay:.26s}.d5{animation-delay:.33s}.d6{animation-delay:.40s}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:26px;padding:38px 40px 34px;
  background:linear-gradient(145deg,rgba(255,122,24,.10) 0%,rgba(10,10,16,.6) 42%,rgba(6,6,10,.85) 100%);
  animation:fadeUp .8s cubic-bezier(.2,.7,.3,1) both;}
.hero::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(115deg,transparent 35%,rgba(255,255,255,.06) 50%,transparent 65%);
  background-size:220% 100%;animation:sweep 7s linear infinite;}
.hero-code{position:absolute;right:26px;top:22px;font-family:var(--mono);font-size:.66rem;line-height:1.7;color:rgba(255,122,24,.30);text-align:right;user-select:none;}
.eyebrow{display:inline-flex;align-items:center;gap:9px;text-transform:uppercase;letter-spacing:.20em;font-size:.68rem;
  font-weight:800;color:var(--orange);border:1px solid rgba(255,122,24,.32);background:var(--orange-dim);
  padding:6px 13px;border-radius:999px;}
.hero h1{font-size:3.5rem;line-height:1.02;margin:16px 0 10px;font-weight:800;}
.grad{background:linear-gradient(92deg,var(--orange) 0%,var(--orange-soft) 45%,#fff 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;}
.hero-sub{font-size:1.06rem;color:#B9B9CB;max-width:640px;margin:0;}
.hero-sub .w{display:inline-block;animation:fadeUp .5s ease both;}
.caret{display:inline-block;width:9px;height:1.05rem;background:var(--orange);vertical-align:-2px;margin-left:4px;animation:blink 1.1s steps(1) infinite;}

/* ---------- cards ---------- */
.card{position:relative;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:20px 22px;
  transition:transform .25s cubic-bezier(.2,.7,.3,1),border-color .25s,background .25s;overflow:hidden;}
.card::before{content:"";position:absolute;inset:0;opacity:0;transition:opacity .3s;
  background:radial-gradient(420px 180px at 15% 0%,rgba(255,122,24,.13),transparent 70%);}
.card:hover{transform:translateY(-5px);border-color:rgba(255,122,24,.42);background:rgba(255,255,255,.055);}
.card:hover::before{opacity:1;}
.card.lit{border-color:rgba(255,122,24,.55);box-shadow:0 0 42px rgba(255,122,24,.10);}
.num{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;font-family:var(--mono);font-weight:700;
  font-size:.82rem;color:#0A0A0F;background:linear-gradient(140deg,var(--orange),var(--orange-soft));margin-bottom:13px;}
.card h4{margin:0 0 6px;font-size:1.02rem;font-weight:700;overflow-wrap:normal;word-break:normal;hyphens:none;}
.card.eq{min-height:232px;display:flex;flex-direction:column;}
.card.eq p{overflow-wrap:normal;word-break:normal;}
.card p{margin:0;color:var(--muted);font-size:.87rem;line-height:1.55;}
.rule{height:2px;width:34px;border-radius:2px;background:linear-gradient(90deg,var(--orange),transparent);margin:11px 0;}
.accent{color:var(--orange);font-weight:700;}
.small{color:var(--muted);font-size:.84rem;}

/* ---------- score ring ---------- */
@property --deg{syntax:'<angle>';initial-value:0deg;inherits:false;}
.ring-wrap{display:flex;align-items:center;gap:20px;}
.ring{--target:0deg;position:relative;width:118px;height:118px;border-radius:50%;flex:0 0 118px;
  background:conic-gradient(var(--orange) var(--deg),rgba(255,255,255,.07) 0);
  animation:ringIn 1.5s cubic-bezier(.2,.8,.2,1) forwards;}
.ring::after{content:"";position:absolute;inset:9px;border-radius:50%;background:#0A0A11;border:1px solid var(--line);}
.ring b{position:absolute;inset:0;display:grid;place-items:center;z-index:2;font-size:2.05rem;font-weight:800;
  animation:popIn .8s .3s both;}
.ring-label{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:700;}
.ring-big{font-size:1.5rem;font-weight:800;margin-top:2px;}

/* ---------- meters ---------- */
.meter-row{margin:13px 0;}
.meter-top{display:flex;justify-content:space-between;font-size:.86rem;margin-bottom:7px;gap:12px;}
.meter-top b{font-weight:600;}
.meter-top span{font-family:var(--mono);font-size:.8rem;color:var(--muted);}
.meter{height:7px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden;}
.meter i{display:block;height:100%;border-radius:99px;animation:barIn 1.25s cubic-bezier(.2,.8,.2,1) both;}
.m-low i{background:linear-gradient(90deg,#FF5A4E,#FF8A6B);}
.m-mid i{background:linear-gradient(90deg,var(--orange),var(--orange-soft));}
.m-high i{background:linear-gradient(90deg,#1FA971,#37D89A);}

/* ---------- chips & pills ---------- */
.chip{display:inline-block;padding:5px 12px;margin:0 6px 7px 0;border-radius:999px;font-size:.78rem;font-weight:600;
  background:rgba(255,255,255,.05);border:1px solid var(--line);color:#D3D3DE;transition:.2s;}
.chip:hover{border-color:rgba(255,122,24,.5);color:#fff;}
.pill{display:inline-flex;align-items:center;gap:7px;padding:5px 13px;border-radius:999px;font-size:.73rem;
  font-weight:800;letter-spacing:.08em;text-transform:uppercase;}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;}
.p-imm{color:var(--red);background:rgba(255,90,78,.12);border:1px solid rgba(255,90,78,.32);}
.p-man{color:var(--amber);background:rgba(255,176,32,.12);border:1px solid rgba(255,176,32,.32);}
.p-opt{color:var(--green);background:rgba(38,194,129,.12);border:1px solid rgba(38,194,129,.30);}

/* ---------- band banner ---------- */
.band{display:flex;gap:16px;align-items:center;border-radius:18px;padding:17px 22px;border:1px solid var(--line);
  background:var(--card);animation:fadeUp .7s .1s both;}
.band .bar{width:4px;align-self:stretch;border-radius:4px;}
.band b{font-size:1.02rem;letter-spacing:.02em;}
.b-low .bar{background:var(--red);} .b-low b{color:var(--red);}
.b-mid .bar{background:var(--amber);} .b-mid b{color:var(--amber);}
.b-high .bar{background:var(--green);} .b-high b{color:var(--green);}

/* ---------- gap / rec blocks ---------- */
.block{position:relative;border:1px solid var(--line);border-left:3px solid var(--orange);border-radius:14px;
  background:var(--card);padding:15px 18px;margin-bottom:11px;transition:.25s;animation:fadeUp .6s both;}
.block:hover{background:rgba(255,255,255,.055);transform:translateX(4px);}
.block h5{margin:0 0 5px;font-size:.97rem;font-weight:700;}
.block p{margin:0;color:var(--muted);font-size:.87rem;line-height:1.55;}
.timeline{border-left:1px dashed rgba(255,255,255,.16);padding-left:20px;margin-left:8px;}
.tl-item{position:relative;padding-bottom:17px;animation:fadeUp .6s both;}
.tl-item::before{content:"";position:absolute;left:-26px;top:5px;width:11px;height:11px;border-radius:50%;
  background:var(--orange);box-shadow:0 0 0 4px rgba(255,122,24,.16);}
.tl-item b{font-size:.94rem;}
.tl-item .from-to{font-family:var(--mono);font-size:.76rem;color:var(--muted);display:block;margin-top:4px;}

/* ---------- scan loader ---------- */
.scan{position:relative;height:3px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden;margin:6px 0 2px;}
.scan i{position:absolute;inset:0;width:32%;border-radius:99px;
  background:linear-gradient(90deg,transparent,var(--orange),transparent);animation:scanline 1.5s ease-in-out infinite;}

/* ---------- streamlit widgets ---------- */
.stButton > button{border-radius:14px;font-weight:750;border:1px solid var(--line);background:rgba(255,255,255,.05);
  color:var(--ink);padding:.62rem 1.1rem;transition:.22s;}
.stButton > button:hover{border-color:rgba(255,122,24,.55);color:#fff;transform:translateY(-2px);background:rgba(255,255,255,.08);}
.stButton > button[kind="primary"]{background:linear-gradient(120deg,var(--orange),var(--orange-soft));color:#0A0A0F;
  border:none;font-size:1.02rem;padding:.85rem 1.2rem;animation:glowPulse 3.4s ease-in-out infinite;}
.stButton > button[kind="primary"]:hover{filter:brightness(1.07);transform:translateY(-2px);}
[data-testid="stDownloadButton"] button{background:linear-gradient(120deg,var(--orange),var(--orange-soft));color:#0A0A0F;
  border:none;font-weight:800;border-radius:14px;padding:.8rem 1.1rem;}
[data-testid="stDownloadButton"] button:hover{filter:brightness(1.07);transform:translateY(-2px);}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"]{background:rgba(255,255,255,.04)!important;
  border-color:var(--line)!important;border-radius:12px!important;}
.stTextInput input,.stTextArea textarea,[data-testid="stTextInput"] input,[data-baseweb="input"] input,
[data-baseweb="base-input"] input,[data-baseweb="textarea"] textarea{
  background:transparent!important;border:none!important;color:#F4F4F7!important;
  -webkit-text-fill-color:#F4F4F7!important;caret-color:var(--orange);}
.stTextInput input::placeholder,.stTextArea textarea::placeholder,[data-baseweb="input"] input::placeholder{
  color:#6E6E82!important;-webkit-text-fill-color:#6E6E82!important;opacity:1;}
.stTextInput div[data-baseweb="input"]:focus-within,[data-baseweb="base-input"]:focus-within{
  border-color:var(--orange)!important;box-shadow:0 0 0 3px rgba(255,122,24,.14)!important;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.028);border:1.5px dashed rgba(255,255,255,.16);
  border-radius:16px;transition:.25s;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--orange);background:rgba(255,122,24,.05);}
[data-testid="stFileUploaderDropzone"] *{color:var(--muted);}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:11px 11px 0 0;padding:10px 17px;color:var(--muted);font-weight:650;}
.stTabs [aria-selected="true"]{background:rgba(255,122,24,.09);color:var(--orange)!important;box-shadow:inset 0 -2px 0 var(--orange);}
.stTabs [data-baseweb="tab-highlight"]{background:transparent;}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden;}
[data-testid="stExpander"] summary{color:var(--ink);font-weight:650;}
[data-testid="stExpander"] summary:hover{color:var(--orange);}
.stProgress > div > div > div > div{background:linear-gradient(90deg,var(--orange),var(--orange-soft));}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--line);background:var(--card);}
::-webkit-scrollbar{width:9px;height:9px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(255,122,24,.32);border-radius:99px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,122,24,.55);}

/* ---------- footer ---------- */
.foot{margin-top:38px;border-top:1px solid var(--line);padding-top:20px;display:flex;justify-content:space-between;
  flex-wrap:wrap;gap:12px;align-items:center;}
.foot .by{font-size:.92rem;color:#C9C9D6;}
.foot .by b{background:linear-gradient(92deg,var(--orange),var(--orange-soft));-webkit-background-clip:text;
  background-clip:text;color:transparent;font-weight:800;}
.foot .note{font-size:.78rem;color:var(--muted);max-width:620px;}

@media (max-width:900px){
  .hero{padding:28px 22px;} .hero h1{font-size:2.3rem;} .hero-code{display:none;}
  .ring{width:96px;height:96px;flex:0 0 96px;} .ring b{font-size:1.7rem;}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;}
}
</style>
"""
