import streamlit as st
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="HERNANPHY | BIO", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. LIMPIEZA TOTAL DE INTERFAZ
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        header { visibility: hidden; height: 0; }
        footer { visibility: hidden; }
        .block-container { padding: 0rem; }
        [data-testid="stAppViewContainer"] { background-color: #0b1114; overflow: hidden; }
        html, body { overflow: hidden; cursor: none; }
    </style>
""", unsafe_allow_html=True)

<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>HERNANPHY</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
:root{
  --bg:#0b0d10;
  --fg:#e5e7eb;
  --muted:#7a7f87;
  --carbon:#9aa0a6;
}

*{margin:0;padding:0;box-sizing:border-box;}

html,body{
  width:100%;
  height:100%;
  background:var(--bg);
  font-family:"Courier New",monospace;
  overflow:hidden;
  cursor:none;
}

/* CURSOR */
#cursor{
  position:fixed;
  width:14px;
  height:14px;
  border-radius:50%;
  border:1px solid var(--muted);
  pointer-events:none;
  transform:translate(-50%,-50%);
  opacity:.6;
}

/* CORE */
#core{ position:absolute; inset:0; }

/* FRAGMENTOS */
.fragment{
  position:absolute;
  font-size:13px;
  letter-spacing:2px;
  color:var(--muted);
  opacity:0;
  filter:blur(4px);
  white-space:nowrap;
  transition:opacity .6s ease, filter .6s ease;
  user-select:text;
}

.fragment.visible{
  opacity:1;
  filter:blur(0);
}

.fragment.blur{
  filter:blur(4px);
}

.fragment.hidden{
  opacity:0;
}

.fragment.read{
  opacity:0;
  pointer-events:none;
}

/* TEXTO EXPANDIDO */
#expanded{
  position:absolute;
  left:50%;
  top:50%;
  transform:translate(-50%,-50%);
  max-width:560px;
  font-size:14px;
  line-height:1.8;
  color:var(--carbon);
  opacity:0;
  pointer-events:none;
}

/* BRANDING */
#identity{
  position:absolute;
  bottom:36px;
  left:50%;
  transform:translateX(-50%);
  text-align:center;
  opacity:0;
  transition:opacity 1.2s ease;
}

#identity h1{
  font-size:16px;
  letter-spacing:6px;
  font-weight:400;
  color:var(--fg);
}

#identity p{
  margin-top:6px;
  font-size:9px;
  letter-spacing:2px;
  color:var(--muted);
  display:flex;
  justify-content:space-between;
}

/* MENSAJE FINAL */
#finalMessage{
  position:absolute;
  left:50%;
  top:50%;
  transform:translate(-50%,-50%);
  font-size:14px;
  line-height:1.9;
  letter-spacing:1px;
  color:var(--carbon);
  opacity:0;
  white-space:pre-line;
  transition:opacity 2.2s ease, filter 2.2s ease;
}

#finalMessage.fade{
  opacity:0;
  filter:blur(6px);
}
</style>
</head>

<body>

<div id="cursor"></div>
<div id="core"></div>
<div id="expanded"></div>

<div id="identity">
  <h1>HERNAN<span style="color:var(--carbon)">PHY</span></h1>
  <p>
    <span>TECNOLOGÍA</span>
    <span>DISEÑO</span>
    <span>LÓGICA</span>
  </p>
</div>

<div id="finalMessage"></div>

<script>
const core = document.getElementById("core");
const cursor = document.getElementById("cursor");
const expanded = document.getElementById("expanded");
const identity = document.getElementById("identity");
const finalMessage = document.getElementById("finalMessage");

const fragmentsData = [
  {s:"Guadalajara",l:"Nací en Guadalajara, Jalisco. Mi formación académica no fue extensa. Me formé como técnico en informática, programación y diseño."},
  {s:"Autodidacta",l:"Gran parte de mi aprendizaje ha sido autodidacta, impulsado por la curiosidad constante y la necesidad de comprender cómo funcionan las cosas."},
  {s:"HTML",l:"Mis primeros acercamientos a la programación fueron con HTML y herramientas visuales que despertaron mi interés por la interacción."},
  {s:"Flash",l:"Adobe Flash me enseñó narrativa visual, animación y lógica cuando los recursos eran limitados."},
  {s:"Windows Me",l:"Mi primera computadora operaba con Windows Me y una conexión telefónica inestable."},
  {s:"Logística",l:"La logística y los inventarios se convirtieron en un terreno natural para aplicar automatización y análisis."},
  {s:"Python",l:"Python me permitió construir herramientas funcionales enfocadas en datos y procesos."},
  {s:"UX",l:"Mi enfoque integra lógica, diseño y experiencia de usuario como un solo sistema."}
];

let fragments=[];
let readCount=0;
let revealed=false;
let brandingShown=false;
let activeFragment=null;

let lastX=0;
let lastY=0;
let lastTime=Date.now();

function randomPosition(el){
  el.style.left=Math.random()*80+10+"%";
  el.style.top=Math.random()*80+10+"%";
}

function typeText(text,el,callback){
  el.textContent="";
  el.style.opacity=1;
  let i=0;
  const speed=32;
  const timer=setInterval(()=>{
    el.textContent+=text.charAt(i);
    i++;
    if(i>=text.length){
      clearInterval(timer);
      if(callback) callback();
    }
  },speed);
}

function createFragments(){
  fragmentsData.forEach(f=>{
    const el=document.createElement("div");
    el.className="fragment";
    el.textContent=f.s;
    el.dataset.long=f.l;
    el.dataset.read="false";
    randomPosition(el);
    core.appendChild(el);
    fragments.push(el);

    el.addEventListener("mousedown",()=>{
      activeFragment=el;

      fragments.forEach(fr=>{
        if(fr!==el && fr.dataset.read==="false"){
          fr.classList.add("hidden");
        }
      });

      expanded.style.opacity=1;
      typeText(f.l,expanded);
    });

    el.addEventListener("mouseup",()=>{
      if(el.dataset.read==="false"){
        el.dataset.read="true";
        readCount++;
        el.classList.add("read");
      }

      expanded.style.opacity=0;
      activeFragment=null;

      fragments.forEach(fr=>{
        if(fr.dataset.read==="false"){
          fr.classList.remove("hidden");
        }
      });

      if(readCount===fragments.length){
        endSequence();
      }
    });
  });

  fragments.forEach((f,i)=>{
    setTimeout(()=>f.classList.add("visible"),i*80);
  });
}

function endSequence(){
  fragments.forEach(f=>f.style.opacity=0);
  identity.style.opacity=0;
  cursor.style.opacity=0;

  setTimeout(()=>{
    typeText(
`Gracias por tomarte el tiempo de recorrer esta biografía.

Nada aquí fue diseñado para apresurarse,
sino para ser leído con atención y silencio.

Valoro profundamente que hayas llegado hasta el final.
El tiempo que dedicaste es lo más importante.

Gracias.`,
      finalMessage,
      ()=>{
        setTimeout(()=>{
          finalMessage.classList.add("fade");
          setTimeout(()=>{
            document.body.innerHTML="";
            document.body.style.background="var(--bg)";
          },2300);
        },1600);
      }
    );
  },900);
}

document.addEventListener("mousemove",e=>{
  const now=Date.now();
  const dx=e.clientX-lastX;
  const dy=e.clientY-lastY;
  const dt=now-lastTime;

  const speed=Math.sqrt(dx*dx+dy*dy)/dt;

  fragments.forEach(f=>{
    if(speed>0.8){
      f.classList.add("blur");
    }else{
      f.classList.remove("blur");
    }
  });

  lastX=e.clientX;
  lastY=e.clientY;
  lastTime=now;

  cursor.style.left=e.clientX+"px";
  cursor.style.top=e.clientY+"px";

  if(!brandingShown){
    identity.style.opacity=1;
    brandingShown=true;
  }
});

document.addEventListener("click",()=>{
  if(!brandingShown){
    identity.style.opacity=1;
    brandingShown=true;
  }
  if(!revealed){
    revealed=true;
    createFragments();
  }
});
</script>

</body>
</html>
html_de_tu_bio = r"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>HERNANPHY</title>
    </head>
<body>
    </body>
</html>
"""

# 4. RENDERIZADO
# Usamos un height alto para asegurar que cubra todo el viewport
components.html(html_de_tu_bio, height=1200, scrolling=False)
