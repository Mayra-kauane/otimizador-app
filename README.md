# Plataforma Inteligente de Análise e Otimização de Currículos

Aplicação desenvolvida em `Streamlit`, com persistência em `SQLite` e backend em `FastAPI`, focada em diagnóstico e otimização de currículos.

## 1) Problema
Candidatos costumam ter dificuldade para:
- saber se o currículo está claro e com impacto;
- identificar lacunas para vagas específicas;
- entender aderência a filtros ATS;
- transformar análise em melhorias práticas.

## 2) Solução proposta
A plataforma organiza o processo em módulos:
1. `Home`: visão geral, histórico e gestão de análises.
2. `Upload e Parsing`: envio do currículo e extração estruturada (mock).
3. `Análise por Seção`: métricas por seção + simulações de otimização com IA.
4. `Comparação com a Vaga`: fluxo estruturado de comparação currículo x vaga.
5. `Relatário Final`: painel analático com score, prioridades e recomendações.
6. `Histórico`: consulta das análises registradas.

## 3) Arquitetura
- Frontend: `Streamlit`
- Backend: `FastAPI` (API REST)
- Banco de dados: `SQLite` (`data/analises.db`)
- Lógica de negócio: módulo `core/`

### Estrutura de pastas
- `app.py`: ponto de entrada do Streamlit
- `pages/`: telas da aplicação
- `components/`: widgets e estilos
- `core/`: acesso a dados e regras de negócio
- `backend/main.py`: API FastAPI
- `backend/requirements.txt`: dependências do backend
- `data/analises.db`: banco SQLite

## 4) Como executar

### 4.1 Frontend (Streamlit)
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install streamlit
streamlit run app.py
```
Acesse: `http://localhost:8501`

