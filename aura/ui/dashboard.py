# -*- coding: utf-8 -*-
"""
aura/ui/dashboard.py  —  Aura: Escudo Etico · Dashboard completo
Diseño fiel al mockup con datos dinamicos desde SQLite.
Incluye panel de debug como menu separado.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, math, time
from datetime import datetime, date

# ── Colores ───────────────────────────────────────────────
D = {
    "bg":      "#0d0d14", "sidebar": "#111119", "card":   "#16161f",
    "card2":   "#1c1c28", "border":  "#ffffff",
    "accent":  "#7c3aed", "accent2": "#6d28d9", "accentl":"#a855f7",
    "teal":    "#06b6d4", "purple":  "#a855f7",  "pink":   "#ec4899",
    "safe":    "#10b981", "warn":    "#f59e0b",   "danger": "#ef4444",
    "text":    "#f1f5f9", "text2":   "#94a3b8",   "text3":  "#475569",
    "gold":    "#f59e0b",
}

def _lerp(c1, c2, t):
    def h(c): return tuple(int(c.lstrip("#")[i:i+2],16) for i in (0,2,4))
    r1,g1,b1 = h(c1); r2,g2,b2 = h(c2)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

# ── Helpers UI ────────────────────────────────────────────
def _lbl(parent, text, font=("Helvetica",10), fg=None, bg=None, **kw):
    return tk.Label(parent, text=text, font=font,
                    fg=fg or D["text"], bg=bg or D["card"], **kw)

def _sep(parent, bg=None):
    return tk.Frame(parent, bg=bg or D["border"], height=1)

def _card(parent, **kw):
    return tk.Frame(parent, bg=D["card"], **kw)

def _card2(parent, **kw):
    return tk.Frame(parent, bg=D["card2"], **kw)

def _btn(parent, text, cmd, bg=None, fg="white", font=("Helvetica",9,"bold"), padx=16, pady=8):
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg or D["accent"], fg=fg,
                     activebackground=D["accent2"],
                     font=font, relief="flat", bd=0,
                     padx=padx, pady=pady, cursor="hand2")

# ── Logo canvas ───────────────────────────────────────────
class LogoCanvas(tk.Canvas):
    def __init__(self, parent, size=34, bg=D["sidebar"], **kw):
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        s = size
        for i in range(20,0,-1):
            t = i/20; r = int(s/2*t)
            c = _lerp("#7c3aed","#06b6d4",1-t)
            cx,cy = s//2,s//2
            self.create_oval(cx-r,cy-r,cx+r,cy+r,fill=c,outline="")
        sc = s*0.55; ox,oy = s/2-sc/2, s/2-sc*0.52
        pts = [s/2,oy, ox+sc,oy+sc*0.25, ox+sc,oy+sc*0.6,
               s/2,oy+sc, ox,oy+sc*0.6, ox,oy+sc*0.25]
        self.create_polygon(pts,outline="white",fill="",width=2)
        hx,hy,hr = s/2, s/2+s*0.05, s*0.09
        self.create_oval(hx-hr*1.1,hy-hr,hx,hy+hr*0.3,fill="white",outline="")
        self.create_oval(hx,hy-hr,hx+hr*1.1,hy+hr*0.3,fill="white",outline="")
        self.create_polygon([hx-hr*1.1,hy+hr*0.1,hx,hy+hr*1.4,hx+hr*1.1,hy+hr*0.1],fill="white",outline="")

# ── Score ring ────────────────────────────────────────────
class ScoreRing(tk.Canvas):
    def __init__(self, parent, size=200, score=85, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=D["card"], highlightthickness=0, **kw)
        self.size=size; self.target=score; self.current=0
        self._draw(0); self.after(30, self._anim)

    def _anim(self):
        if self.current < self.target:
            self.current = min(self.current+3, self.target)
            self._draw(self.current); self.after(16,self._anim)

    def update_score(self, score):
        self.target=score
        if score < self.current:
            self.current=score; self._draw(score)
        else:
            self.after(30, self._anim)

    def _draw(self, score):
        self.delete("all")
        s=self.size; pad=18
        # Glow ring de fondo
        self.create_arc(pad,pad,s-pad,s-pad,start=90,extent=360,
                        outline=D["card2"],width=14,style="arc")
        # Arco de score con gradiente visual
        ext = -(360*score/100)
        color = D["safe"] if score>=80 else D["warn"] if score>=50 else D["danger"]
        self.create_arc(pad,pad,s-pad,s-pad,start=90,extent=ext,
                        outline=color,width=14,style="arc")
        # Punto final
        if score > 0:
            ang = math.radians(90-abs(ext))
            r = (s-2*pad)/2
            px = s/2+r*math.cos(ang); py = s/2-r*math.sin(ang)
            self.create_oval(px-6,py-6,px+6,py+6,fill=color,outline=D["bg"])
        # Texto
        self.create_text(s//2,s//2-14,text=str(score),
                         font=("Helvetica",34,"bold"),fill=D["text"])
        self.create_text(s//2,s//2+18,text="out of 100",
                         font=("Helvetica",10),fill=D["text3"])
        nivel = ("Excelente" if score>=80 else "Bueno" if score>=60
                 else "En riesgo" if score>=40 else "Critico")
        nc = D["safe"] if score>=80 else D["warn"] if score>=60 else D["danger"]
        self.create_text(s//2,s//2+36,text=nivel,
                         font=("Helvetica",9,"bold"),fill=nc)

# ── Spark bars ────────────────────────────────────────────
class SparkBars(tk.Canvas):
    def __init__(self, parent, data=None, labels=None, **kw):
        super().__init__(parent, height=80, bg=D["card"],
                         highlightthickness=0, **kw)
        self.data=data or []; self.labels=labels or []
        self.bind("<Configure>",self._draw)

    def update_data(self, data, labels=None):
        self.data=data; self.labels=labels or self.labels; self._draw()

    def _draw(self,e=None):
        self.delete("all")
        w=self.winfo_width() or 300; h=self.winfo_height() or 80
        n=len(self.data)
        if not n: return
        mx=max(self.data) or 1
        bw=max(4,(w-(n-1)*6)//n)
        for i,v in enumerate(self.data):
            bh=int((v/mx)*(h-20))
            x0=i*(bw+6); x1=x0+bw; y0=h-bh-2; y1=h-2
            is_last=(i==n-1)
            clr = D["accent"] if is_last else _lerp(D["card2"],D["accentl"],v/mx)
            # Barra redondeada (radio arriba)
            r=min(4,bw//2)
            self.create_rectangle(x0,y0+r,x1,y1,fill=clr,outline="")
            self.create_oval(x0,y0,x0+r*2,y0+r*2,fill=clr,outline="")
            self.create_oval(x1-r*2,y0,x1,y0+r*2,fill=clr,outline="")
            self.create_rectangle(x0+r,y0,x1-r,y0+r,fill=clr,outline="")
            if self.labels and i < len(self.labels):
                self.create_text(x0+bw//2,h-1,text=self.labels[i],
                                 font=("Helvetica",6),fill=D["text3"],anchor="s")

# ══════════════════════════════════════════════════════════
#  POPUP: SCORE CRITICO
# ══════════════════════════════════════════════════════════
class AlertaScoreCritico(tk.Toplevel):
    def __init__(self, parent, score, consecuencias):
        super().__init__(parent)
        self.title(""); self.configure(bg=D["bg"])
        self.resizable(False,False)
        self.attributes("-topmost",True); self.grab_set_global()
        self.focus_force()
        self._ov = tk.Toplevel(parent)
        sw=self._ov.winfo_screenwidth(); sh=self._ov.winfo_screenheight()
        self._ov.geometry(f"{sw}x{sh}+0+0"); self._ov.configure(bg="black")
        self._ov.attributes("-alpha",0.7,"-topmost",True); self._ov.overrideredirect(True)
        self._ov.lower(self)
        self._build(score, consecuencias); self._centrar()

    def _build(self, score, consecuencias):
        outer = tk.Frame(self, bg=D["bg"], padx=32, pady=28)
        outer.pack(fill="both",expand=True)
        # Icono
        ic = tk.Canvas(outer,width=60,height=60,bg=D["bg"],highlightthickness=0)
        ic.pack(pady=(0,14))
        ic.create_oval(2,2,58,58,fill="#2d1515",outline=D["danger"],width=2)
        ic.create_text(30,30,text="!",font=("Helvetica",26,"bold"),fill=D["danger"])
        _lbl(outer,"Reputacion en Zona Critica",
             font=("Helvetica",17,"bold"),fg=D["danger"],bg=D["bg"]).pack()
        _lbl(outer,f"Tu score ha caido a {score}/100",
             font=("Helvetica",10),fg=D["text2"],bg=D["bg"]).pack(pady=(4,16))
        # Consecuencias
        cf = tk.Frame(outer,bg=D["card2"],padx=16,pady=14)
        cf.pack(fill="x",pady=(0,16))
        _lbl(cf,"Consecuencias activas:",
             font=("Helvetica",9,"bold"),fg=D["warn"],bg=D["card2"]).pack(anchor="w")
        for c in consecuencias:
            row=tk.Frame(cf,bg=D["card2"]); row.pack(fill="x",pady=2)
            _lbl(row,"▸",font=("Helvetica",9),fg=D["danger"],bg=D["card2"]).pack(side="left")
            _lbl(row," "+c,font=("Helvetica",9),fg=D["text"],bg=D["card2"],
                 wraplength=320,justify="left").pack(side="left",anchor="w")
        _btn(outer,"Entendido — voy a mejorar",self.destroy,
             bg=D["accent"],pady=10).pack(fill="x")

    def _centrar(self):
        self.update_idletasks()
        w=400; h=self.winfo_reqheight()
        sw=self.winfo_screenwidth(); sh=self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def destroy(self):
        try: self._ov.destroy()
        except: pass
        super().destroy()

# ══════════════════════════════════════════════════════════
#  POPUP: ESPEJO DE EMPATIA
# ══════════════════════════════════════════════════════════
class EspejoEmpatia(tk.Toplevel):
    def __init__(self, parent, texto, severidad, puntos, score_nuevo, on_decision=None):
        super().__init__(parent)
        self.on_decision=on_decision; self._t0=time.time()
        self.title(""); self.configure(bg=D["card"])
        self.resizable(False,False)
        self.attributes("-topmost",True); self.grab_set_global(); self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._reflexionar)
        self.after(50, self._forzar_frente)
        self._ov=tk.Toplevel(parent)
        sw=self._ov.winfo_screenwidth(); sh=self._ov.winfo_screenheight()
        self._ov.geometry(f"{sw}x{sh}+0+0"); self._ov.configure(bg="black")
        self._ov.attributes("-alpha",0.6,"-topmost",True); self._ov.overrideredirect(True)
        self._ov.lower(self)
        self._build(texto, severidad, puntos, score_nuevo); self._centrar()
        # Countdown
        self._countdown = 5
        self._tick()

    def _forzar_frente(self):
        try:
            import ctypes
            hwnd=int(self.wm_frame(),16)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except: pass
        self.focus_force(); self.lift()

    def _build(self, texto, severidad, puntos, score_nuevo):
        # Eye icon header
        hdr=tk.Frame(self,bg=D["card"],pady=20); hdr.pack(fill="x")
        ic=tk.Canvas(hdr,width=48,height=48,bg=D["card"],highlightthickness=0); ic.pack()
        ic.create_oval(2,14,46,34,fill=D["card2"],outline=D["accent"],width=2)
        ic.create_oval(18,18,30,30,fill=D["accent"],outline="")
        ic.create_oval(21,21,27,27,fill="white",outline="")
        _lbl(hdr,"Espejo de Empatia",font=("Helvetica",15,"bold"),bg=D["card"]).pack(pady=(8,2))
        _lbl(hdr,"Aura ha detectado un tono que podria afectar tu relacion.",
             font=("Helvetica",9),fg=D["text2"],bg=D["card"]).pack()

        # Emojis de emocion
        emo_frame=tk.Frame(self,bg=D["card"]); emo_frame.pack(pady=(8,4))
        emojis = [("😔","HURT"), ("—",""), ("😢","SAD")] if severidad=="LEVE" else \
                 [("😠","ANGRY"), ("—",""), ("😭","HURT")] if severidad=="MODERADO" else \
                 [("💔","BROKEN"), ("—",""), ("😰","SCARED")]
        for em,lbl in emojis:
            if em == "—":
                _lbl(emo_frame,"——",font=("Helvetica",12),fg=D["text3"],bg=D["card"]).pack(side="left",padx=4)
            else:
                ef=tk.Frame(emo_frame,bg=D["card"]); ef.pack(side="left",padx=10)
                _lbl(ef,em,font=("Helvetica",24),bg=D["card"]).pack()
                _lbl(ef,lbl,font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["card"]).pack()

        # Texto detectado
        tf=_card2(self,padx=16,pady=12); tf.pack(fill="x",padx=20,pady=(4,8))
        _lbl(tf,'"'+texto[:80]+('"...' if len(texto)>80 else '"'),
             font=("Helvetica",10,"italic"),fg=D["text"],bg=D["card2"],
             wraplength=360,justify="center").pack()

        # Score badge
        sev_color = D["warn"] if severidad=="LEVE" else D["danger"] if severidad=="CRITICO" else D["pink"]
        sb=tk.Frame(self,bg=D["card"]); sb.pack(pady=(0,8))
        tk.Label(sb,text=f"  {severidad}  ",font=("Helvetica",8,"bold"),
                 fg="white",bg=sev_color,padx=6,pady=3).pack(side="left",padx=4)
        tk.Label(sb,text=f"-{puntos} pts  →  Score: {score_nuevo}/100",
                 font=("Helvetica",9,"bold"),fg=D["warn"],bg=D["card"]).pack(side="left")

        _sep(self).pack(fill="x",padx=20)

        # Botones
        bf=tk.Frame(self,bg=D["card"],pady=14,padx=20); bf.pack(fill="x")
        self._btn_reflex=_btn(bf,"  Reflexionar",self._reflexionar,pady=10)
        self._btn_reflex.pack(fill="x",pady=(0,8))
        self._timer_lbl=tk.Label(self._btn_reflex,text="00:05",
                                  font=("Helvetica",9,"bold"),fg=D["accentl"],bg=D["accent"])
        self._timer_lbl.place(relx=1,rely=0.5,anchor="e",x=-10)
        _btn(bf,"Enviar de todos modos",self._continuar,
             bg=D["card2"],fg=D["text2"],font=("Helvetica",9),pady=8).pack(fill="x")
        tk.Label(self,text="CULTIVA CONEXIONES MAS PROFUNDAS",
                 font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["card"]).pack(pady=(0,12))

    def _tick(self):
        if self._countdown > 0:
            mins=self._countdown//60; secs=self._countdown%60
            try: self._timer_lbl.configure(text=f"{mins:02d}:{secs:02d}")
            except: return
            self._countdown -= 1
            self.after(1000, self._tick)
        else:
            try: self._timer_lbl.configure(text="✓ Listo")
            except: pass

    def _centrar(self):
        self.update_idletasks()
        w=420; h=self.winfo_reqheight()
        sw=self.winfo_screenwidth(); sh=self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cerrar_ov(self):
        try: self._ov.destroy()
        except: pass

    def _reflexionar(self):
        ms=int((time.time()-self._t0)*1000)
        self._cerrar_ov()
        if self.on_decision: self.on_decision("editar", ms)
        self.destroy()

    def _continuar(self):
        ms=int((time.time()-self._t0)*1000)
        self._cerrar_ov()
        if self.on_decision: self.on_decision("continuar", ms)
        self.destroy()

# ══════════════════════════════════════════════════════════
#  POPUP: PROMPT RESTRICTED
# ══════════════════════════════════════════════════════════
class PromptRestricted(tk.Toplevel):
    def __init__(self, parent, texto, severidad, puntos, score_nuevo, razon="", on_decision=None):
        super().__init__(parent)
        self.on_decision=on_decision; self._t0=time.time()
        self.title(""); self.configure(bg=D["bg"])
        self.resizable(False,False)
        self.attributes("-topmost",True); self.grab_set_global(); self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._revisar)
        self.after(50,self._forzar_frente)
        self._ov=tk.Toplevel(parent)
        sw=self._ov.winfo_screenwidth(); sh=self._ov.winfo_screenheight()
        self._ov.geometry(f"{sw}x{sh}+0+0"); self._ov.configure(bg="black")
        self._ov.attributes("-alpha",0.75,"-topmost",True); self._ov.overrideredirect(True)
        self._ov.lower(self)
        self._build(texto,severidad,puntos,score_nuevo,razon); self._centrar()

    def _forzar_frente(self):
        try:
            import ctypes
            hwnd=int(self.wm_frame(),16)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except: pass
        self.focus_force(); self.lift()

    def _build(self, texto, severidad, puntos, score_nuevo, razon):
        outer=tk.Frame(self,bg=D["bg"],padx=32,pady=28); outer.pack(fill="both",expand=True)
        # Badge "ASISTENTE PROTECTOR"
        badge_f=tk.Frame(outer,bg=D["bg"]); badge_f.pack(pady=(0,12))
        tk.Label(badge_f,text="  ◈  ASISTENTE PROTECTOR  ",
                 font=("Helvetica",7,"bold"),fg=D["text2"],
                 bg=D["card2"],padx=8,pady=4).pack()
        # Icono triangulo
        ic=tk.Canvas(outer,width=64,height=64,bg=D["bg"],highlightthickness=0); ic.pack(pady=(0,12))
        ic.create_oval(4,4,60,60,fill="#1e1a2e",outline=D["accent"],width=2)
        ic.create_polygon([32,16,52,48,12,48],fill="#2d1a4a",outline=D["warn"],width=2)
        ic.create_text(32,37,text="!",font=("Helvetica",16,"bold"),fill=D["warn"])
        _lbl(outer,"Prompt Restricted",font=("Helvetica",20,"bold"),bg=D["bg"]).pack()
        _lbl(outer,
             "Tu solicitud fue marcada por el Asistente Protector de Aura.\n"
             "Este mensaje viola las guias de etica digital sobre\nacoso y contenido danino.",
             font=("Helvetica",9),fg=D["text2"],bg=D["bg"],justify="center",wraplength=360).pack(pady=(8,16))
        # Score badge
        sev_color=D["danger"]
        sb=tk.Frame(outer,bg=D["bg"]); sb.pack(pady=(0,12))
        tk.Label(sb,text=f"  CRITICO  ",font=("Helvetica",8,"bold"),
                 fg="white",bg=sev_color,padx=6,pady=3).pack(side="left",padx=4)
        tk.Label(sb,text=f"-{puntos} pts  →  Score: {score_nuevo}/100",
                 font=("Helvetica",9,"bold"),fg=D["danger"],bg=D["bg"]).pack(side="left")
        # Violation box
        if razon:
            vf=tk.Frame(outer,bg=D["card2"],padx=16,pady=12); vf.pack(fill="x",pady=(0,16))
            _lbl(vf,"Detected Violation:",font=("Helvetica",8),fg=D["text3"],bg=D["card2"]).pack(anchor="w")
            rf=tk.Frame(vf,bg=D["card2"]); rf.pack(anchor="w",pady=(4,0))
            tk.Label(rf,text="◈",font=("Helvetica",10),fg=D["accent"],bg=D["card2"]).pack(side="left")
            _lbl(rf," "+razon[:80],font=("Helvetica",9,"bold"),fg=D["text"],
                 bg=D["card2"],wraplength=300,justify="left").pack(side="left")
        # Compliance ID
        import random,string
        cid="AUR-"+"".join(random.choices(string.digits,k=4))+"-X"+"".join(random.choices(string.ascii_uppercase,k=1))
        _lbl(outer,f"COMPLIANCE ID: {cid}",font=("Helvetica",7),fg=D["text3"],bg=D["bg"]).pack(pady=(0,12))
        # Botones
        bf=tk.Frame(outer,bg=D["bg"]); bf.pack(fill="x")
        _btn(bf,"✎  Revisar Prompt",self._revisar,pady=10).pack(side="left",padx=(0,8))
        _btn(bf,"📖  Aprender Mas",self._revisar,bg=D["card2"],fg=D["text2"],pady=10).pack(side="left")

    def _centrar(self):
        self.update_idletasks()
        w=440; h=self.winfo_reqheight()
        sw=self.winfo_screenwidth(); sh=self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _cerrar_ov(self):
        try: self._ov.destroy()
        except: pass

    def _revisar(self):
        ms=int((time.time()-self._t0)*1000)
        self._cerrar_ov()
        if self.on_decision: self.on_decision("editar",ms)
        self.destroy()

# ══════════════════════════════════════════════════════════
#  PANEL DE DEBUG (ventana separada)
# ══════════════════════════════════════════════════════════
class PanelDebug(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Aura — Panel de Debug")
        self.geometry("800x600")
        self.configure(bg=D["bg"])
        self.resizable(True,True)
        self._build()
        self._refresh()

    def _build(self):
        # Header
        hdr=tk.Frame(self,bg=D["card"],pady=10,padx=16); hdr.pack(fill="x")
        _lbl(hdr,"Panel de Debug",font=("Helvetica",14,"bold"),bg=D["card"]).pack(side="left")
        _btn(hdr,"↻ Actualizar",self._refresh,
             bg=D["card2"],fg=D["text2"],font=("Helvetica",8),padx=10,pady=4).pack(side="right")
        _btn(hdr,"🗑 Limpiar BD",self._limpiar,
             bg=D["danger"],font=("Helvetica",8),padx=10,pady=4).pack(side="right",padx=(0,8))

        # Tabs
        nb=ttk.Notebook(self)
        nb.pack(fill="both",expand=True,padx=8,pady=8)

        style=ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",background=D["bg"],borderwidth=0)
        style.configure("TNotebook.Tab",background=D["card2"],foreground=D["text2"],
                        padding=[12,6],font=("Helvetica",9))
        style.map("TNotebook.Tab",background=[("selected",D["accent"])],
                  foreground=[("selected","white")])

        self._tab_log     = tk.Frame(nb,bg=D["bg"])
        self._tab_det     = tk.Frame(nb,bg=D["bg"])
        self._tab_score   = tk.Frame(nb,bg=D["bg"])
        self._tab_sitios  = tk.Frame(nb,bg=D["bg"])
        self._tab_raw     = tk.Frame(nb,bg=D["bg"])

        nb.add(self._tab_log,   text=" Log en vivo ")
        nb.add(self._tab_det,   text=" Detecciones ")
        nb.add(self._tab_score, text=" Score Diario ")
        nb.add(self._tab_sitios,text=" Sitios Bloq  ")
        nb.add(self._tab_raw,   text=" SQL Raw      ")

        self._build_tab_log()
        self._build_tab_detecciones()
        self._build_tab_score()
        self._build_tab_sitios()
        self._build_tab_raw()

    # ── Tab: Log en vivo ──────────────────────────────────
    def _build_tab_log(self):
        f=self._tab_log
        self._log_text=scrolledtext.ScrolledText(
            f,bg=D["card"],fg=D["text"],font=("Consolas",9),
            relief="flat",bd=0,state="disabled")
        self._log_text.pack(fill="both",expand=True,padx=4,pady=4)
        self._log_text.tag_configure("danger",foreground=D["danger"])
        self._log_text.tag_configure("warn",  foreground=D["warn"])
        self._log_text.tag_configure("safe",  foreground=D["safe"])
        self._log_text.tag_configure("muted", foreground=D["text3"])
        # Registrar en logger global
        from aura.logger import registrar_callback
        registrar_callback(self._on_log)

    def _on_log(self, msg, color):
        tag={D["warn"]:"warn",D["danger"]:"danger",D["safe"]:"safe"}.get(color,"muted")
        hora=datetime.now().strftime("%H:%M:%S")
        def _ins():
            self._log_text.configure(state="normal")
            self._log_text.insert("end","["+hora+"] "+msg+"\n",tag)
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
        try: self.after(0,_ins)
        except: pass

    # ── Tab: Detecciones ──────────────────────────────────
    def _build_tab_detecciones(self):
        f=self._tab_det
        cols=("ID","Fecha","Nivel","Score","Fuente","Texto","Puntos")
        tv=ttk.Treeview(f,columns=cols,show="headings",height=20)
        widths=[40,140,80,60,100,260,60]
        for c,w in zip(cols,widths):
            tv.heading(c,text=c); tv.column(c,width=w,minwidth=w)
        sb=ttk.Scrollbar(f,orient="vertical",command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); tv.pack(fill="both",expand=True,padx=4,pady=4)
        self._tv_det=tv
        style=ttk.Style()
        style.configure("Treeview",background=D["card"],fieldbackground=D["card"],
                        foreground=D["text"],rowheight=24,font=("Helvetica",9))
        style.configure("Treeview.Heading",background=D["card2"],foreground=D["text2"],
                        font=("Helvetica",9,"bold"))

    def _build_tab_score(self):
        f=self._tab_score
        cols=("Fecha","Score","Detecciones","Nivel")
        tv=ttk.Treeview(f,columns=cols,show="headings",height=20)
        for c,w in zip(cols,[150,80,100,120]):
            tv.heading(c,text=c); tv.column(c,width=w,minwidth=w)
        sb=ttk.Scrollbar(f,orient="vertical",command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); tv.pack(fill="both",expand=True,padx=4,pady=4)
        self._tv_score=tv

    def _build_tab_sitios(self):
        f=self._tab_sitios
        cols=("ID","Sitio","Inicio","Fin","Activo","Razon")
        tv=ttk.Treeview(f,columns=cols,show="headings",height=20)
        for c,w in zip(cols,[40,120,140,140,60,200]):
            tv.heading(c,text=c); tv.column(c,width=w,minwidth=w)
        sb=ttk.Scrollbar(f,orient="vertical",command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); tv.pack(fill="both",expand=True,padx=4,pady=4)
        self._tv_sitios=tv

    def _build_tab_raw(self):
        f=self._tab_raw
        _lbl(f,"Ejecutar SQL directo:",font=("Helvetica",9),bg=D["bg"],fg=D["text2"]).pack(anchor="w",padx=8,pady=(8,2))
        self._sql_entry=tk.Text(f,height=3,bg=D["card"],fg=D["text"],
                                 font=("Consolas",9),relief="flat",bd=4)
        self._sql_entry.pack(fill="x",padx=8); self._sql_entry.insert("1.0","SELECT * FROM detecciones LIMIT 10;")
        _btn(f,"▶ Ejecutar",self._exec_sql,font=("Helvetica",8),pady=4).pack(anchor="w",padx=8,pady=4)
        self._sql_result=scrolledtext.ScrolledText(f,bg=D["card"],fg=D["safe"],
                                                    font=("Consolas",8),relief="flat",bd=0)
        self._sql_result.pack(fill="both",expand=True,padx=8,pady=(0,8))

    def _exec_sql(self):
        import sqlite3, os
        db=os.path.normpath(os.path.join(os.path.dirname(__file__),"..","..","aura_data.db"))
        sql=self._sql_entry.get("1.0","end").strip()
        self._sql_result.configure(state="normal"); self._sql_result.delete("1.0","end")
        try:
            con=sqlite3.connect(db); con.row_factory=sqlite3.Row
            rows=con.execute(sql).fetchall(); con.close()
            if rows:
                self._sql_result.insert("end"," | ".join(rows[0].keys())+"\n","")
                self._sql_result.insert("end","-"*80+"\n")
                for r in rows:
                    self._sql_result.insert("end"," | ".join(str(v) for v in r)+"\n")
            else:
                self._sql_result.insert("end","(sin resultados)\n")
        except Exception as e:
            self._sql_result.insert("end","ERROR: "+str(e)+"\n")
        self._sql_result.configure(state="disabled")

    def _limpiar(self):
        from aura.database import limpiar_todo
        limpiar_todo()
        self._refresh()

    def _refresh(self):
        try:
            from aura.database import get_detecciones, get_score_historico, get_sitios_bloqueados
            # Detecciones
            self._tv_det.delete(*self._tv_det.get_children())
            for d in get_detecciones(100):
                self._tv_det.insert("","end",values=(
                    d["id"],d["fecha"][:16],d["nivel"],
                    round(d["score_ia"],2),d["fuente"],
                    d["texto"][:50],d["puntos_rest"]
                ))
            # Score
            self._tv_score.delete(*self._tv_score.get_children())
            for s in get_score_historico(30):
                self._tv_score.insert("","end",values=(
                    s["fecha"],s["score"],s["detecciones"],s["nivel_dia"]
                ))
            # Sitios
            self._tv_sitios.delete(*self._tv_sitios.get_children())
            for s in get_sitios_bloqueados(50):
                self._tv_sitios.insert("","end",values=(
                    s["id"],s["sitio"],s["fecha_ini"][:16],
                    s["fecha_fin"][:16] if s["fecha_fin"] else "—",
                    "SI" if s["activo"] else "NO",s["razon"][:40]
                ))
        except Exception as e:
            pass
        self.after(5000, self._refresh)

# ══════════════════════════════════════════════════════════
#  DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════════════════
class AuraDashboard(tk.Tk):
    WIDTH=1100; HEIGHT=680

    def __init__(self):
        super().__init__()
        self.title("Aura: Escudo Etico")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.configure(bg=D["bg"])
        self.resizable(True,True); self.minsize(900,600)

        # Init DB
        try:
            from aura.database import inicializar, get_config
            from aura.config import CONFIG
            inicializar()
            key=get_config("groq_key","")
            if key: CONFIG["groq_key"]=key
        except Exception as e:
            print("DB init error:",e)

        self._vista="home"; self._monitor=None; self._encendido=False
        self._debug_win=None; self._ultimo_det_id=None
        self._build(); self._nav("home")
        self._actualizar_score_ui()
        self.after(10000, self._refresh_loop)

    def _refresh_loop(self):
        if self._vista=="home": self._actualizar_score_ui()
        self.after(10000, self._refresh_loop)

    def _actualizar_score_ui(self):
        try:
            from aura.database import get_score_hoy, get_stats_hoy, get_score_historico
            score=get_score_hoy(); stats=get_stats_hoy()
            hist=get_score_historico(7)
            if hasattr(self,"_score_ring"): self._score_ring.update_score(score)
            if hasattr(self,"_lbl_alertas"): self._lbl_alertas.configure(text=str(stats["total"]))
            if hasattr(self,"_lbl_criticos"): self._lbl_criticos.configure(text=str(stats["criticos"]))
            if hasattr(self,"_lbl_editados"): self._lbl_editados.configure(text=str(stats["editados"]))
            # Grafico
            if hasattr(self,"_spark") and hist:
                self._spark.update_data([h["score"] for h in hist],
                                         [h["fecha"][-5:] for h in hist])
            # Trend label
            if hasattr(self,"_lbl_trend") and len(hist)>=2:
                diff=hist[-1]["score"]-hist[-2]["score"]
                arrow="↑" if diff>=0 else "↓"
                color=D["safe"] if diff>=0 else D["danger"]
                self._lbl_trend.configure(text=f"{arrow} {abs(diff)} pts hoy",fg=color)
            # Log de detecciones recientes
            if hasattr(self,"_log_items_frame"):
                for w in self._log_items_frame.winfo_children(): w.destroy()
                from aura.database import get_detecciones
                for d in get_detecciones(5,solo_hoy=True):
                    self._add_log_item(
                        d["nivel"]+" detectado", d["razon"][:50] or d["texto"][:50],
                        D["danger"] if d["nivel"]=="CRITICO" else D["warn"],
                        d["fecha"][11:16]
                    )
        except Exception as e:
            pass

    # ── Build base ────────────────────────────────────────
    def _build(self):
        self._sidebar=tk.Frame(self,bg=D["sidebar"],width=210)
        self._sidebar.pack(side="left",fill="y"); self._sidebar.pack_propagate(False)
        self._content=tk.Frame(self,bg=D["bg"])
        self._content.pack(side="left",fill="both",expand=True)
        self._build_sidebar()

    def _build_sidebar(self):
        s=self._sidebar
        # Logo
        top=tk.Frame(s,bg=D["sidebar"],pady=18,padx=16); top.pack(fill="x")
        LogoCanvas(top,size=32,bg=D["sidebar"]).pack(side="left")
        tf=tk.Frame(top,bg=D["sidebar"]); tf.pack(side="left",padx=(10,0))
        _lbl(tf,"Aura",font=("Helvetica",13,"bold"),bg=D["sidebar"]).pack(anchor="w")
        _lbl(tf,"ETHICAL SHIELD",font=("Helvetica",7,"bold"),
             fg=D["accentl"],bg=D["sidebar"]).pack(anchor="w")
        _sep(s,D["border"]).pack(fill="x",padx=16)
        # Nav
        self._nav_btns={}
        menu=[("home","Home","⌂"),("chat_guard","Chat Guard","◉"),
              ("ai_shield","AI Shield","◈"),("settings","Settings","⚙")]
        nf=tk.Frame(s,bg=D["sidebar"],pady=10); nf.pack(fill="x")
        for key,lbl,ico in menu:
            self._nav_btns[key]=self._nav_item(nf,key,ico,lbl)
        # Debug button
        tk.Frame(s,bg=D["sidebar"]).pack(fill="both",expand=True)
        _btn(s,"🐛  Debug Panel",self._abrir_debug,
             bg=D["card2"],fg=D["text2"],font=("Helvetica",8),pady=6).pack(fill="x",padx=14,pady=(0,6))
        # Activate button
        self._btn_protect=_btn(s,"▶  Activar Proteccion",self._toggle_monitor,pady=10)
        self._btn_protect.pack(fill="x",padx=14,pady=(0,16))
        # Edge AI status badge
        badge=tk.Frame(s,bg=D["card2"],padx=12,pady=8); badge.pack(fill="x",padx=14,pady=(0,14))
        dot=tk.Label(badge,text="●",font=("Helvetica",8),fg=D["safe"],bg=D["card2"]); dot.pack(side="left")
        bf=tk.Frame(badge,bg=D["card2"]); bf.pack(side="left",padx=(6,0))
        _lbl(bf,"Edge AI Active",font=("Helvetica",8,"bold"),bg=D["card2"]).pack(anchor="w")
        _lbl(bf,"Local processing active",font=("Helvetica",7),fg=D["text3"],bg=D["card2"]).pack(anchor="w")

    def _nav_item(self, parent, key, ico, lbl):
        f=tk.Frame(parent,bg=D["sidebar"],cursor="hand2"); f.pack(fill="x")
        ind=tk.Frame(f,bg=D["sidebar"],width=3); ind.pack(side="left",fill="y")
        inner=tk.Frame(f,bg=D["sidebar"],padx=14,pady=11); inner.pack(side="left",fill="x",expand=True)
        il=tk.Label(inner,text=ico,font=("Helvetica",11),fg=D["text2"],bg=D["sidebar"]); il.pack(side="left")
        ll=tk.Label(inner,text=" "+lbl,font=("Helvetica",10),fg=D["text2"],bg=D["sidebar"]); ll.pack(side="left")
        def click(e): self._nav(key)
        for w in [f,inner,il,ll]: w.bind("<Button-1>",click)
        def enter(e):
            if self._vista!=key:
                for w2 in [f,inner,il,ll]: w2.configure(bg=D["card"])
        def leave(e):
            if self._vista!=key:
                for w2 in [f,inner,il,ll]: w2.configure(bg=D["sidebar"])
        for w in [f,inner,il,ll]: w.bind("<Enter>",enter); w.bind("<Leave>",leave)
        f._ind=ind; f._ico=il; f._lbl=ll; f._inner=inner
        return f

    def _nav(self, key):
        self._vista=key
        for k,btn in self._nav_btns.items():
            if k==key:
                for w in [btn,btn._inner,btn._ico,btn._lbl]: w.configure(bg=D["card2"])
                btn._ind.configure(bg=D["accent"]); btn._ico.configure(fg=D["accent"])
                btn._lbl.configure(fg=D["text"],font=("Helvetica",10,"bold"))
            else:
                for w in [btn,btn._inner,btn._ico,btn._lbl]: w.configure(bg=D["sidebar"])
                btn._ind.configure(bg=D["sidebar"]); btn._ico.configure(fg=D["text2"])
                btn._lbl.configure(fg=D["text2"],font=("Helvetica",10))
        for w in self._content.winfo_children(): w.destroy()
        {"home":self._vista_home,"chat_guard":self._vista_chat_guard,
         "ai_shield":self._vista_ai_shield,"settings":self._vista_settings}.get(key,self._vista_home)()

    # ── Vista: HOME ───────────────────────────────────────
    def _vista_home(self):
        root=self._content
        # Header
        hdr=tk.Frame(root,bg=D["bg"],padx=28,pady=20); hdr.pack(fill="x")
        _lbl(hdr,"Reputation Dashboard",font=("Helvetica",20,"bold"),bg=D["bg"]).pack(anchor="w",side="left")
        right=tk.Frame(hdr,bg=D["bg"]); right.pack(side="right")
        tk.Label(right,text="🔔",font=("Helvetica",14),fg=D["text2"],bg=D["bg"]).pack(side="left",padx=(0,10))
        av=tk.Frame(right,bg=D["card2"],padx=10,pady=6); av.pack(side="left")
        tk.Label(av,text="  Alex Rivera  ",font=("Helvetica",9,"bold"),fg=D["text"],bg=D["card2"]).pack()
        _lbl(hdr,"Real-time digital citizenship & ethical health analytics.",
             font=("Helvetica",9),fg=D["text2"],bg=D["bg"]).pack(anchor="sw",side="left",padx=(12,0))

        body=tk.Frame(root,bg=D["bg"],padx=28); body.pack(fill="both",expand=True)

        # Fila superior
        row1=tk.Frame(body,bg=D["bg"]); row1.pack(fill="x",pady=(0,14))

        # Tarjeta score
        sc=_card(row1,padx=24,pady=20); sc.pack(side="left",padx=(0,12))
        _lbl(sc,"DIGITAL CITIZENSHIP SCORE",font=("Helvetica",8,"bold"),
             fg=D["text3"],bg=D["card"]).pack(anchor="w")
        from aura.database import get_score_hoy
        score=get_score_hoy()
        self._score_ring=ScoreRing(sc,size=200,score=score)
        self._score_ring.pack(pady=(12,8))
        self._lbl_trend=tk.Label(sc,text="— sin cambios hoy",
                                  font=("Helvetica",9,"bold"),
                                  fg=D["text3"],bg=D["card2"],padx=12,pady=5)
        self._lbl_trend.pack()
        _lbl(sc,"Tu huella etica es excepcional.\nEsta en el top 2% de ciudadanos digitales.",
             font=("Helvetica",8),fg=D["text2"],bg=D["card"],
             wraplength=200,justify="center").pack(pady=(8,0))

        # Metricas rapidas
        mc=tk.Frame(row1,bg=D["bg"]); mc.pack(side="left",fill="both",expand=True)
        metrics=[
            ("❤","EMOTIONAL IMPACT","High","+2%",D["pink"],D["safe"]),
            ("🔒","PRIVACY SAFETY","98%","-1%",D["teal"],D["warn"]),
            ("★","COMMUNITY","Gold Tier","+12%",D["gold"],D["safe"]),
        ]
        for ico,title,val,chg,icolor,ccolor in metrics:
            mf=_card(mc,padx=16,pady=14); mf.pack(fill="x",pady=(0,8))
            top=tk.Frame(mf,bg=D["card"]); top.pack(fill="x")
            tk.Label(top,text=ico,font=("Helvetica",16),fg=icolor,bg=D["card"]).pack(side="left")
            tk.Label(top,text=" "+chg,font=("Helvetica",9,"bold"),fg=ccolor,bg=D["card"]).pack(side="right")
            _lbl(mf,title,font=("Helvetica",8,"bold"),fg=D["text3"],bg=D["card"]).pack(anchor="w",pady=(6,2))
            _lbl(mf,val,font=("Helvetica",16,"bold"),bg=D["card"]).pack(anchor="w")

        # Fila inferior
        row2=tk.Frame(body,bg=D["bg"]); row2.pack(fill="both",expand=True)

        # Grafico estabilidad
        stab=_card(row2,padx=20,pady=16); stab.pack(side="left",fill="both",expand=True,padx=(0,12))
        sh=tk.Frame(stab,bg=D["card"]); sh.pack(fill="x")
        _lbl(sh,"Reputation Stability",font=("Helvetica",12,"bold"),bg=D["card"]).pack(side="left")
        tbf=tk.Frame(sh,bg=D["card"]); tbf.pack(side="right")
        for t,sel in [("Weekly",False),("Monthly",True)]:
            bg=D["accent"] if sel else D["card2"]
            fg2="white" if sel else D["text3"]
            tk.Label(tbf,text=" "+t+" ",font=("Helvetica",8,"bold"),
                     fg=fg2,bg=bg,padx=6,pady=3).pack(side="left",padx=2)
        from aura.database import get_score_historico
        hist=get_score_historico(7)
        scores=[h["score"] for h in hist]
        labels=[h["fecha"][-5:] for h in hist]
        if not scores: scores=[100]*7; labels=["—"]*7
        self._spark=SparkBars(stab,data=scores,labels=labels)
        self._spark.pack(fill="both",expand=True,pady=(14,0),ipady=8)

        # Stats hoy
        from aura.database import get_stats_hoy
        stats=get_stats_hoy()
        sf=tk.Frame(row2,bg=D["bg"],width=240); sf.pack(side="left",fill="y"); sf.pack_propagate(False)
        for sval,slbl,sclr in [
            (str(stats["total"]),   "Alertas hoy",    D["danger"]),
            (str(stats["criticos"]),"Nivel Critico",  D["warn"]),
            (str(stats["editados"]),"Editados",       D["safe"]),
        ]:
            sf2=_card(sf,padx=16,pady=10); sf2.pack(fill="x",pady=(0,6))
            lv=tk.Label(sf2,text=sval,font=("Helvetica",22,"bold"),fg=sclr,bg=D["card"]); lv.pack(anchor="w")
            _lbl(sf2,slbl,font=("Helvetica",8),fg=D["text2"],bg=D["card"]).pack(anchor="w")
            if slbl=="Alertas hoy": self._lbl_alertas=lv
            elif slbl=="Nivel Critico": self._lbl_criticos=lv
            elif slbl=="Editados": self._lbl_editados=lv

        # Shield log
        log_frame=_card(row2,padx=16,pady=14); log_frame.pack(side="left",fill="both",expand=True,padx=(8,0))
        _lbl(log_frame,"Shield Protection Log",font=("Helvetica",11,"bold"),bg=D["card"]).pack(anchor="w")
        self._log_items_frame=tk.Frame(log_frame,bg=D["card"]); self._log_items_frame.pack(fill="both",expand=True,pady=(10,0))
        self._actualizar_score_ui()

    def _add_log_item(self, title, desc, color, tiempo):
        item=_card2(self._log_items_frame,padx=12,pady=8)
        item.pack(fill="x",pady=(0,6))
        row=tk.Frame(item,bg=D["card2"]); row.pack(fill="x")
        sf=tk.Frame(row,bg=color,width=32,height=32); sf.pack(side="left"); sf.pack_propagate(False)
        tk.Label(sf,text="◈",font=("Helvetica",12),fg="white",bg=color).place(relx=.5,rely=.5,anchor="center")
        inf=tk.Frame(row,bg=D["card2"],padx=10); inf.pack(side="left",fill="x",expand=True)
        _lbl(inf,title,font=("Helvetica",9,"bold"),bg=D["card2"]).pack(anchor="w")
        _lbl(inf,desc,font=("Helvetica",8),fg=D["text2"],bg=D["card2"],wraplength=220).pack(anchor="w")
        _lbl(row,tiempo,font=("Helvetica",7),fg=D["text3"],bg=D["card2"]).pack(side="right",anchor="n",padx=4)

    # ── Vista: CHAT GUARD ─────────────────────────────────
    def _vista_chat_guard(self):
        root=self._content
        hdr=tk.Frame(root,bg=D["bg"],padx=28,pady=16); hdr.pack(fill="x")
        _lbl(hdr,"Aura Chat Guard",font=("Helvetica",18,"bold"),bg=D["bg"]).pack(side="left")
        rh=tk.Frame(hdr,bg=D["bg"]); rh.pack(side="right")
        _lbl(rh,"SYSTEM HEALTH",font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["bg"]).pack(anchor="e")
        sh=tk.Frame(rh,bg=D["bg"]); sh.pack(anchor="e")
        tk.Label(sh,text="●",font=("Helvetica",9),fg=D["safe"],bg=D["bg"]).pack(side="left")
        _lbl(sh,"Optimized",font=("Helvetica",9,"bold"),fg=D["safe"],bg=D["bg"]).pack(side="left")
        body=tk.Frame(root,bg=D["bg"],padx=28); body.pack(fill="both",expand=True)

        # Sidebar izquierdo
        left=tk.Frame(body,bg=D["bg"],width=220); left.pack(side="left",fill="y",padx=(0,12)); left.pack_propagate(False)
        sc=_card(left,padx=14,pady=12); sc.pack(fill="x",pady=(0,10))
        _lbl(sc,"Aura Status",font=("Helvetica",8,"bold"),fg=D["text3"],bg=D["card"]).pack(anchor="w")
        sr=tk.Frame(sc,bg=D["card"]); sr.pack(fill="x",pady=(4,0))
        dot_c=D["safe"] if self._encendido else D["text3"]
        tk.Label(sr,text="●",font=("Helvetica",10),fg=dot_c,bg=D["card"]).pack(side="left")
        self._cg_status=_lbl(sr,"Monitoring" if self._encendido else "Inactive",
                              font=("Helvetica",13,"bold"),bg=D["card"])
        self._cg_status.pack(side="left",padx=(6,0))
        _lbl(sc,"Scan Frequency: 0.2ms",font=("Helvetica",8),fg=D["text3"],bg=D["card"]).pack(anchor="w",pady=(4,0))

        _lbl(left,"PROTECTION LAYERS",font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["bg"]).pack(anchor="w",pady=(8,4))
        layers=[("◈","End-to-End Encryption","AES-256 Bit Active"),
                ("◎","DLP Engine","Scanning for PII"),
                ("◉","Anonymization","Dynamic Masking On")]
        for ico,title,sub in layers:
            lf=_card(left,padx=12,pady=10); lf.pack(fill="x",pady=(0,6))
            lr=tk.Frame(lf,bg=D["card"]); lr.pack(fill="x")
            tk.Label(lr,text=ico,font=("Helvetica",12),fg=D["accent"],bg=D["card"]).pack(side="left")
            inf=tk.Frame(lr,bg=D["card"],padx=10); inf.pack(side="left")
            _lbl(inf,title,font=("Helvetica",9,"bold"),bg=D["card"]).pack(anchor="w")
            _lbl(inf,sub,font=("Helvetica",7),fg=D["text3"],bg=D["card"]).pack(anchor="w")

        # Quote box
        qf=tk.Frame(left,bg=D["card2"],padx=12,pady=10); qf.pack(fill="x",pady=(8,0))
        _lbl(qf,'"Aura is currently intercepting and scrubbing session tokens from outbound requests."',
             font=("Helvetica",8,"italic"),fg=D["text2"],bg=D["card2"],wraplength=180,justify="left").pack()

        # Chat principal
        main=tk.Frame(body,bg=D["bg"]); main.pack(side="left",fill="both",expand=True)
        # Session banner
        sb=tk.Frame(main,bg=D["bg"]); sb.pack(fill="x",pady=(0,8))
        tk.Label(sb,text="— SECURE SESSION STARTED — TODAY "+datetime.now().strftime("%I:%M %p")+" —",
                 font=("Helvetica",8),fg=D["text3"],bg=D["bg"]).pack()

        msgs_outer=_card(main); msgs_outer.pack(fill="both",expand=True)
        msgs_f=tk.Frame(msgs_outer,bg=D["card"],padx=16,pady=12); msgs_f.pack(fill="both",expand=True)
        # Mensaje sistema
        self._add_chat_msg(msgs_f,
            "Aura Core","SYSTEM",
            "Connection initialized. I'm Aura, your real-time security guard. "
            "Every message you type is being scanned for sensitive information before it hits the network.",
            is_system=True)

        # Input bar
        ib=tk.Frame(main,bg=D["card2"],padx=16,pady=10); ib.pack(fill="x",pady=(8,0))
        st=tk.Frame(ib,bg=D["card2"]); st.pack(fill="x",side="bottom",pady=(6,0))
        for dot,lbl in [("●","DLP: ACTIVE"),("●","PII: MASKING")]:
            tk.Label(st,text=dot,font=("Helvetica",8),fg=D["safe"],bg=D["card2"]).pack(side="left",padx=(0,2))
            _lbl(st,lbl,font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["card2"]).pack(side="left",padx=(0,10))
        _lbl(st,"Data is processed locally and encrypted before transmission",
             font=("Helvetica",7),fg=D["text3"],bg=D["card2"]).pack(side="right")
        inp=tk.Frame(ib,bg=D["card2"]); inp.pack(fill="x")
        _lbl(inp,"+",font=("Helvetica",14),fg=D["text2"],bg=D["card2"]).pack(side="left",padx=(0,8))
        self._chat_e=tk.Entry(inp,bg=D["card2"],fg=D["text"],insertbackground=D["text"],
                               font=("Helvetica",10),relief="flat",bd=0)
        self._chat_e.pack(side="left",fill="x",expand=True)
        self._chat_e.insert(0,"Type your message... (Aura is watching for sensitive data)")
        self._chat_e.bind("<FocusIn>",lambda e:self._chat_e.delete(0,"end") if "Aura" in self._chat_e.get() else None)
        tk.Label(inp,text="🙂",font=("Helvetica",12),fg=D["text2"],bg=D["card2"]).pack(side="left",padx=(8,6))
        _btn(inp,"➤",lambda:self._analizar_chat(msgs_f),bg=D["accent"],padx=10,pady=6).pack(side="left")
        # Active shield banner
        asf=tk.Frame(main,bg=D["bg"]); asf.pack(fill="x",pady=(6,0))
        tk.Label(asf,text="◈  AURA ACTIVE SHIELD: REAL-TIME SCANNING",
                 font=("Helvetica",7,"bold"),fg=D["text3"],bg=D["card2"],padx=12,pady=4).pack()

        self._msgs_frame=msgs_f

    def _add_chat_msg(self, parent, sender, badge, text, is_me=False, is_system=False, tag_color=None):
        mf=tk.Frame(parent,bg=D["card"]); mf.pack(fill="x",pady=(0,12),anchor="e" if is_me else "w")
        if not is_me:
            top=tk.Frame(mf,bg=D["card"]); top.pack(anchor="w",pady=(0,4))
            if is_system:
                ic=tk.Canvas(top,width=28,height=28,bg=D["card"],highlightthickness=0); ic.pack(side="left")
                ic.create_oval(1,1,27,27,fill=D["accent"],outline="")
                ic.create_text(14,14,text="⚡",font=("Helvetica",10),fill="white")
            tk.Label(top,text=" "+sender,font=("Helvetica",9,"bold"),fg=D["text"],bg=D["card"]).pack(side="left")
            if badge:
                bg={"SYSTEM":D["card2"],"INTERCEPTED":D["danger"]}.get(badge,D["card2"])
                tk.Label(top,text="  "+badge+"  ",font=("Helvetica",7,"bold"),
                         fg="white",bg=bg,padx=4,pady=2).pack(side="left",padx=(6,0))
        bubble=tk.Frame(mf,bg=D["accent"] if is_me else D["card2"],padx=14,pady=10)
        bubble.pack(anchor="e" if is_me else "w",pady=(0,2))
        if tag_color:
            tf=tk.Frame(bubble,bg=D["card2"]); tf.pack(anchor="w",pady=(0,6))
            tk.Label(tf,text="⚠ ",font=("Helvetica",9),fg=D["warn"],bg=D["card2"]).pack(side="left")
            tk.Label(tf,text="Potential Risk Detected",font=("Helvetica",9,"bold"),
                     fg=D["warn"],bg=D["card2"]).pack(side="left")
        tk.Label(bubble,text=text,font=("Helvetica",9),
                 fg=D["text"],bg=D["accent"] if is_me else D["card2"],
                 wraplength=380,justify="left").pack(anchor="w")

    def _analizar_chat(self, msgs_frame):
        texto=self._chat_e.get().strip()
        if not texto or "Aura is watching" in texto: return
        self._chat_e.delete(0,"end")
        self._add_chat_msg(msgs_frame,"","",texto,is_me=True)
        def _run():
            try:
                from aura.detector import analizar
                resultado=analizar(texto)
                def _show():
                    if resultado:
                        self._add_chat_msg(msgs_frame,"Aura Guard","INTERCEPTED",
                            "I noticed: "+resultado.get("razon","Contenido potencialmente ofensivo")[:120],
                            tag_color=D["warn"])
                self.after(0,_show)
            except Exception as e:
                pass
        threading.Thread(target=_run,daemon=True).start()

    # ── Vista: AI SHIELD ─────────────────────────────────
    def _vista_ai_shield(self):
        root=self._content
        hdr=tk.Frame(root,bg=D["bg"],padx=28,pady=20); hdr.pack(fill="x")
        _lbl(hdr,"AI Shield",font=("Helvetica",18,"bold"),bg=D["bg"]).pack(anchor="w")
        _lbl(hdr,"Configura el motor de inteligencia artificial de Aura",
             font=("Helvetica",9),fg=D["text2"],bg=D["bg"]).pack(anchor="w")
        body=tk.Frame(root,bg=D["bg"],padx=28); body.pack(fill="both",expand=True)
        # API Key
        ac=_card(body,padx=20,pady=18); ac.pack(fill="x",pady=(0,12))
        _lbl(ac,"Groq API Key",font=("Helvetica",12,"bold"),bg=D["card"]).pack(anchor="w")
        _lbl(ac,"Obtén tu key gratuita en console.groq.com — modelo LLaMA3",
             font=("Helvetica",8),fg=D["text2"],bg=D["card"]).pack(anchor="w",pady=(4,12))
        er=tk.Frame(ac,bg=D["card"]); er.pack(fill="x")
        from aura.database import get_config
        from aura.config import CONFIG
        self._key_e=tk.Entry(er,show="*",bg=D["card2"],fg=D["text"],insertbackground=D["text"],
                              font=("Helvetica",10),relief="flat",bd=0,
                              highlightthickness=1,highlightbackground=D["border"],highlightcolor=D["accent"])
        self._key_e.pack(side="left",fill="x",expand=True,ipady=8,padx=(0,10))
        self._key_e.insert(0,get_config("groq_key","") or CONFIG.get("groq_key",""))
        self._key_st=_lbl(er,"",font=("Helvetica",8),fg=D["text3"],bg=D["card"])
        self._key_st.pack(side="left",padx=(0,10))
        _btn(er,"Guardar y Probar",self._guardar_key,pady=8).pack(side="left")
        # Modos
        _lbl(body,"Capas de Deteccion",font=("Helvetica",11,"bold"),bg=D["bg"]).pack(anchor="w",pady=(12,8))
        layers=[("Groq AI (LLaMA3)","Analisis profundo con comprension de contexto. Prioridad maxima.",True,D["accent"]),
                ("Analisis Local","Palabras clave. Instantaneo. Sin internet. Fallback.",True,D["safe"]),
                ("Localhost (Ollama)","Modelo local si Groq no responde. Puerto 11434.",False,D["teal"])]
        for name,desc,active,color in layers:
            lf=_card(body,padx=16,pady=12); lf.pack(fill="x",pady=(0,8))
            lr=tk.Frame(lf,bg=D["card"]); lr.pack(fill="x")
            tk.Label(lr,text="●",font=("Helvetica",10),fg=color if active else D["text3"],bg=D["card"]).pack(side="left")
            _lbl(lr," "+name,font=("Helvetica",10,"bold"),bg=D["card"],
                 fg=D["text"] if active else D["text2"]).pack(side="left")
            _lbl(lr,"ACTIVO" if active else "Standby",font=("Helvetica",8,"bold"),
                 fg=color if active else D["text3"],bg=D["card"]).pack(side="right")
            _lbl(lf,desc,font=("Helvetica",8),fg=D["text2"],bg=D["card"]).pack(anchor="w",pady=(4,0))

    def _guardar_key(self):
        import tkinter.messagebox as mb
        import traceback
        from aura.config import CONFIG
        from aura.database import set_config

        key = self._key_e.get().strip()
        CONFIG["groq_key"] = key
        set_config("groq_key", key)

        if not key:
            self._key_st.configure(text="Sin key", fg=D["text3"])
            return

        self._key_st.configure(text="Probando...", fg=D["warn"])

        def probe():
            try:
                # 1. Libreria instalada?
                try:
                    from groq import Groq
                except ImportError:
                    def _e():
                        self._key_st.configure(text="Sin libreria", fg=D["danger"])
                        mb.showerror("Libreria faltante",
                                     "Ejecuta en tu terminal:\n  pip install groq")
                    self.after(0, _e)
                    return

                # 2. Formato valido?
                if not key.startswith("gsk_"):
                    def _e():
                        self._key_st.configure(text="Key invalida", fg=D["danger"])
                        mb.showerror("Key invalida",
                                     "La key debe empezar con gsk_\n"
                                     "Obtienela en console.groq.com\n\n"
                                     "Key ingresada: " + key[:20] + "...")
                    self.after(0, _e)
                    return

                # 3. Probar conexion real
                client = Groq(api_key=key)
                resp = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10,
                )
                model_ok = getattr(resp, "model", "llama-3.1-8b-instant")

                def _ok(m=model_ok):
                    self._key_st.configure(text="Conectado", fg=D["safe"])
                    mb.showinfo("Groq Conectado",
                                "Conexion exitosa\nModelo: " + str(m) +
                                "\n\nEl analisis con IA ya esta activo.")
                self.after(0, _ok)

            except Exception as e:
                tb = traceback.format_exc()
                err_txt = type(e).__name__ + ": " + str(e)[:150]

                def _err(et=err_txt, tbt=tb[-500:]):
                    self._key_st.configure(text="Error", fg=D["danger"])
                    mb.showerror("Error de conexion Groq",
                                 "Error: " + et +
                                 "\n\nPosibles causas:\n"
                                 "1. Key incorrecta\n"
                                 "2. Sin internet\n"
                                 "3. Cuenta Groq sin creditos\n\n"
                                 "Detalle:\n" + tbt)
                self.after(0, _err)

        threading.Thread(target=probe, daemon=True).start()

    # ── Vista: SETTINGS ───────────────────────────────────
    def _vista_settings(self):
        root=self._content
        hdr=tk.Frame(root,bg=D["bg"],padx=28,pady=20); hdr.pack(fill="x")
        _lbl(hdr,"Configuracion",font=("Helvetica",18,"bold"),bg=D["bg"]).pack(anchor="w")
        body=tk.Frame(root,bg=D["bg"],padx=28); body.pack(fill="both",expand=True)
        settings=[("Bloqueo de Sitios Web","Bloquear sitios tras 3 detecciones en el mismo sitio.",True),
                  ("Notificaciones del Sistema","Mostrar notificaciones de Windows al detectar contenido.",True),
                  ("Alerta Score Critico","Mostrar popup cuando el score baje de 50 puntos.",True),
                  ("Modo Silencioso","Solo bloquear Enter, sin popup de alerta visual.",False)]
        for title,desc,default in settings:
            sf=_card(body,padx=16,pady=14); sf.pack(fill="x",pady=(0,8))
            row=tk.Frame(sf,bg=D["card"]); row.pack(fill="x")
            _lbl(row,title,font=("Helvetica",10,"bold"),bg=D["card"]).pack(side="left")
            tk.Label(row,text=" ON " if default else " OFF ",
                     font=("Helvetica",8,"bold"),
                     fg="white" if default else D["text3"],
                     bg=D["accent"] if default else D["card2"],
                     padx=4,pady=2).pack(side="right")
            _lbl(sf,desc,font=("Helvetica",8),fg=D["text2"],bg=D["card"]).pack(anchor="w",pady=(4,0))
        # Danger zone
        _lbl(body,"Zona de Riesgo",font=("Helvetica",11,"bold"),fg=D["danger"],bg=D["bg"]).pack(anchor="w",pady=(16,8))
        dc=_card(body,padx=16,pady=14); dc.pack(fill="x")
        _lbl(dc,"Limpiar todo el historial",font=("Helvetica",10),bg=D["card"]).pack(side="left")
        _btn(dc,"Limpiar BD",self._limpiar_bd,bg=D["danger"],pady=4).pack(side="right")

    def _limpiar_bd(self):
        from aura.database import limpiar_todo
        limpiar_todo(); self._actualizar_score_ui()

    # ── Monitor ───────────────────────────────────────────
    def _toggle_monitor(self):
        self._encendido = not self._encendido
        if self._encendido:
            self._btn_protect.configure(text="⏸  Pausar Proteccion",bg=D["danger"])
            try:
                from aura.monitor import MonitorTeclado
                self._monitor=MonitorTeclado(on_alerta=self._on_alerta)
                self._monitor.iniciar()
            except Exception as e:
                print("Monitor error:",e)
        else:
            self._btn_protect.configure(text="▶  Activar Proteccion",bg=D["accent"])
            try: self._monitor.detener()
            except: pass

    def _on_alerta(self, resultado, texto):
        self.after(0, self._mostrar_alerta, resultado, texto)

    def _mostrar_alerta(self, resultado, texto):
        from aura.scoring import procesar_deteccion, get_consecuencias
        from aura.site_blocker import sitio_activo
        from aura.database import registrar_decision

        sitio=sitio_activo() or ""
        info=procesar_deteccion(texto, resultado, sitio=sitio)
        self._ultimo_det_id=info["deteccion_id"]
        self._actualizar_score_ui()

        sev=info["severidad"]; puntos=info["puntos"]; score=info["score_nuevo"]

        t0=time.time()
        def on_decision(decision, ms=0):
            try:
                registrar_decision(self._ultimo_det_id, decision, ms)
            except: pass
            try:
                self._monitor.desbloquear_enter()
                if decision=="continuar":
                    from pynput.keyboard import Controller, Key
                    kb=Controller(); kb.press(Key.enter); kb.release(Key.enter)
                self._monitor.reanudar()
            except: pass
            self._actualizar_score_ui()
            # Verificar score bajo
            if info["alerta_score_bajo"]:
                consecuencias=get_consecuencias(score)
                self.after(500,lambda:AlertaScoreCritico(self,score,consecuencias))

        try: self._monitor.pausar()
        except: pass

        if sev=="CRITICO":
            PromptRestricted(self, texto, sev, puntos, score,
                             razon=resultado.get("razon",""), on_decision=on_decision)
        else:
            EspejoEmpatia(self, texto, sev, puntos, score, on_decision=on_decision)

    # ── Debug window ─────────────────────────────────────
    def _abrir_debug(self):
        if self._debug_win and self._debug_win.winfo_exists():
            self._debug_win.lift(); return
        self._debug_win=PanelDebug(self)


if __name__=="__main__":
    app=AuraDashboard(); app.mainloop()
