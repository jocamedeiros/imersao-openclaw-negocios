#!/usr/bin/env python3
"""
Skill: suporte-vs-vendas
Gera relatório HTML com análise de tickets de suporte vs. vendas e reembolsos
nos últimos N dias (padrão: 7).

Uso:
  python3 gerar_relatorio.py
  python3 gerar_relatorio.py --dias 14
  python3 gerar_relatorio.py --tickets path/to/tickets.csv --vendas path/to/vendas.csv
  python3 gerar_relatorio.py --output relatorio.html
"""

import csv
import argparse
from datetime import date, timedelta, datetime
from collections import defaultdict
from pathlib import Path

# ── Caminhos padrão ──────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE.parent.parent.parent.parent / "wizard-imersao" / "dados-demo"

TICKETS_CSV = DATA_DIR / "tickets-suporte.csv"
VENDAS_CSV  = DATA_DIR / "vendas.csv"
OUTPUT_HTML = Path("/root/.openclaw/workspace-assistente/relatorio-suporte-vs-vendas.html")

# ── Args ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dias",    type=int, default=7)
parser.add_argument("--tickets", type=Path, default=TICKETS_CSV)
parser.add_argument("--vendas",  type=Path, default=VENDAS_CSV)
parser.add_argument("--output",  type=Path, default=OUTPUT_HTML)
args = parser.parse_args()

HOJE      = date.today()
INICIO    = HOJE - timedelta(days=args.dias - 1)

def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()

def in_range(d):
    return INICIO <= d <= HOJE