### 4.2 Backend (FastAPI)
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```
Acesse:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 5) Endpoints principais da API
- `GET /health`
- `GET /analises`
- `GET /analises/{id}`
- `POST /analises`
- `DELETE /analises/{id}`
- `POST /comparacoes/run`
- `GET /comparacoes/analise/{analise_id}`
- `GET /comparacoes/{id}`
- `GET /relatorios/{analise_id}`

### Prompt 1
"› Eu quero fazer uma plataforma inteligente de analise e otimização de currículos, o problema seria que os candidatos
  clareza e impacto e asugerir palavras chaves. A ideia para o fluxo geral da aplicação seria upload de curriculos,
  analise por seção, comparação com a vaga, realtório final e histórico de analises. Na tela um eu gostaria de um
  dashboard, que seria a tela home, onde o objetivo seria gerenciar analises, os componentes seia botão de nova
  analise, lista de analises anteriores, data da analise, nome do candidato, status e botão visulizar, e isso poderia
  ser salvo num banco SQlite. Na segunda tela eu gostaria de upload e parsing com os componentes upload de arquivos de
  pdf ou docx, campo: Nome do candidato, campo: área de interese, botão de procesar curriculo e apos o upload mostrar
  extração estruturada, dados pessoais, experiencia, educação, habilidades, certificações. Na terceira tela seria uma
  analise por seção, aqui seria uma interface em abas, na aba 1 seris estrutura, tem resumo profissional?, Tamanho
  adequado?, ordem lógica? aba 2 experiencia, quantidade de experiencias? tempo medio? uso de verbos de ação, mock
  comparação com a vaga, componenets campo para colar dewscrição da vaga, botão de comparar, sistema calcula(mock) % de
  compatibilidade, palavras chaves presentes, palavras chave ausentes, mostrar lista verde encontrados, lista vermelha
  faltando, score geral. e na tela 5 seria o relatório final com score geral, pontos fracos e pontos fortes,
  recomendações e sugestão de melhorias por seção e um botão de exportar pdf. vc entendeu a ideia? faça isso no
  streamlit por favor"
- Status: **Funcionou**
- Motivo: defini o fluxo, as telas e os componentes esperados.

### Prompt 2
"Agora acentue todas as palavras e deixe tudo correto gramaticalmente."
- Status: **Parcialmente funcionou**
- Motivo: vários textos foram corrigidos, mas houve regressões de encoding durante as iterações.

### Prompt 3
"Vamos melhorar isso visualemente. Agora eu quero melhorar a tela do dashboard, mude o nome para home, retire esse dashboarde da tela, deixe apenas a frase "Gerencie análises, acompanhe status e acesse relatórios." logo após o texto de plataforma..., e falando nisso coloque o texto de "Plataforma de Análise e Otimização de Currículos" coloque algo para destacalo, como um retangulo sei lá, muder a cor do retangulo qu ele eestá inserido, na lista de analises anteriores adiocne um botão de excluir ao lado do botão visualizar, coloque o analise no mês dentro de uma card e o score médio tbm, dimunua o botão de nova analise e deixe ele mais após as analises no mÊs e scpre medio. Mude a navegação, implemente um sidebar mais adequado"
- Status: **Funcionou**
- Motivo: layout da Home foi reestruturado e ações de gestão foram adicionadas.

### Prompt 4
"Agora vamos componentizar isso"
- Status: **Funcionou**
- Motivo: projeto foi modularizado em `core/`, `components/` e `pages/`.

### Prompt 5
"Coloque o que for do banco de dados em uma pasta também."
- Status: **Funcionou**
- Motivo: banco movido para `data/` com caminho atualizado.

### Prompt 6
"agora vamos organizar novamente o visual da paltaforma, deixe o body branco e os componenetes coloque uma cor que fique legal, talvez no lugar do azul do texto de Plataforma de Análise e Otimização de Currículos colocar um amarelo pastel, e os cads tbm na msm cor, coloqu o botão de nova analise com uma cor que combine com esse amarelo pastel, na lista de analises de vendas coloque uma verifição em modal caso o usuário clique para excluir, coloque a verifição se ele deseja msm excluir, e adicione mais usários mokadoa nos status que temos no sistema"
- Status: **Funcionou**
- Motivo: tema e interação de exclusão foram implementados; seed expandido.

### Prompt 7
"Volte pras cores que estavam antes, fundo preto e os cards em alguma cor que combine com o fundo preto, o botão de nova analise a msm coisa, e o fundo de Plataforma de Análise e Otimização de Currículos colocar tbm em uma cor que combine com os demais componentes da tela"
- Status: **Funcionou**
- Motivo: paleta escura foi restabelecida.

### Prompt 8
"agora diminua o tamanho dos cards e faça novamnete a varredura e certifique-se que todas as palavras do front entejam corretamente acentuadas e gramaticalmente corretas"
- Status: **Parcialmente funcionou**
- Motivo: cards foram ajustados, mas houve oscilação entre redução vertical e horizontal.

### Prompt 9
"Implemente ação de excluir no botão de excluir"
- Status: **Funcionou**
- Motivo: corrigido comportamento de seed que reinseria registros excluídos.

### Prompt 10
"Upload e Parsing puxe o nome do candidato e Área de interesse direto do curriculo, e só deixe esses campo Extração estruturada no formulário, alías estruture essa extração em um formulário, os campos podem ser os mesmos apenas corrija a forma como está na tela, e deixe em formato de formulário e todas as informações devem ser preenchidas pelas informações vindas do currículo"
- Status: **Funcionou (mock)**
- Motivo: inferência automática foi implementada por heurística; parser real ainda não foi integrado.

### Prompt 11
"o botão visulaizr não está funcionando, corrija e coloque pra visualizar diretamente na tela home, quando clicar em visualizar deve-se abrir um modal do relatório"
- Status: **Funcionou**
- Motivo: seletor de candidato e blocos de IA mock por seção foram adicionados.

### Prompt 12
"o formulário na tela Upload e Parsing só deve aparecer quando tiver currículo pra extração de dados e após isso, quando o cúrriculo sair ou trocar detela ele deve sumir"
- Status: **Funcionou**

### Prompt 13
"Para essa tela de analise por seção coloque algo como IA na Reescrita Inteligente(mock) o sistema pode ter um botão “Reescrever seção” e quando a IA for implementada ela poderia ajustar para tom mais profissional, adaptar para área específica, transformar bullet points fracos em fortes, ajustar para vaga específica e na aba IA para ajuste para ATS quandoa a IA for implementada poderia detectar ausência de palavras-chave estratégicas reorganizar estrutura, melhorar escaneabilidade, ajustar linguagem para passar filtros automáticos. Faça isso de forma que o layout fique bem com que já temos e organize tudo, os componentes pra que quando for integrado com a IA isso funcione bem, por enquanto deixe tudo com dados mokado"
- Status: **funcionou**
- Motivo: as alteraçõe forma devidamente implementadas como descrito no prompt

### Prompt 14
"Faça o botão Nova análise da Home voltar a funcionar."
- Status: ** Não funcionou**
- Motivo: Deu erro tentando modificar uma chave de SessionState que já foi vinculada a um widget.

### Prompt 15
"na parte de comparação com vaga Para melhorar a tela de Comparação com a Vaga, devemos transformá-la em um fluxo mais estruturado e estratégico, permitindo que o usuário selecione qual currículo deseja comparar antes de inserir ou escolher a vaga. Em vez de apenas um campo para colar a descrição, a interface deve conter três etapas claras: (1) seleção do currículo salvo no sistema, (2) inserção ou escolha de uma vaga previamente cadastrada e (3) execução da análise com opção de salvar o resultado. Essa mudança torna o sistema mais realista, pois permite comparar diferentes versões de currículo com múltiplas vagas e manter um histórico de análises. A integração futura com IA generativa pode ocorrer na etapa de análise, permitindo não apenas calcular aderência por palavras-chave, mas também realizar correspondência semântica entre experiências e requisitos, identificar lacunas estratégicas e gerar automaticamente sugestões de adaptação do currículo para aquela vaga específica. Dessa forma, a tela deixa de ser apenas comparativa e passa a ser um módulo inteligente de recomendação e otimização personalizada, elevando a complexidade técnica e o valor prático do sistema."
- Status: **Funcionou**
- Motivo: tela foi estruturada com seleção de currículo, vaga e execução/salvamento.

### Prompt 16
"a tela de relatório final deve mudar e evlouir desta maneira, um formato estático para um painel analítico mais visual, estruturado e orientado à ação. Em vez de apresentar apenas um score geral seguido de listas de pontos fortes e fracos, o layout pode ser reorganizado em cards bem definidos, com um destaque maior para o score (incluindo classificação qualitativa e indicador visual), além de uma análise por seção com barras individuais e níveis de prioridade de melhoria. Os pontos fortes e fracos devem conter explicações mais contextualizadas, demonstrando interpretação do conteúdo e não apenas enumeração de problemas. Também é importante incluir uma seção específica de “Recomendações Geradas por IA”, onde o sistema simula sugestões de reescrita, melhoria estratégica e adaptação à vaga, evidenciando claramente o uso futuro de IA generativa. Por fim, a tela pode oferecer opções mais robustas de exportação e comparação entre versões, transformando o relatório em um módulo inteligente de diagnóstico e otimização contínua, e não apenas um resumo informativo."
- Status: **Funcionou**
- Motivo: relatário evoluiu para painel analático com prioridades e recomendações mock de IA.

### Prompt 17
"Coloque um select box para escolher qual currículo ver no histórico final."
- Status: **Funcionou**
- Motivo: seletor foi adicionado no topo do relatário.

### Prompt 16
"implemente um backend, cosntrua um que se adapte ao que eu tenho e intregre sem erros"
- Status: **Funcionou**
- Motivo: backend FastAPI foi criado em `backend/` com integraçãoo ao SQLite.

### Prompt 17
"Corrija gramaticalmente todas as palavras que contem acentuação"
- Status: ** Não funcionou**
