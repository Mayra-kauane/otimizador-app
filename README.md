# Resume AI - Avaliação Final (IA Generativa)

Aplicação de análise e otimização de currículos com IA generativa integrada via Ollama.

## 1. Problema e solução
Problema:
- Candidatos não sabem se o currículo está aderente à vaga, se passa em ATS e quais seções melhorar.

Solução:
- Plataforma com fluxo de upload, análise por seção, comparação com vaga e relatório final.
- Nesta fase final, a IA generativa foi integrada para gerar diagnóstico, reescrita por seção e plano de ação.

## 2. Arquitetura de LLM
Fluxo principal:
1. Usuário informa currículo + vaga na interface.
2. App monta contexto (skills, métricas por seção, descrição da vaga).
3. `agents/ollama_agent.py` carrega `prompts/system_prompt.txt`.
4. Modelo sugere planejamento de tools em JSON (`tool_selection_prompt.txt`).
5. `tools/resume_tools.py` executa tools com parâmetros tipados.
6. O agente garante execução mínima das tools essenciais (keywords, gap, score, ações).
7. Modelo gera síntese final estruturada em JSON (`final_response_prompt.txt`).
8. Interface exibe resumo, risco ATS, forças, fraquezas, reescritas e próximos passos.

Arquivos relevantes:
- `prompts/system_prompt.txt`
- `prompts/tool_selection_prompt.txt`
- `prompts/final_response_prompt.txt`
- `tools/resume_tools.py`
- `agents/ollama_agent.py`
- `pages/comparison.py`
- `pages/report.py`
- `backend/main.py` (`POST /llm/analyze`)

## 3. Escolha de framework e trade-offs
Escolha:
- Orquestração própria (chamada direta HTTP para Ollama) em vez de LangChain/LangGraph.

Justificativa:
- Menor complexidade para escopo da disciplina.
- Mais controle sobre prompt, parsing de JSON e fluxo de tools.
- Fácil de explicar em 3 minutos na apresentação.

Trade-offs:
- Menos abstrações prontas do que LangChain.
- Maior responsabilidade manual de robustez no parser/output.

## 4. Modelo e parâmetros
Modelo escolhido:
- Ollama local (default: `llama3.1:8b`).

Parâmetros padrão do app:
- `temperature`: 0.3
- `top_p`: 0.9
- `num_predict`: 700

### 4.1 Experimentos de parâmetros
| Cenário | temperature | top_p | num_predict | Resultado observado |
|---|---:|---:|---:|---|
| Estável (adotado) | 0.3 | 0.9 | 700 | Melhor equilíbrio entre JSON válido e qualidade das sugestões |
| Muito conservador | 0.0 | 0.9 | 500 | JSON mais estável, porém respostas secas e menos úteis para reescrita |
| Mais criativo | 0.7 | 0.95 | 900 | Recomendações mais ricas, mas maior risco de sair do schema |

Por que modelo local:
- Custo zero por chamada.
- Privacidade de dados de currículo.
- Funciona offline para demonstração.

Limitações esperadas:
- Qualidade e confiabilidade de JSON abaixo de modelos pagos de ponta.
- Tool planning pode variar por modelo.
- Latência pode aumentar em máquinas menos potentes.

Se trocar por modelo pago:
- Tendência de melhor aderência a formato estruturado e melhor raciocínio semântico.
- Maior custo por uso e dependência de API externa.

## 5. System prompt e estratégia de prompting
System prompt:
- Define papel técnico (avaliador de currículos ATS).
- Impõe restrições (não inventar experiência, sinalizar incerteza, foco em impacto).
- Exige JSON com schema fixo.

Estratégia:
- Two-step prompting:
1. Planejamento de tools (`tool_selection_prompt.txt`) com JSON de chamadas.
2. Síntese final (`final_response_prompt.txt`) com schema de resposta.

Táticas usadas:
- Structured output (JSON estrito).
- Tool-augmented prompting.
- Prompt templates em arquivos separados para versionamento.

## 6. Tools e integração
Tools implementadas em `tools/resume_tools.py`:
- `extract_keywords(job_description, max_keywords)`
- `keyword_gap_analysis(resume_skills, job_keywords)`
- `section_score_summary(section_metrics)`
- `prioritize_actions(missing_keywords, section_scores)`

Por que essas tools:
- Cobrem o núcleo da decisão de currículo x vaga.
- São auditáveis e determinísticas.
- Facilitam explicar para o professor como LLM + código se combinam.

Tratamento de erros:
- Tool desconhecida: retorno com `tool_not_found`.
- Exceção em tool: erro capturado e retornado no payload.
- Resposta inválida do modelo: normalização de schema com fallback.
- Planning incompleto: execução forçada das 4 tools essenciais.

## 7. Segurança e robustez
Controles implementados no agente:
- Sanitização de entrada (remoção de caracteres de controle e limite de tamanho).
- Limite de skills e limite de chamadas de tools por execução.
- Contexto delimitado como dados JSON (reduz efeito de prompt injection textual).
- Normalização de saída com campos obrigatórios para evitar quebra da UI.

Risco residual:
- O modelo ainda pode produzir análises medianas em vagas muito ambíguas.
- Em hardware fraco, timeout/latência pode impactar a UX.

## 8. Como rodar
### 8.1 Ollama
```bash
ollama serve
ollama pull llama3.1:8b
```

### 8.2 Frontend (Streamlit)
```bash
cd resume-ai-app
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### 8.3 Backend (FastAPI)
```bash
cd resume-ai-app
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Endpoint adicional de LLM:
- `POST /llm/analyze`

## 9. O que funcionou
- Separar prompts em arquivos melhorou iteração e clareza.
- Fluxo de tools antes da resposta final melhorou ação prática das recomendações.
- Temperatura baixa (0.2-0.4) reduziu saídas fora de formato.
- Exibir tool results na UI ajudou na explicabilidade.
- Forçar toolchain mínima aumentou consistência entre execuções.

## 10. O que não funcionou
- Alguns modelos locais não retornam JSON válido com consistência em todas as chamadas.
- Seleção automática de tools pode vir incompleta.
- Com prompt muito aberto, o modelo tende a gerar texto fora do schema.

Ajustes aplicados:
- Prompt de seleção de tools com formato JSON estrito.
- Prompt final com campos obrigatórios.
- Fallback de resposta para manter app robusto em demo.
- Normalização final de schema no agente.

## 11. Evidência de uso do agente de codificação
- Histórico de prompts em `prompts/prompts.txt`.
- System prompt e templates versionados em `prompts/`.
- Tools e agente separados em `tools/` e `agents/`.

## 13. Repositório
- GitHub: `https://github.com/Mayra-kauane/otimizacao-app`
