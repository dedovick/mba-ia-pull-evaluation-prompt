# Plano — Pull, Otimização e Avaliação de Prompts

Objetivo: transformar `bug_to_user_story_v1` num prompt v2 que atinja **≥ 0.8 em todas as 5 métricas**
(e média ≥ 0.8) contra o dataset fixo de 15 bugs (5 simples, 7 médios, 3 complexos).

Decisões:
- Provider: **OpenAI** — `LLM_MODEL=gpt-4.1-mini` (respostas), `EVAL_MODEL=gpt-4.1` (juiz). Ambos aceitam `temperature=0`
- Repositório: https://github.com/dedovick/mba-ia-pull-evaluation-prompt (`origin`), `upstream` = devfullcycle
- Handle LangSmith Hub: **piparapiro** → prompt publicado como `piparapiro/bug_to_user_story_v2`
- Few-shot como pares de mensagens (human/ai) montados pelo push a partir de `few_shot_examples` no YAML

---

## 1. Como a nota é calculada (o que guia o design do prompt)

Só existem 3 notas reais (LLM-as-judge comparando resposta × referência). As outras 2 são médias:

| Métrica      | Cálculo                                            |
|--------------|----------------------------------------------------|
| F1-Score     | juiz: precision × recall contra a referência       |
| Clarity      | juiz: organização, linguagem, ambiguidade, concisão |
| Precision    | juiz: sem alucinação, foco, correção factual       |
| Helpfulness  | (Clarity + Precision) / 2                          |
| Correctness  | (F1 + Precision) / 2                               |

Implicações:
- **Precision pesa em 3 das 5 métricas** → a regra nº 1 é não inventar nada que não esteja no relato.
- **F1 depende de espelhar o formato da referência**: "Como um [persona], eu quero [...], para que [...]"
  + "Critérios de Aceitação" em Dado/Quando/Então/E. Bugs complexos usam seções (título, critérios agrupados A/B/C).
- **CoT não pode vazar na saída** → raciocinar internamente, entregar só a User Story.
- **Tamanho proporcional à complexidade**: bug simples → resposta curta; bug complexo → todas as seções.

---

## 2. Checklist de requisitos (fonte de verdade para a verificação final)

### Setup
- [x] R1. Fork público em `dedovick`, remotes `origin`/`upstream` configurados
- [x] R2. venv + `pip install -r requirements.txt`
- [x] R3. `.env` preenchido (LangSmith, OpenAI, handle, modelos) — nunca commitado
- [x] R4. Handle público do LangSmith Hub criado (definitivo!)

### Pull (`src/pull_prompts.py`)
- [x] R5. Conecta ao LangSmith com as credenciais do `.env`
- [x] R6. Pull de `leonanluppi/bug_to_user_story_v1` com `dangerously_pull_public_prompt=True`
- [x] R7. Salva em `prompts/bug_to_user_story_v1.yml` usando `save_yaml`

### Prompt v2 (`prompts/bug_to_user_story_v2.yml`)
- [x] R8. Few-shot com exemplos de entrada/saída (obrigatório)
- [x] R9. Pelo menos mais uma técnica (planejado: Role Prompting + Skeleton of Thought + CoT interno)
- [x] R10. Instruções claras e específicas
- [x] R11. Regras explícitas de comportamento
- [x] R12. Tratamento de edge cases
- [x] R13. Separação adequada System × User (`{bug_report}` só no user prompt)
- [x] R14. Metadados: `description`, `version`, `tags`, `techniques_applied` (≥ 2)

### Push (`src/push_prompts.py`)
- [x] R15. Lê `prompts/bug_to_user_story_v2.yml` e valida
- [x] R16. Push público como `{handle}/bug_to_user_story_v2`
- [x] R17. Metadados no push (tags, descrição, técnicas)

### Testes (`tests/test_prompts.py`)
- [x] R18. `test_prompt_has_system_prompt`
- [x] R19. `test_prompt_has_role_definition`
- [x] R20. `test_prompt_mentions_format`
- [x] R21. `test_prompt_has_few_shot_examples`
- [x] R22. `test_prompt_no_todos`
- [x] R23. `test_minimum_techniques`
- [x] (extra) `{bug_report}` presente no user prompt e ausente do system prompt

### Avaliação
- [x] R24. Helpfulness, Correctness, F1, Clarity, Precision **todas ≥ 0.8**
- [x] R25. 3–5 iterações registradas no log abaixo

