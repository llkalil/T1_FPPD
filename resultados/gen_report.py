"""Gera relatorio_t1.pdf a partir de c8g.16xlarge/summary.csv + arquivos crus.  Uso: python gen_report.py"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle, KeepTogether)

D = Path(__file__).parent
R = D / "c8g.16xlarge"
F = Path("C:/Windows/Fonts")
for name, f in [("A", "arial.ttf"), ("A-B", "arialbd.ttf"), ("A-I", "ariali.ttf"), ("M", "consola.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(F / f)))
pdfmetrics.registerFontFamily("A", normal="A", bold="A-B", italic="A-I", boldItalic="A-B")

rows = list(csv.DictReader((R / "summary.csv").open(encoding="utf-8")))
S = {(r["versao"], int(r["n"])): r for r in rows}
NS = [5, 48, 96]
VS = ["V0", "V1", "V2", "V3"]
env = (R / "env.txt").read_text(encoding="utf-8")

# ---------- gráficos ----------
col = {"V0": "#7f7f7f", "V2": "#d62728", "V3": "#2ca02c"}
lab = {"V0": "V0 sequencial", "V2": "V2 mutex global", "V3": "V3 garfos ordenados"}
fig, ax = plt.subplots(1, 3, figsize=(10.5, 4.3))
w = 0.26
def bars(a, vs, key, scale, fmt):
    for i, v in enumerate(vs):
        xs = [j + (i - (len(vs) - 1) / 2) * w for j in range(3)]
        ys = [float(S[(v, n)][key]) * scale for n in NS]
        a.bar(xs, ys, w, label=lab[v], color=col[v])
        for xx, yy in zip(xs, ys):
            a.text(xx, yy * 1.08 if a.get_yscale() == "log" else yy + 0.6, fmt(yy), ha="center", va="bottom", fontsize=6.5)
ax[0].set_yscale("log"); ax[1].set_yscale("log")
bars(ax[0], ["V0", "V2", "V3"], "total_ms_media", 1 / 1000, lambda y: f"{y:.1f}")
bars(ax[1], ["V2", "V3"], "espera_media_ms", 1, lambda y: f"{y:.0f}" if y >= 10 else f"{y:.1f}")
bars(ax[2], ["V0", "V2", "V3"], "max_comendo", 1, lambda y: f"{y:.0f}")
ax[0].set_ylim(0.3, 120); ax[1].set_ylim(1, 3000); ax[2].set_ylim(0, 52)
for a, t in zip(ax, ["Tempo total (s) — escala log", "Espera média pelos garfos (ms) — escala log", "Máx. filósofos comendo ao mesmo tempo"]):
    a.set_title(t, fontsize=8.5); a.set_xticks(range(3)); a.set_xticklabels([f"N={n}" for n in NS], fontsize=8)
    a.tick_params(axis="y", labelsize=8); a.grid(axis="y", alpha=.3); a.set_axisbelow(True)
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(D / "graficos.png", dpi=170)

# figura 2: comparação de vCPUs (V3, onde há diferença; V0/V2 são idênticas)
MS_ = {(r["versao"], int(r["n"])): r for r in csv.DictReader((D / "c8g.medium" / "summary.csv").open(encoding="utf-8"))}
fig2, bx = plt.subplots(1, 3, figsize=(10.5, 3.2))
for a, key, ttl, fmt in [(bx[0], "total_ms_media", "V3 — tempo total (ms)", "{:.0f}"), (bx[1], "espera_media_ms", "V3 — espera média (ms)", "{:.1f}"),
                         (bx[2], "max_comendo", "V3 — máx. comendo juntos", "{:.0f}")]:
    for i, (lbl, src, c) in enumerate([("c8g.medium (1 vCPU)", MS_, "#1f77b4"), ("c8g.16xlarge (64 vCPUs)", S, "#ff7f0e")]):
        xs = [j + (i - .5) * .36 for j in range(3)]
        ys = [float(src[("V3", n)][key]) for n in NS]
        a.bar(xs, ys, .36, color=c, label=lbl)
        for xx, yy in zip(xs, ys):
            a.text(xx, yy, fmt.format(yy), ha="center", va="bottom", fontsize=6.5)
    a.set_title(ttl, fontsize=8.5); a.set_xticks(range(3)); a.set_xticklabels([f"N={n}" for n in NS], fontsize=8)
    a.tick_params(axis="y", labelsize=8); a.grid(axis="y", alpha=.3); a.set_axisbelow(True)
    a.margins(y=.15)
h2_, l2_ = bx[0].get_legend_handles_labels()
fig2.legend(h2_, l2_, loc="lower center", ncol=2, fontsize=8, frameon=False)
fig2.tight_layout(rect=(0, 0.07, 1, 1))
fig2.savefig(D / "graficos_vcpus.png", dpi=170)

# ---------- estilos ----------
def st(name, size, lead, **kw):
    return ParagraphStyle(name, fontName=kw.pop("fontName", "A"), fontSize=size, leading=lead, **kw)
H1 = st("h1", 13, 16, fontName="A-B", spaceAfter=3)
H2 = st("h2", 10.5, 13, fontName="A-B", spaceBefore=5, spaceAfter=2, textColor=colors.HexColor("#1f3b73"))
B = st("b", 9.2, 11.6, spaceAfter=2.5, alignment=4)
BL = st("bl", 9.2, 11.6, leftIndent=9, bulletIndent=0, spaceAfter=1.5, alignment=4)
C = st("c", 9.3, 12, spaceAfter=4, alignment=4)
CL = st("cl", 9.3, 12, leftIndent=12, bulletIndent=0, spaceAfter=2, alignment=4)
SM = st("sm", 7, 8.4, textColor=colors.HexColor("#444444"))
MONO = ParagraphStyle("mono", fontName="M", fontSize=7.2, leading=8.8)

def p(t): return Paragraph(t, B)
def bl(t): return Paragraph(t, BL, bulletText="•")
def cp(t): return Paragraph(t, C)
def cb(t): return Paragraph(t, CL, bulletText="•")

def box(text, bg="#101418", fg="#d8dee9"):
    t = Table([[Preformatted(text, ParagraphStyle("m2", parent=MONO, textColor=colors.HexColor(fg)))]], colWidths=[17.4 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t

def x(v, n, k): return S[(v, n)][k]
def ratio(a, b, n): return float(x(a, n, "total_ms_media")) / float(x(b, n, "total_ms_media"))

# ---------- página 1 ----------
s = []
s.append(Paragraph("Trabalho 1 — Concorrência e Sincronização: O Problema dos Filósofos Jantando", H1))
s.append(p("<b>Grupo:</b> Lorenzo Kalil · Mateus Huster · [3º integrante a definir] &nbsp;|&nbsp; "
           "<b>Disciplina:</b> Fundamentos de Programação Paralela e Distribuída (PUCRS) &nbsp;|&nbsp; "
           "<b>Código-fonte (Git):</b> https://github.com/llkalil/T1_FPPD"))
s.append(Paragraph("Soluções, mecanismos de sincronização e como são implementados em Go", H2))
s.append(p("Cinco (ou N) filósofos, um garfo entre cada par. O filósofo <i>i</i> usa os garfos <i>i</i> (esquerdo) e <i>(i+1) mod N</i> (direito). "
           "Cada garfo é um <font name='M'>sync.Mutex</font> (<font name='M'>Lock/Unlock</font>: exclusão mútua, sem preempção e não reentrante); "
           "cada filósofo é uma goroutine e <font name='M'>sync.WaitGroup</font> aguarda o fim. Pensar/comer é <font name='M'>time.Sleep</font> "
           "(10 ms cada), igual em todas as versões, e as métricas usam <font name='M'>sync/atomic</font> (contador de filósofos comendo, com máximo via CAS) "
           "e medição por filósofo do tempo entre o fim de pensar e a posse dos dois garfos. Um <i>watchdog</i> declara deadlock se nenhum ciclo "
           "termina por 5 s e imprime quem segura e quem espera cada garfo (o detector nativo do runtime não dispara porque há timers ativos)."))
s.append(bl("<b>V0 — sequencial (baseline):</b> um filósofo por vez, sem goroutines nem garfos; o tempo esperado é N × 20 × (10+10) ms."))
s.append(bl("<b>V1 — deadlock:</b> todos pegam primeiro o garfo esquerdo e depois o direito, com pausa de 1 ms entre os dois "
            "(<font name='M'>-gap</font>, só nesta versão) para tornar o deadlock provável. Se todos seguram o esquerdo, ninguém avança."))
s.append(bl("<b>V2 — sincronização excessiva:</b> um mutex global é adquirido antes dos garfos e só liberado depois de comer. "
            "Correta e sem deadlock, mas serializa a mesa inteira: só um filósofo come por vez, mesmo havendo garfos livres."))
s.append(bl("<b>V3 — aprimorada:</b> <i>hierarquia de recursos</i>: cada filósofo pega sempre o garfo de menor índice primeiro. "
            "O último filósofo (N−1) inverte a ordem (garfo 0 antes do N−1), o que quebra a espera circular; vizinhos não conflitantes comem em paralelo."))
s.append(Paragraph("V1: por que ocorre deadlock (as 4 condições de Coffman)", H2))
s.append(p("<b>Exclusão mútua:</b> um garfo (Mutex) só tem um dono. <b>Segura-e-espera:</b> cada filósofo segura o garfo <i>i</i> e espera o <i>i+1</i>. "
           "<b>Ausência de preempção:</b> o Mutex não pode ser tomado à força. <b>Espera circular:</b> 0→1→2→3→4→0 (o filósofo <i>i</i> espera o garfo em posse do <i>i+1</i>). "
           "Com as quatro presentes o sistema trava: cada filósofo tem <b>1 garfo</b> (o esquerdo) e espera <b>1</b> (o direito, do vizinho); ver captura na página 2."))
s.append(Paragraph("Como V2 e V3 evitam o deadlock; starvation", H2))
s.append(p("<b>V2</b> nega <i>segura-e-espera/espera circular</i>: só quem tem o mutex global pede garfos, e como ninguém mais os segura eles sempre estão livres. "
           "<b>V3</b> nega a <i>espera circular</i>: ordenando os recursos, a cadeia de esperas é sempre crescente e não fecha um ciclo. "
           "<b>Starvation:</b> em V2 e V3 o <font name='M'>sync.Mutex</font> do Go entra em modo de inanição após 1 ms de espera (entrega direta em FIFO ao mais antigo), "
           "o que limita a espera de cada goroutine; observamos todos os filósofos concluindo os 20 ciclos em todas as execuções. Em teoria a V3 sozinha, "
           "com escalonamento arbitrário, não garante justiça; aqui ela vem do mutex."))
s.append(Paragraph("Ambiente de execução", H2))
s.append(p("AWS EC2 <b>c8g.16xlarge</b> (spot, us-east-1b): AWS Graviton4, <b>64 vCPUs</b> (1 thread/core), Amazon Linux 2023 (kernel 6.18, aarch64), "
           "<b>Go 1.26.8 linux/arm64</b>. Compilação: <font name='M'>go build -o filosofos .</font> · Execução: "
           "<font name='M'>NS=\"5 48 96\" RUNS=5 ./run.sh</font> (V1: 10 execuções por N; individual: <font name='M'>./filosofos -v 3 -n 96 -csv</font>). "
           "20 ciclos por filósofo, pensar = comer = 10 ms, 5 execuções por versão e N (o enunciado pede N=5; N=48 e 96 foram acrescentados para ver a escala). "
           "Como pensar/comer são <i>sleep</i>, o resultado não depende do número de cores (tentamos a c8g.48xlarge/24xlarge, sem capacidade spot)."))
s.append(Paragraph("Visão geral das versões", H2))
ov = [["Versão", "Sincronização", "Deadlock?", "Máx. comendo (N=5/48/96)", "Total N=96"],
      ["V0", "nenhuma (sequencial)", "não", "1 / 1 / 1", f"{float(x('V0',96,'total_ms_media'))/1000:.1f} s"],
      ["V1", "1 mutex por garfo, esq→dir", "sim (30/30)", "0", "não termina"],
      ["V2", "mutex global + garfos", "não", "1 / 1 / 1", f"{float(x('V2',96,'total_ms_media'))/1000:.1f} s"],
      ["V3", "garfos ordenados (menor índice 1º)", "não", f"{x('V3',5,'max_comendo')} / {x('V3',48,'max_comendo')} / {x('V3',96,'max_comendo')}", f"{float(x('V3',96,'total_ms_media'))/1000:.2f} s"]]
ot = Table(ov, colWidths=[1.5 * cm, 6.2 * cm, 2.6 * cm, 4.1 * cm, 3 * cm])
ot.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "A", 8.3), ("FONT", (0, 0), (-1, 0), "A-B", 8.3),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe6f3")), ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                        ("ALIGN", (2, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
s.append(ot)
s.append(Paragraph("Análise comparativa (resumo)", H2))
s.append(p(f"V3 é a melhor: com N=96 leva {float(x('V3',96,'total_ms_media'))/1000:.2f} s contra {float(x('V2',96,'total_ms_media'))/1000:.1f} s da V2 "
           f"({ratio('V2','V3',96):.0f}× mais lenta) e {float(x('V0',96,'total_ms_media'))/1000:.1f} s da V0 ({ratio('V0','V3',96):.0f}×), com até {x('V3',96,'max_comendo')} filósofos comendo em paralelo. "
           f"V2 é correta, mas só ganha ~{ratio('V0','V2',96):.1f}× sobre a V0 (sobrepõe apenas o pensar) e a espera média cresce com N ({x('V2',5,'espera_media_ms')} → {x('V2',96,'espera_media_ms')} ms). "
           "V1 travou em 30 de 30 execuções. Repetido na c8g.medium (1 vCPU), V0/V2/V1 deram o mesmo resultado e a V3 foi 17–18% mais rápida com N≥48: o número de vCPUs quase não importa (página 3)."))
s.append(PageBreak())

# ---------- página 2 ----------
s.append(Paragraph("Resultados experimentais", H1))
HN = "\n"
hdr = ["Versão", "N", "Exec." + HN + "(ok/dead)", "Total médio" + HN + "(ms)", "Desvio" + HN + "(ms)", "Mín–Máx" + HN + "(ms)",
       "Espera média" + HN + "(ms)", "Maior espera" + HN + "(ms)", "Máx." + HN + "comendo", "Ciclos/" + HN + "filósofo"]
data = [hdr]
for v in VS:
    for n in NS:
        r = S[(v, n)]
        if v == "V1":
            data.append([v, n, f"0/{r['deadlocks']}", "deadlock", "-", "-", "-", "-", "-", "parcial: 0"])
        else:
            data.append([v, n, f"{r['ok']}/{r['deadlocks']}", r["total_ms_media"], r["total_ms_dp"], f"{r['total_ms_min']}–{r['total_ms_max']}",
                         r["espera_media_ms"], r["espera_max_ms_pior"], r["max_comendo"], f"{r['ciclos_min']}–{r['ciclos_max']}"])
t = Table(data, repeatRows=1, colWidths=[1.3, .9, 1.9, 2.1, 1.2, 2.9, 1.9, 1.9, 1.6, 1.8])
t._argW = [c * cm for c in [1.3, .9, 1.9, 2.1, 1.2, 2.9, 1.9, 1.9, 1.6, 1.8]]
t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "A", 7.2), ("FONT", (0, 0), (-1, 0), "A-B", 7.2),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe6f3")), ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                       ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                       ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                       ("BACKGROUND", (0, 4), (-1, 6), colors.HexColor("#fbe3e3")),
                       ("BACKGROUND", (0, 10), (-1, 12), colors.HexColor("#e3f3e3"))]))
s.append(t)
s.append(Paragraph("Tabela 1 — Médias sobre as execuções concluídas (c8g.16xlarge, 20 ciclos, pensar=comer=10 ms). Dados crus: <font name='M'>c8g.16xlarge/results.csv</font>. "
                   "Na V1 o “tempo” medido seria só o do watchdog (5,1 s) e não é comparável.", SM))
s.append(Spacer(1, 4))
s.append(Image(str(D / "graficos.png"), width=17.4 * cm, height=17.4 * cm * 4.3 / 10.5))
s.append(Paragraph("Figura 1 — Comparação por versão e N (barras: média das 5 execuções).", SM))
s.append(Spacer(1, 4))
dl = (R / "deadlock_n5.txt").read_text(encoding="utf-8").strip()
csvl = [l for l in (R / "results.csv").read_text(encoding="utf-8").splitlines()]
def one(v, n): return next(l for l in csvl if l.startswith(f"{v},{n},"))
def trunc(l): return l if len(l) <= 96 else l[:93] + "..."
s.append(Paragraph("<b>Captura 1 — V1 em deadlock</b> (saída real do terminal, <font name='M'>./filosofos -v 1 -n 5</font>)", B))
s.append(box("$ ./filosofos -v 1 -n 5" + chr(10) + dl))
s.append(Spacer(1, 4))
s.append(Paragraph("<b>Captura 2 — linhas reais do <font name='M'>results.csv</font></b> (versao, n, status, total_ms, espera_media_ms, espera_max_ms, max_comendo, ciclos)", B))
s.append(box(chr(10).join(trunc(one(v, n)) for v, n in [("V2", 96), ("V3", 96)])))
s.append(PageBreak())

# ---------- conclusão ----------
s.append(Paragraph("Conclusão e análise dos resultados", H1))
q = lambda n, t: s.append(cp(f"<b>{n}.</b> {t}"))
q(1, "<b>Como funciona cada solução.</b> V0 executa os filósofos em sequência (baseline). V1 pega esquerdo e depois direito e trava. "
     "V2 envolve pegar-comer-soltar num mutex global. V3 impõe ordem global de aquisição dos garfos (menor índice primeiro).")
q(2, "<b>Mecanismos.</b> Exclusão mútua por <font name='M'>sync.Mutex</font> (um por garfo, mais um global na V2), <font name='M'>WaitGroup</font> para juntar goroutines, "
     "<font name='M'>atomic</font> para contadores e um watchdog para detectar deadlock. Nenhum canal foi necessário.")
q(3, "<b>Implementação em Go.</b> Mutex do runtime (sem preempção, não reentrante) sobre semáforos; goroutines escalonadas em até 64 threads do SO (GOMAXPROCS = 64); "
     "<font name='M'>time.Sleep</font> simula pensar/comer sem consumir CPU, por isso o desempenho é dominado pela <i>estrutura de sincronização</i>, não pelo número de cores.")
q(4, "<b>Deadlock na V1.</b> As quatro condições de Coffman ocorrem ao mesmo tempo (página 1). A evidência coletada é o estado de cada filósofo no travamento: "
     "todos com 1 garfo (o esquerdo) esperando o direito, formando o ciclo 0→1→…→N−1→0, com 0 ciclos concluídos. Travou em <b>30 de 30</b> execuções "
     "(N=5, 48 e 96). O <i>gap</i> de 1 ms entre os dois garfos alinha os filósofos e torna isso quase certo; em testes locais preliminares (outra máquina, sem controle) "
     "algumas execuções chegaram a terminar, ou seja, o deadlock depende de timing. Sem o gap não medimos a probabilidade.")
q(5, "<b>Como V2 e V3 evitam.</b> V2 impede <i>segura-e-espera</i> e a espera circular (um só filósofo por vez disputa garfos). V3 impede a espera circular pela ordenação: "
     "como o último filósofo pega o garfo 0 antes do N−1, não existe ciclo de dependências. Ambas concluíram 100% das execuções (V2: 15/15, V3: 15/15).")
q(6, f"<b>Starvation.</b> Em teoria a V3 usa só ordenação e não garante justiça, e a V2 depende da fila do mutex global. Na prática o modo de inanição do <font name='M'>sync.Mutex</font> (1 ms) faz a espera ser limitada. "
     f"Medimos isso: todos os filósofos fizeram exatamente 20 ciclos em todas as execuções, e a maior espera foi {x('V2',96,'espera_max_ms_pior')} ms na V2 (≈ N×10 ms = 960 ms: cada um espera a fila inteira comer) e "
     f"{x('V3',96,'espera_max_ms_pior')} ms na V3 (~5 tempos de comer). Não observamos starvation; a V1 não se aplica, pois trava antes.")
q(7, f"<b>Maior tempo total.</b> Entre as que terminam, a <b>V0</b> (N=96: {float(x('V0',96,'total_ms_media'))/1000:.1f} s; N=48: {float(x('V0',48,'total_ms_media'))/1000:.1f} s; N=5: {float(x('V0',5,'total_ms_media'))/1000:.2f} s), "
     "que coincide com o previsto N×20×20 ms. A V1 não termina (tempo infinito).")
q(8, f"<b>Maior tempo de espera.</b> A <b>V2</b>: média de {x('V2',5,'espera_media_ms')} ms (N=5), {x('V2',48,'espera_media_ms')} ms (N=48) e {x('V2',96,'espera_media_ms')} ms (N=96), crescendo linearmente com N, "
     f"contra {x('V3',5,'espera_media_ms')}–{x('V3',96,'espera_media_ms')} ms na V3 e ~0 na V0 (não há disputa). Na V1 a espera é infinita.")
q(9, f"<b>Filósofos comendo simultaneamente.</b> V0: 1. V2: 1 (mesmo com garfos livres). V3: {x('V3',5,'max_comendo')} (N=5), {x('V3',48,'max_comendo')} (N=48) e {x('V3',96,'max_comendo')} (N=96), "
     "próximo do teto teórico N/2 = 2, 24 e 48 (arredondando para baixo). V1: 0 (ninguém chega a comer).")
q(10, f"<b>Impacto da sincronização excessiva (V2).</b> A V2 só é ~{ratio('V0','V2',96):.1f}× melhor que a V0: o mutex global já permite sobrepor o <i>pensar</i> de uns com o comer de outro, mas serializa o comer. "
      f"Frente à V3 ela é {ratio('V2','V3',5):.1f}× mais lenta com N=5, {ratio('V2','V3',48):.0f}× com N=48 e {ratio('V2','V3',96):.0f}× com N=96 — o custo cresce com N porque a V3 mantém o tempo quase constante e a V2 cresce linearmente.")
q(11, "<b>Mais sincronização = melhor desempenho?</b> Não. A V2 é a que mais sincroniza (mutex global <i>além</i> dos garfos) e foi a pior das corretas, com maior espera e concorrência 1. "
      "A V3 usa a <i>mesma</i> quantidade de locks de garfo, mas sem o ponto de serialização, e teve o menor tempo total e a menor espera. Importa <i>onde</i> se sincroniza (escopo da seção crítica), não quanto. "
      "Também não é mais sincronização o que evita deadlock, e sim a estrutura (ordem) dela.")
q(12, "<b>Grau de concorrência × tempo total.</b> O tempo é aproximadamente T ≈ (trabalho a serializar) ÷ (concorrência efetiva): "
      f"V0 (concorrência 1): T = N×20×20 ms; V2 (o comer é serial, o pensar sobrepõe): T ≈ N×20×10 ms (medido {float(x('V2',96,'total_ms_media'))/1000:.2f} s vs 19,2 s previstos com N=96); "
      f"V3 (concorrência ≈ N/2): T ≈ 20×(pensar+comer) = 400 ms, medido ≈ {float(x('V3',96,'total_ms_media')):.0f} ms (+30%, por disputa de garfos vizinhos e jitter de timers). "
      f"Speedup da V3 sobre a V0: {ratio('V0','V3',5):.1f}× (N=5), {ratio('V0','V3',48):.0f}× (N=48), {ratio('V0','V3',96):.0f}× (N=96), acompanhando o aumento da concorrência observada (2 → 23 → 44).")
M = {(r["versao"], int(r["n"])): r for r in csv.DictReader((D / "c8g.medium" / "summary.csv").open(encoding="utf-8"))}
s.append(Paragraph("Comparação: c8g.medium (1 vCPU) × c8g.16xlarge (64 vCPUs)", H2))
cmp_rows = [["Versão", "N", "Total (ms)\nmedium", "Total (ms)\n16xlarge", "Espera média (ms)\nmedium / 16xl", "Máx. comendo\nmedium / 16xl"]]
for v in ["V0", "V2", "V3"]:
    for n in NS:
        a, b = M[(v, n)], S[(v, n)]
        cmp_rows.append([v, n, a["total_ms_media"], b["total_ms_media"], f"{a['espera_media_ms']} / {b['espera_media_ms']}", f"{a['max_comendo']} / {b['max_comendo']}"])
s.append(Image(str(D / "graficos_vcpus.png"), width=17.4 * cm, height=17.4 * cm * 3.2 / 10.5))
s.append(Paragraph("Figura 2 — Efeito do número de vCPUs na V3 (V0, V2 e V1 não mudam: ver tabela). Barras: média de 5 execuções.", SM))
s.append(Spacer(1, 4))
ct = Table(cmp_rows, repeatRows=1, colWidths=[1.5 * cm, 1 * cm, 2.6 * cm, 2.6 * cm, 4.6 * cm, 3.6 * cm])
ct.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "A", 8), ("FONT", (0, 0), (-1, 0), "A-B", 8),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe6f3")), ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
s.append(ct)
s.append(Spacer(1, 4))
s.append(cp("A medium (1 vCPU, GOMAXPROCS=1) repetiu o mesmo experimento (5 execuções por caso; V1 com 10). "
            "<b>V0 e V2 ficaram idênticos</b> (razão 0,999–1,001): são limitados por <i>sleep</i> e por serialização, não por CPU. "
            "<b>A V1 travou nas 30 execuções também na medium</b>: o deadlock é lógico e não depende de núcleos. "
            f"<b>A V3 foi ~17–18% mais rápida na medium</b> com N=48 e 96 (e ~4% mais lenta com N=5) ({M[('V3',96)]['total_ms_media']} ms contra {x('V3',96,'total_ms_media')} ms com N=96), "
            f"com espera média menor ({M[('V3',96)]['espera_media_ms']} contra {x('V3',96,'espera_media_ms')} ms), desvio-padrão quase zero ({M[('V3',96)]['total_ms_dp']} ms contra {x('V3',96,'total_ms_dp')} ms) "
            f"e concorrência máxima de {M[('V3',96)]['max_comendo']} filósofos (teto 48). Confirmado na seção seguinte (a mesma 16xlarge com GOMAXPROCS=1 reproduz a medium): com um só P, os timers acordam os filósofos em lotes alinhados "
            "e há menos migração/jitter entre threads; na 16xlarge, o escalonamento em 64 threads adiciona atrasos (mais variação). "
            "Conclusão: para esta carga, mais cores <b>não</b> melhoram o desempenho; a estrutura de sincronização é o fator dominante (V2 → V3 = 19–37×), e um núcleo basta."))
import statistics as _st
G = {}
for r in csv.DictReader((D / "gomaxprocs" / "gmp.csv").open(encoding="utf-8")):
    G.setdefault((r["versao"], int(r["n"]), int(r["gomaxprocs"])), []).append(r)
GM = [1, 2, 4, 8, 16, 64]
def gstat(v, n, g, k):
    xs = [float(r[k]) for r in G[(v, n, g)]]
    return _st.mean(xs), (_st.stdev(xs) if len(xs) > 1 else 0.0)
figg, gx = plt.subplots(1, 2, figsize=(10.5, 3.2))
for n, c in [(48, "#1f77b4"), (96, "#2ca02c")]:
    for a, k, ttl in [(gx[0], "total_ms", "V3 — tempo total (ms)"), (gx[1], "espera_media_ms", "V3 — espera média (ms)")]:
        m = [gstat("V3", n, g, k)[0] for g in GM]; e = [gstat("V3", n, g, k)[1] for g in GM]
        a.errorbar(range(len(GM)), m, yerr=e, marker="o", ms=4, capsize=3, color=c, label=f"N={n}")
        a.set_title(ttl, fontsize=8.5); a.set_xticks(range(len(GM))); a.set_xticklabels([str(g) for g in GM], fontsize=8)
        a.set_xlabel("GOMAXPROCS (nº de cores usados pelo runtime)", fontsize=8); a.tick_params(axis="y", labelsize=8)
        a.grid(alpha=.3); a.legend(fontsize=7)
gx[0].set_ylim(0, 620); gx[1].set_ylim(0, 4.5)
figg.tight_layout(); figg.savefig(D / "graficos_gmp.png", dpi=170)
s.append(Paragraph("Isolando o efeito dos cores: GOMAXPROCS na mesma c8g.16xlarge", H2))
s.append(cp("Para separar “número de cores” de “máquina diferente”, repetimos a V3 (N=48 e 96, 5 execuções) e a V2 (N=48, 3 execuções) na <b>mesma</b> 16xlarge variando "
            "<font name='M'>GOMAXPROCS</font> (1, 2, 4, 8, 16, 64). Script: <font name='M'>filosofos/run_gmp.sh</font>; dados: <font name='M'>gomaxprocs/gmp.csv</font>."))
s.append(Image(str(D / "graficos_gmp.png"), width=17.4 * cm, height=17.4 * cm * 3.2 / 10.5))
s.append(Paragraph("Figura 3 — V3: tempo total e espera média × GOMAXPROCS (média ± desvio-padrão).", SM))
grows = [["GOMAXPROCS", "V3 N=48\ntotal (ms) ± dp", "V3 N=48\nespera (ms)", "V3 N=96\ntotal (ms) ± dp", "V3 N=96\nespera (ms)", "V2 N=48\ntotal (ms)"]]
for g in GM:
    a, b = gstat("V3", 48, g, "total_ms"), gstat("V3", 96, g, "total_ms")
    grows.append([g, f"{a[0]:.1f} ± {a[1]:.1f}", f"{gstat('V3',48,g,'espera_media_ms')[0]:.2f}", f"{b[0]:.1f} ± {b[1]:.1f}",
                  f"{gstat('V3',96,g,'espera_media_ms')[0]:.2f}", f"{gstat('V2',48,g,'total_ms')[0]:.0f}"])
gt = Table(grows, repeatRows=1, colWidths=[2.4 * cm, 3.3 * cm, 2.6 * cm, 3.3 * cm, 2.6 * cm, 2.6 * cm])
gt.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "A", 8), ("FONT", (0, 0), (-1, 0), "A-B", 8),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe6f3")), ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
s.append(gt)
s.append(Spacer(1, 4))
s.append(cp(f"<b>Hipótese confirmada:</b> com GOMAXPROCS=1 a 16xlarge dá {gstat('V3',48,1,'total_ms')[0]:.1f} ms (dp {gstat('V3',48,1,'total_ms')[1]:.1f}) com N=48, "
            f"praticamente igual à c8g.medium ({M[('V3',48)]['total_ms_media']} ms). Portanto a divergência <b>não vem da máquina</b>, e sim do número de Ps (processadores lógicos do escalonador do Go). "
            f"Já com 2 Ps o tempo sobe para {gstat('V3',48,2,'total_ms')[0]:.0f} ms e, de 4 até 64, fica num patamar de ~510–540 ms com desvio de 20–45 ms: <b>mais cores não ajudam, passam a atrapalhar</b> "
            "(mais variação e mais espera). Com um só P os timers e o escalonamento são determinísticos e os filósofos ficam em fase; com vários Ps os acordares se espalham e a fase muda a cada execução, "
            "aumentando a disputa entre vizinhos. A causa exata dentro do escalonador não foi investigada (isso exigiria <i>tracing</i>). "
            f"A V2 é insensível: {gstat('V2',48,1,'total_ms')[0]:.0f} ms com 1 P e {gstat('V2',48,64,'total_ms')[0]:.0f} ms com 64 (o mutex global já serializa)."))
s.append(Paragraph("Ressalvas", H2))
s.append(cb("O enunciado usa N=5; N=48 e 96 foram acrescentados para evidenciar a escala. Em N=5 o ganho da V3 sobre a V2 é modesto (1,9×) e a V3 é limitada a 2 comensais."))
s.append(cb("Pensar/comer são simulados com <i>sleep</i>; com trabalho real de CPU, o número de cores passaria a limitar a V3. Desvios-padrão baixos (≤ 31 ms) indicam medidas estáveis; 5 execuções por caso."))
s.append(cb("Medidas de espera incluem a espera pelo mutex global (V2) e pelos dois garfos (V1/V3). A V1 é analisada à parte: as 30 execuções terminaram em deadlock, com evidência em <font name='M'>deadlock_n5/48/96.txt</font>."))
s.append(cb("As “capturas” são a saída textual real do terminal; código completo no repositório indicado na página 1."))

# ---------- apêndices ----------
import textwrap
CODE = ParagraphStyle("code", parent=MONO, fontSize=6, leading=7.2)
def listing(text, width=150):
    out = []
    for l in text.expandtabs(4).splitlines():
        out += textwrap.wrap(l, width, subsequent_indent="      ", drop_whitespace=False, replace_whitespace=False) or [""]
    return Preformatted("\n".join(out), CODE)

def cyc(c):  # resume a coluna de ciclos
    v = c.split(";")
    return f"{v[0]}x{len(v)}" if len(set(v)) == 1 else c

s.append(PageBreak())
s.append(Paragraph("Apêndice A — Ambiente completo", H1))
for name in ["c8g.16xlarge", "c8g.medium"]:
    s.append(Paragraph(name, H2))
    s.append(box((D / name / "env.txt").read_text(encoding="utf-8").strip()))
s.append(Paragraph("Apêndice B — Todas as execuções (dados crus)", H1))
s.append(Paragraph("Colunas: versão, N, status, total (ms), espera média (ms), maior espera (ms), máx. comendo, ciclos por filósofo "
                   "(“20x96” = todos os 96 filósofos com 20 ciclos; na V1 os ciclos são os do momento do deadlock). Arquivos originais: "
                   "<font name='M'>results.csv</font> de cada pasta.", SM))
for name in ["c8g.16xlarge", "c8g.medium"]:
    s.append(Paragraph(f"{name} ({name} / results.csv)", H2))
    lines = ["versao,n,status,total_ms,espera_media_ms,espera_max_ms,max_comendo,ciclos"]
    for l in (D / name / "results.csv").read_text(encoding="utf-8").splitlines()[1:]:
        f = l.split(",")
        lines.append(",".join(f[:7] + [cyc(f[7])]))
    s.append(Preformatted("\n".join(lines), CODE))
s.append(Paragraph("gomaxprocs (gomaxprocs / gmp.csv)", H2))
glines = ["gomaxprocs,versao,n,status,total_ms,espera_media_ms,espera_max_ms,max_comendo,ciclos"]
for l in (D / "gomaxprocs" / "gmp.csv").read_text(encoding="utf-8").splitlines()[1:]:
    f = l.split(",")
    glines.append(",".join(f[:8] + [cyc(f[8])]))
s.append(Preformatted("\n".join(glines), CODE))
s.append(PageBreak())
s.append(Paragraph("Apêndice C — Evidências de deadlock (V1) em N=48 e N=96", H1))
for n in [48, 96]:
    txt = (R / f"deadlock_n{n}.txt").read_text(encoding="utf-8").strip().splitlines()
    head = [l for l in txt if not l.startswith("filósofo")]
    ph = [l for l in txt if l.startswith("filósofo")]
    s.append(Paragraph(f"N={n} (c8g.16xlarge) — {len(ph)} filósofos, todos com 1 garfo e esperando o do vizinho; primeiros 6 e último:", H2))
    s.append(box("\n".join(head + ph[:6] + ["..."] + ph[-1:])))
s.append(Paragraph("Apêndice D — Código-fonte", H1))
s.append(Paragraph("Repositório: https://github.com/llkalil/T1_FPPD", B))
for f in ["filosofos/main.go", "filosofos/run.sh", "filosofos/go.mod"]:
    s.append(Paragraph(f, H2))
    s.append(listing((D.parent / f).read_text(encoding="utf-8")))

def foot(c, d):
    c.saveState(); c.setFont("A", 7); c.setFillColor(colors.grey)
    c.drawRightString(A4[0] - 1.6 * cm, 1 * cm, f"Trabalho 1 — Filósofos Jantando · pág. {d.page}"); c.restoreState()

doc = SimpleDocTemplate(str(D / "relatorio_t1.pdf"), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                        topMargin=1.4 * cm, bottomMargin=1.5 * cm, title="Trabalho 1 - Filósofos Jantando")
doc.build(s, onFirstPage=foot, onLaterPages=foot)
print("ok")