# ── Carregar dados ────────────────────────────────────────────────────────────
tickets = []
with open(args.tickets, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = parse_date(row["data_abertura"])
        if in_range(d):
            tickets.append({**row, "_date": d})

vendas = []
with open(args.vendas, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        d = parse_date(row["data"])
        if in_range(d):
            vendas.append({**row, "_date": d, "_valor": float(row["valor"])})

reembolsos = [t for t in tickets if t["categoria"] == "reembolso"]
cancelamentos = [t for t in tickets if t["categoria"] == "cancelamento"]
tickets_criticos = [t for t in tickets if t["prioridade"] == "critica"]
tickets_abertos  = [t for t in tickets if t["status"] == "aberto"]

# ── Métricas ──────────────────────────────────────────────────────────────────
receita_total = sum(v["_valor"] for v in vendas if v["status"] == "aprovado")
total_vendas  = len([v for v in vendas if v["status"] == "aprovado"])
total_tickets = len(tickets)

# Volume por dia
vendas_por_dia  = defaultdict(lambda: {"receita": 0.0, "qtd": 0})
tickets_por_dia = defaultdict(int)
for v in vendas:
    if v["status"] == "aprovado":
        vendas_por_dia[v["_date"]]["receita"] += v["_valor"]
        vendas_por_dia[v["_date"]]["qtd"] += 1
for t in tickets:
    tickets_por_dia[t["_date"]] += 1

# Tickets por produto
tickets_por_produto = defaultdict(int)
for t in tickets:
    tickets_por_produto[t["produto"]] += 1

# Tickets por categoria
tickets_por_categoria = defaultdict(int)
for t in tickets:
    tickets_por_categoria[t["categoria"]] += 1

# Tickets por produto × categoria
produto_categoria = defaultdict(lambda: defaultdict(int))
for t in tickets:
    produto_categoria[t["produto"]][t["categoria"]] += 1

# Vendas por produto
vendas_por_produto = defaultdict(lambda: {"receita": 0.0, "qtd": 0})
for v in vendas:
    if v["status"] == "aprovado":
        vendas_por_produto[v["produto"]]["receita"] += v["_valor"]
        vendas_por_produto[v["produto"]]["qtd"] += 1

# Ticket rate por produto (tickets / vendas)
all_produtos = sorted(set(list(tickets_por_produto.keys()) + list(vendas_por_produto.keys())))

# Tempo médio de resolução
tempos = [int(t["tempo_resolucao_horas"]) for t in tickets if t["status"] == "resolvido" and int(t["tempo_resolucao_horas"]) > 0]
tempo_medio = round(sum(tempos) / len(tempos), 1) if tempos else 0

# Dias ordenados
all_days = sorted(set(list(vendas_por_dia.keys()) + list(tickets_por_dia.keys())))
labels_dias = [d.strftime("%d/%m") for d in all_days]
series_receita = [vendas_por_dia[d]["receita"] for d in all_days]
series_tickets = [tickets_por_dia[d] for d in all_days]

# Insights automáticos
insights = []

reembolso_rate = len(reembolsos) / total_vendas * 100 if total_vendas else 0
if reembolso_rate > 15:
    insights.append(("danger", "⚠️ Alta taxa de reembolso",
        f"{len(reembolsos)} reembolsos em {total_vendas} vendas ({reembolso_rate:.0f}%). Investigar motivos com urgência."))
elif reembolso_rate > 5:
    insights.append(("warning", "📊 Taxa de reembolso elevada",
        f"{len(reembolsos)} reembolsos ({reembolso_rate:.0f}%). Monitorar tendência."))
else:
    insights.append(("success", "✅ Taxa de reembolso saudável",
        f"Apenas {len(reembolsos)} reembolsos ({reembolso_rate:.0f}%) no período."))

if tickets_abertos:
    prods_abertos = defaultdict(int)
    for t in tickets_abertos:
        prods_abertos[t["produto"]] += 1
    top = max(prods_abertos, key=prods_abertos.get)
    insights.append(("warning", "🔓 Tickets sem resolução",
        f"{len(tickets_abertos)} tickets em aberto. Produto mais afetado: {top} ({prods_abertos[top]} abertos)."))

if cancelamentos:
    produtos_cancel = defaultdict(int)
    for t in cancelamentos:
        produtos_cancel[t["produto"]] += 1
    top_c = max(produtos_cancel, key=produtos_cancel.get)
    insights.append(("danger", "🚨 Cancelamentos no período",
        f"{len(cancelamentos)} pedidos de cancelamento. Produto: {top_c}."))

top_ticket_produto = max(tickets_por_produto, key=tickets_por_produto.get) if tickets_por_produto else None
if top_ticket_produto:
    qtd = tickets_por_produto[top_ticket_produto]
    ratio = qtd / total_tickets * 100
    if ratio > 40:
        insights.append(("warning", f"📦 {top_ticket_produto} concentra {ratio:.0f}% dos tickets",
            f"{qtd} de {total_tickets} tickets no período. Pode indicar problema sistêmico."))

top_categoria = max(tickets_por_categoria, key=tickets_por_categoria.get) if tickets_por_categoria else None
if top_categoria:
    insights.append(("info", f"🏷️ Categoria dominante: {top_categoria}",
        f"{tickets_por_categoria[top_categoria]} tickets ({tickets_por_categoria[top_categoria]/total_tickets*100:.0f}% do total). Avaliar se é recorrente."))

# Correlação diária: dia com mais tickets teve queda de receita?
if len(all_days) >= 3:
    dia_mais_ticket = max(all_days, key=lambda d: tickets_por_dia[d])
    label_dia = dia_mais_ticket.strftime("%d/%m")
    rec_dia = vendas_por_dia[dia_mais_ticket]["receita"]
    avg_receita = sum(series_receita) / len(series_receita) if series_receita else 0
    if rec_dia < avg_receita * 0.7:
        insights.append(("danger", f"📉 Correlação negativa em {label_dia}",
            f"Pico de tickets coincidiu com receita R$ {rec_dia:,.0f} — abaixo da média diária (R$ {avg_receita:,.0f})."))

# ── HTML ──────────────────────────────────────────────────────────────────────
BADGE = {"danger": "#ef4444", "warning": "#f59e0b", "success": "#22c55e", "info": "#3b82f6"}
BADGE_BG = {"danger": "#fef2f2", "warning": "#fffbeb", "success": "#f0fdf4", "info": "#eff6ff"}

CATEGORIAS_ALL = sorted(tickets_por_categoria.keys())

def pct_bar(val, maxi, color="#6366f1"):
    pct = val / maxi * 100 if maxi else 0
    return f'<div style="background:#e5e7eb;border-radius:4px;height:8px;width:100%"><div style="background:{color};border-radius:4px;height:8px;width:{pct:.1f}%"></div></div>'

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Suporte vs. Vendas — Últimos {args.dias} dias</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;color:#1e293b;padding:0}}
  .header{{background:linear-gradient(135deg,#1e293b 0%,#334155 100%);color:#fff;padding:32px 40px}}
  .header h1{{font-size:1.6rem;font-weight:700;margin-bottom:4px}}
  .header .sub{{color:#94a3b8;font-size:.9rem}}
  .container{{max-width:1100px;margin:0 auto;padding:28px 24px}}
  .kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:28px}}
  .kpi{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;text-align:center}}
  .kpi .num{{font-size:2rem;font-weight:700;line-height:1}}
  .kpi .lbl{{font-size:.78rem;color:#64748b;margin-top:6px}}
  .kpi.red .num{{color:#ef4444}}
  .kpi.amber .num{{color:#f59e0b}}
  .kpi.green .num{{color:#22c55e}}
  .kpi.blue .num{{color:#3b82f6}}
  .card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:20px}}
  .card h2{{font-size:1rem;font-weight:600;margin-bottom:16px;color:#374151}}
  .insight{{border-left:4px solid;border-radius:8px;padding:12px 16px;margin-bottom:10px}}
  .insight .title{{font-weight:600;font-size:.9rem;margin-bottom:2px}}
  .insight .body{{font-size:.83rem;color:#374151}}
  table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  th{{background:#f1f5f9;text-align:left;padding:8px 12px;font-weight:600;color:#374151;border-bottom:2px solid #e2e8f0}}
  td{{padding:8px 12px;border-bottom:1px solid #f1f5f9}}
  tr:hover td{{background:#f8fafc}}
  .tag{{display:inline-block;font-size:.72rem;padding:2px 8px;border-radius:20px;font-weight:600}}
  .tag-critica{{background:#fee2e2;color:#dc2626}}
  .tag-alta{{background:#fef3c7;color:#d97706}}
  .tag-media{{background:#dbeafe;color:#2563eb}}
  .tag-baixa{{background:#f0fdf4;color:#16a34a}}
  .tag-aberto{{background:#fee2e2;color:#dc2626}}
  .tag-resolvido{{background:#f0fdf4;color:#16a34a}}
  .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
  @media(max-width:640px){{.two-col{{grid-template-columns:1fr}}}}
  .footer{{text-align:center;color:#94a3b8;font-size:.75rem;padding:24px;margin-top:8px}}
</style>
</head>
<body>

<div class="header">
  <h1>📊 Suporte vs. Vendas</h1>
  <div class="sub">Período: {INICIO.strftime('%d/%m/%Y')} → {HOJE.strftime('%d/%m/%Y')} &nbsp;·&nbsp; Gerado em {HOJE.strftime('%d/%m/%Y')}</div>
</div>

<div class="container">

  <!-- KPIs -->
  <div class="kpi-row">
    <div class="kpi green"><div class="num">R$ {receita_total:,.0f}</div><div class="lbl">Receita no período</div></div>
    <div class="kpi blue"><div class="num">{total_vendas}</div><div class="lbl">Vendas aprovadas</div></div>
    <div class="kpi amber"><div class="num">{total_tickets}</div><div class="lbl">Tickets abertos</div></div>
    <div class="kpi red"><div class="num">{len(reembolsos)}</div><div class="lbl">Reembolsos</div></div>
    <div class="kpi red"><div class="num">{len(cancelamentos)}</div><div class="lbl">Cancelamentos</div></div>
    <div class="kpi {'amber' if tempo_medio > 6 else 'green'}"><div class="num">{tempo_medio}h</div><div class="lbl">Tempo médio resolução</div></div>
  </div>

  <!-- Insights -->
  <div class="card">
    <h2>🔍 Insights Automáticos</h2>
    {''.join(f"""<div class="insight" style="border-color:{BADGE[i[0]]};background:{BADGE_BG[i[0]]}">
      <div class="title" style="color:{BADGE[i[0]]}">{i[1]}</div>
      <div class="body">{i[2]}</div>
    </div>""" for i in insights)}
  </div>

  <!-- Gráfico dual -->
  <div class="card">
    <h2>📈 Receita × Volume de Tickets por Dia</h2>
    <canvas id="chartDual" height="80"></canvas>
  </div>

  <!-- Duas colunas -->
  <div class="two-col">
    <!-- Tickets por produto -->
    <div class="card">
      <h2>📦 Tickets por Produto</h2>
      <table>
        <thead><tr><th>Produto</th><th>Tickets</th><th>Vendas</th><th>Ticket Rate</th></tr></thead>
        <tbody>
        {''.join(f"""<tr>
          <td>{p}</td>
          <td>{tickets_por_produto.get(p,0)}</td>
          <td>{vendas_por_produto.get(p,{}).get('qtd',0)}</td>
          <td>{'%.0f%%' % (tickets_por_produto.get(p,0)/vendas_por_produto.get(p,{'qtd':1})['qtd']*100) if vendas_por_produto.get(p,{}).get('qtd',0) else '—'}</td>
        </tr>""" for p in all_produtos)}
        </tbody>
      </table>
    </div>

    <!-- Tickets por categoria -->
    <div class="card">
      <h2>🏷️ Tickets por Categoria</h2>
      {''.join(f"""<div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
          <span style="font-size:.85rem">{cat}</span>
          <span style="font-size:.85rem;font-weight:600">{cnt}</span>
        </div>
        {pct_bar(cnt, total_tickets)}
      </div>""" for cat, cnt in sorted(tickets_por_categoria.items(), key=lambda x: -x[1]))}
    </div>
  </div>

  <!-- Tabela de tickets críticos/abertos -->
  <div class="card">
    <h2>🚨 Tickets Críticos e Em Aberto</h2>
    <table>
      <thead><tr><th>Data</th><th>Cliente</th><th>Produto</th><th>Categoria</th><th>Prioridade</th><th>Status</th></tr></thead>
      <tbody>
      {''.join(f"""<tr>
        <td>{t['data_abertura']}</td>
        <td>{t['cliente']}</td>
        <td>{t['produto']}</td>
        <td>{t['categoria']}</td>
        <td><span class="tag tag-{t['prioridade']}">{t['prioridade']}</span></td>
        <td><span class="tag tag-{t['status']}">{t['status']}</span></td>
      </tr>""" for t in sorted(tickets_criticos + [t for t in tickets_abertos if t not in tickets_criticos], key=lambda x: x['_date'], reverse=True))}
      </tbody>
    </table>
  </div>

  <!-- Produto × Categoria (heatmap simples) -->
  <div class="card">
    <h2>🔥 Tipo de Problema por Produto</h2>
    <table>
      <thead><tr><th>Produto</th>{''.join(f'<th style="text-align:center">{c}</th>' for c in CATEGORIAS_ALL)}<th>Total</th></tr></thead>
      <tbody>
      {''.join(f"""<tr>
        <td style="font-weight:500">{p}</td>
        {''.join(f'<td style="text-align:center;color:{"#ef4444" if produto_categoria[p][c]>=3 else "#f59e0b" if produto_categoria[p][c]>=2 else "#374151"};font-weight:{"700" if produto_categoria[p][c]>=2 else "400"}">{produto_categoria[p][c] or "—"}</td>' for c in CATEGORIAS_ALL)}
        <td style="font-weight:600">{tickets_por_produto.get(p,0)}</td>
      </tr>""" for p in all_produtos)}
      </tbody>
    </table>
  </div>

</div>

<div class="footer">Empresa Exemplo · Gerado automaticamente pelo Assistente · {HOJE.strftime('%d/%m/%Y')}</div>

<script>
const ctx = document.getElementById('chartDual').getContext('2d');
new Chart(ctx, {{
  data: {{
    labels: {labels_dias},
    datasets: [
      {{
        type: 'bar',
        label: 'Receita (R$)',
        data: {series_receita},
        backgroundColor: 'rgba(99,102,241,0.2)',
        borderColor: '#6366f1',
        borderWidth: 2,
        yAxisID: 'y',
        borderRadius: 4
      }},
      {{
        type: 'line',
        label: 'Tickets',
        data: {series_tickets},
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239,68,68,0.1)',
        tension: 0.3,
        yAxisID: 'y2',
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: '#ef4444'
      }}
    ]
  }},
  options: {{
    responsive: true,
    interaction: {{mode:'index',intersect:false}},
    plugins: {{legend: {{position:'top'}}}},
    scales: {{
      y: {{position:'left',title:{{display:true,text:'Receita (R$)'}},ticks:{{callback:v=>'R$'+v.toLocaleString('pt-BR')}}}},
      y2: {{position:'right',title:{{display:true,text:'Tickets'}},grid:{{drawOnChartArea:false}},ticks:{{stepSize:1}}}}
    }}
  }}
}});
</script>
</body>
</html>"""

args.output.write_text(html, encoding="utf-8")
print(f"✅ Relatório gerado: {args.output}")
print(f"   Período: {INICIO} → {HOJE}")
print(f"   Tickets: {total_tickets} | Vendas: {total_vendas} | Reembolsos: {len(reembolsos)}")
