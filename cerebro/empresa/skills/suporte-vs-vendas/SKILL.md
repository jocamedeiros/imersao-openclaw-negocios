---
name: suporte-vs-vendas
description: |
  Gera relatório HTML cruzando tickets de suporte com vendas e reembolsos. Use quando o usuário pedir análise de suporte vs. vendas, impacto de tickets em receita, relatório de reembolsos, ticket rate por produto, ou insights de atendimento nos últimos N dias. Output: arquivo HTML com KPIs, gráfico dual, tabela de críticos/abertos, heatmap por produto e insights automáticos.
---

# Skill: suporte-vs-vendas

## Fontes de dados

| Arquivo | Campos-chave |
|---------|-------------|
| `wizard-imersao/dados-demo/tickets-suporte.csv` | data_abertura, cliente, email, produto, categoria, prioridade, status, tempo_resolucao_horas, descricao |
| `wizard-imersao/dados-demo/vendas.csv` | data, produto, valor, canal_aquisicao, metodo_pagamento, status |

## Executar

```bash
python3 scripts/gerar_relatorio.py
python3 scripts/gerar_relatorio.py --dias 14
python3 scripts/gerar_relatorio.py --output /tmp/relatorio.html
```

Output padrão: `/root/.openclaw/workspace-assistente/relatorio-suporte-vs-vendas.html`

## Entregar

1. Enviar o `.html` como **documento** via Telegram (não link, não screenshot).
2. Mencionar os 3 principais insights do período no texto da mensagem.

## Parâmetros

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--dias` | 7 | Janela de análise em dias |
| `--tickets` | caminho padrão | CSV de tickets |
| `--vendas` | caminho padrão | CSV de vendas |
| `--output` | workspace/relatorio-suporte-vs-vendas.html | Destino do HTML |

## Insights gerados automaticamente

O script calcula e emite alertas para:
- Taxa de reembolso (>5% warning, >15% danger)
- Tickets em aberto por produto
- Cancelamentos
- Produto com maior concentração de tickets
- Categoria dominante
- Correlação negativa entre pico de tickets e queda de receita no dia

## Cron sugerido

Toda segunda-feira 8h BRT → relatório da semana anterior → tópico 💰 Vendas (topic_id: 4)
