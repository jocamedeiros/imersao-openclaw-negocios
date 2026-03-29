# Skill: Consulta Base de Conhecimento

> Busca na base de conhecimento e nas transcrições do curso antes de responder qualquer pergunta.

## Quando executar

**Toda vez que um aluno fizer uma pergunta.** Sem exceção. O bot nunca responde "de cabeça" — sempre consulta primeiro.

## Passos

1. **Receber a pergunta** do aluno
2. **Buscar na base de conhecimento** — FAQ validado pelo Bruno + perguntas consolidadas do Supabase
   - Base gerada automaticamente a partir das perguntas repetidas mapeadas no Supabase
   - Busca por similaridade no título + conteúdo
3. **Buscar nas transcrições** — conteúdo completo das aulas do curso
   - Transcrições indexadas por módulo e aula
   - Busca semântica por relevância
4. **Se encontrou resposta validada** → usar como base, adaptar pro contexto do aluno
5. **Se encontrou só nas transcrições** → responder com referência ao módulo/aula
6. **Se não encontrou** → executar skill `registro-duvida-pendente`

## Fontes (ordem de prioridade)

1. Base de conhecimento (respostas já validadas, geradas do Supabase)
2. Transcrições do curso (conteúdo original)
3. Conhecimento geral do modelo (última instância)

## Output

Resposta seguindo o padrão do SOUL.md:
- Contexto → Resposta → Fonte → Próximo passo