### Entrega (README)
- [ ] R26. Seção "Técnicas Aplicadas (Fase 2)": quais, por quê, exemplos — estruturada pela lógica do Pedro:
  **quem fala** (Role Prompting) · **como pensa** (CoT) · **como entrega** (Skeleton of Thought) · **com que modelo** (Few-shot);
  incluir por que ReAct foi descartado (sem ferramentas/ações reais → blocos Pensamento/Ação/Observação fictícios prejudicariam Clarity e Precision)
- [ ] R27. Seção "Resultados Finais": link público (`share_dataset`), screenshots, comparação v1 × v2
- [ ] R28. Seção "Como Executar": pré-requisitos, comandos por fase
- [ ] R29. Evidências no LangSmith: dataset com 15 exemplos, execuções v2 ≥ 0.8, tracing de ≥ 3 exemplos

Não alterar: `src/evaluate.py`, `src/metrics.py`, `src/utils.py`, `datasets/`.

---

## 3. Ondas de execução

**Onda 0 — Setup:** R1–R4. Conta LangSmith + API key, handle, OpenAI API key, escolha dos modelos.

**Onda 1 — Scripts e testes (test-first):** R5–R7, R15–R23.
Escrever os testes antes do v2 — eles falham até o YAML estar correto.

**Onda 2 — Prompt v2 inicial:** R8–R14.
- System: persona PM/PO sênior · regras (não inventar, persona do domínio, Dado/Quando/Então) ·
  esqueleto de saída adaptado à complexidade · análise interna antes de escrever (sem exibir) · edge cases
  (relato vago, múltiplos bugs, segurança, relato técnico/log, idioma).
- Few-shot: 3 exemplos próprios (simples, médio, complexo) no estilo das referências — **não copiar do dataset**.
- User: apenas `{bug_report}`.

**Onda 3 — Iterações:** R24–R25. Ciclo por rodada:
push → evaluate → abrir no LangSmith os exemplos com menor nota → ler o reasoning do juiz →
mudar **uma coisa por vez** → registrar no log.

**Onda 4 — Entrega:** R26–R29, push para o fork, conferência do checklist item a item.

---

## 4. Log de iterações

| # | Data | Mudança no prompt | F1 | Clarity | Precision | Helpful. | Correct. | Observações |
|---|------|-------------------|----|---------|-----------|----------|----------|-------------|
| 1 | 2026-09-26 | Rascunho: Role + CoT silencioso + Skeleton por complexidade + 3 few-shot; regra forte "não inventar" | 0.84 | 0.81 | 0.90 | 0.86 | 0.87 | Aprovado, mas no limite. Complexos curtos (~1.5k vs 3.6–5.7k da ref.) → recall baixo; juiz pede metas, correções, prevenção e soluções técnicas que a regra "não inventar" bloqueou |
| 2 | 2026-09-26 | Separar FATOS (não inventar) de PROPOSTAS (metas mensuráveis, correção, prevenção, tratamento de falha); critérios técnicos por problema nos complexos | 0.87 | 0.85 | 0.92 | 0.88 | 0.89 | Aprovado com folga (média 0.88). Complexos cresceram para 2–3k. Falhas restantes: persona de usuário em bug de backend/segurança, falta de acessibilidade em bugs de UI, validação em etapa errada (carrinho) |
| 3 | 2026-09-26 | Regras gerais: persona "o sistema" para regras internas; seção de acessibilidade obrigatória em bug de UI médio; validação no ponto da falha; contexto de segurança com severidade, erro 403 e log | 0.89 | 0.86 | 0.92 | 0.89 | 0.90 | Aprovado (média 0.89). Segurança melhorou (F1 0.82→0.92), mas persona, carrinho e modal quase não mudaram: o few-shot médio usava "Como um paciente" num caso de concorrência, contradizendo a regra, e não havia exemplo de UI. Com gpt-4.1-mini, exemplos pesam mais que instruções |
| 4 | 2026-09-26 | Few-shot alinhado às regras: exemplo médio com persona "o sistema" + validação na confirmação + prevenção informativa; novo exemplo de UI (Android) com Critérios de Acessibilidade | 0.89 | 0.86 | 0.94 | 0.90 | 0.91 | Aprovado (média 0.90). Carrinho C 0.85→0.95 / F1 0.79→0.90; modal C 0.85→0.95. Persona de usuário em bug de backend persiste (limitação aceita). Testes corrigidos: aceitar "Como o sistema" e não confundir "todos" com TODO |
| 5 | 2026-09-26 | Nenhuma (reexecução para medir estabilidade) | 0.91 | 0.87 | 0.95 | 0.91 | 0.93 | Aprovado (média 0.91). Mesmo prompt da rodada 4 → variação do juiz de ~±0.02, todas as métricas seguem ≥ 0.87 |
