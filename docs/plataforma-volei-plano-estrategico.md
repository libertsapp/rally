# Rally — De App de Grupo a Plataforma
### Plano estratégico e técnico para transformar o Vôlei de Terça / Vôlei Meme numa plataforma multi-times

*(Rally é só um nome de trabalho — mais sugestões de nome lá embaixo)*

---

## 1. O pitch, em uma frase

> **Já validamos o produto com dois grupos reais, toda semana, há meses. Agora construímos a plataforma que qualquer grupo de vôlei (ou qualquer esporte amador recorrente) pode usar — com a marca dele, no ritmo dele, e com um administrador que gerencia tudo isso de cima.**

Isso é exatamente o argumento que qualquer investidor sério quer ouvir: **não é uma ideia no papel, é tração real com um produto que já funciona.** O trabalho daqui pra frente não é "descobrir se as pessoas usam isso" — é "construir a estrutura pra escalar o que já sabemos que funciona".

---

## 2. O que já temos (e por que isso é uma vantagem competitiva real)

Times de vôlei recreativo — e praticamente qualquer grupo de esporte amador recorrente (futsal, padel, beach tennis, corrida) — hoje se organizam com uma combinação de **grupo de WhatsApp + planilha manual + "quem lembra, lembra"**. Isso gera três dores recorrentes:

- **Sorteio de times injusto** ou sempre feito "no olho" pela mesma pessoa (gerando desconfiança)
- **Ninguém lembra quem já jogou com quem**, quem está sumido, quem é campeão do ano
- **Zero gamificação** — o grupo não tem motivo pra voltar todo dia de jogo além do hábito

O que construímos nos últimos meses resolve exatamente isso, e já está em uso real:

| Categoria | O que já existe e funciona |
|---|---|
| **Sorteio inteligente** | Algoritmo com cota de mulheres, teto de "cabeças de chave", equilíbrio de nota, equilíbrio de altura, anti-repetição de duplas — e uma variante híbrida (grupos por nível + distribuição automática) |
| **Engajamento / gamificação** | Emblemas (Paneleiro, Carregador de Mochila, Grudento, Cabeça de Chave, Defunto), Hall da Fama mensal/anual, evolução de aproveitamento com gráfico |
| **Operacional do dia a dia** | Check-in livre sem senha, placar ao vivo com tela cheia, exportação de check-in direto pro sorteio |
| **Distribuição** | PWA instalável, compartilhamento nativo pro WhatsApp, funciona 100% no celular |
| **Personalização por marca** | Dois times, duas identidades visuais completamente diferentes (Terça = navy/dourado; Meme = roxo/neon), rodando do mesmo código-base |

Esse último ponto é a prova de conceito mais importante pro pitch: **a personalização por administrador já é uma realidade comprovada**, só precisa deixar de ser "dois arquivos HTML separados" e virar "configuração dentro de uma plataforma".

---

## 3. A visão da plataforma

### 3.1 Os três papéis

**🔑 Superadmin (você / a empresa)**
- Aprova e cria novos "espaços" (grupos/times) na plataforma
- Convida, autoriza e remove administradores de grupo
- Visão consolidada: quantos grupos ativos, quantos jogadores no total, quais grupos estão inativos
- No futuro: define planos, aprova pagamentos, suspende espaços inadimplentes

**🎛️ Admin de Grupo (o "dono" de cada time)**
- Tudo que você já tem hoje: cadastrar jogador, lançar rodada, abrir check-in, sortear
- Personalização total da identidade visual do próprio grupo (cores, nome, logo) — sem precisar de mim editando HTML pra cada grupo novo
- Não enxerga dados de outros grupos, nem sabe que eles existem

**🙋 Jogador com conta própria (opcional)**
- Cria uma conta pessoal (e-mail/senha ou login social)
- **Vincula essa conta a um cadastro de jogador já existente**, criado pelo admin — tipo "reivindicar meu perfil"
- Vê o próprio histórico, emblemas e evolução sem precisar do admin mostrar a tela pra ele
- Mais pra frente: recebe notificação quando o check-in abrir, confirma presença direto pelo próprio login

### 3.2 O caminho de monetização (pensando à frente, sem pressa)

Não precisa decidir isso agora, mas vale desenhar pra onde isso pode ir:

- **Plano Gratuito** — 1 grupo, até X jogadores, funcionalidades essenciais (é basicamente o que Terça/Meme já têm)
- **Plano Comunidade** — mensalidade baixa, sem limite de jogadores, histórico ilimitado, domínio próprio (ex: `voleidoseujoao.com` em vez de `.vercel.app`)
- **Plano Liga/Empresa** — múltiplos grupos sob uma mesma organização (ex: uma academia com vários horários/times), relatórios, suporte prioritário

O gancho de venda não é "sistema de sorteio" — é **"o grupo de vocês nunca mais some do WhatsApp por falta de organização, e ainda ganha uma cara profissional própria"**.

---

## 4. A migração técnica

### 4.1 Por que sair do Google Apps Script + Sheets

O que temos hoje foi perfeito pra validar a ideia rápido e de graça — mas tem um teto natural: cada planilha aguenta um grupo, os limites de execução do Apps Script não escalam pra dezenas de tenants simultâneos, e não existe isolamento de dados de verdade entre grupos diferentes (é tudo "na confiança").

### 4.2 A stack proposta

```
Frontend  → o mesmo espírito de hoje (HTML/JS leve), ou React se quiser
Backend   → Python com FastAPI
Banco     → PostgreSQL (Vercel Postgres, ou Neon/Supabase — todos com camada grátis boa pra começar)
Deploy    → Vercel (frontend + funções serverless do backend)
Código    → GitHub (CI/CD automático: dá push, o Vercel publica sozinho)
Auth      → um provedor gerenciado (Clerk, Supabase Auth ou Auth0) em vez de construir login do zero
```

**Por que FastAPI especificamente:** é Python (que você já vai usar), é rápido de aprender, tem documentação automática de API (facilita testar tudo pelo navegador antes de ligar no frontend), e se integra bem com Vercel via funções serverless.

**Por que não construir autenticação do zero:** login/senha parece simples até você precisar de recuperação de senha, verificação de e-mail, proteção contra força bruta, etc. Um provedor gerenciado resolve isso em uma tarde em vez de semanas — e você foca energia no que é realmente diferencial (o algoritmo de sorteio, a gamificação).

### 4.3 Esboço do modelo de dados

```
organizacoes (tenants)
 ├─ id, nome, slug (ex: "volei-terca"), cores_tema (json), plano

usuarios
 ├─ id, email, senha_hash, tipo (superadmin | admin | jogador)

admins_por_organizacao
 ├─ usuario_id, organizacao_id   (um admin pode, no futuro, gerenciar mais de 1 grupo)

jogadores
 ├─ id, organizacao_id, nome, apelido, estrelas, sexo, porte, usuario_id (opcional — vínculo com conta)

rodadas / checkins / configuracoes
 ├─ todos com organizacao_id, isolando os dados de cada grupo
```

A peça-chave de segurança é simples de enunciar e cara de fazer bem: **toda consulta ao banco tem que filtrar por `organizacao_id`, sem exceção.** Isso é o que garante que o grupo A nunca veja um byte do grupo B.

### 4.4 Caminho de migração, em fases

| Fase | O que entrega |
|---|---|
| **0 — feito** | Terça e Meme funcionando, validados por uso real |
| **1** | Reconstruir o backend em Python/FastAPI + banco real, replicando exatamente as funcionalidades de hoje, pra **um único grupo** — prova que a nova base técnica sustenta o que já existe |
| **2** | Adicionar o conceito de organização/tenant + painel de superadmin + convite de admin |
| **3** | Migrar Terça e Meme pra dentro da plataforma nova, como os dois primeiros "clientes" |
| **4** | Onboarding self-service: qualquer admin novo cria o próprio grupo sozinho, sem você mexer em código |
| **5** | Contas de jogador + vínculo de perfil + notificações |
| **6** | Cobrança (Stripe), domínio próprio por grupo, plano pago |

Cada fase entrega algo que funciona sozinho — nenhuma delas depende de "terminar tudo" pra mostrar valor.

---

## 5. Sendo honesto sobre os riscos (todo bom pitch admite isso)

- **Segurança multi-tenant é o maior risco técnico.** Um bug de isolamento (grupo A vendo dado do grupo B) destrói a confiança de uma vez. Vale investir tempo real em testes disso especificamente na Fase 2.
- **O crescimento não vem sozinho.** Ter um produto bom não gera novos grupos automaticamente — precisa de um motor de aquisição (indicação entre grupos, parcerias com quadras/arenas, etc.), que é um problema de negócio, não de código.
- **LGPD.** Dado de jogador (nome, foto, frequência) é dado pessoal. Se for cobrar dinheiro de terceiros, vale ter uma política de privacidade de verdade, não só decorativa.
- **O algoritmo de sorteio é o verdadeiro ativo técnico.** Ele já é sofisticado (cota, altura, anti-repetição, grupos por nível) — isso é difícil de copiar rápido e é, honestamente, o motivo pelo qual esse produto é mais interessante que "só uma lista de presença".

---

## 6. Ideias de nome pra plataforma (o "Rally" é só um chute)

- **Rally** — termo do próprio esporte, curto, internacional
- **Quadra** — direto, em português, fácil de lembrar
- **Convoca** — remete a "convocar o grupo", genérico o bastante pra outros esportes
- **Sacada** — trocadilho com vôlei, memorável

---

## 7. O que eu sugiro como próximo passo concreto

Antes de escrever a primeira linha da Fase 1, vale um exercício de 1 página: **listar, dos dois apps atuais, exatamente quais telas/funcionalidades são "core" (todo grupo vai querer) vs. "específico" (só Terça/Meme têm porque foi pedido assim).** Isso vira o escopo real da Fase 1, sem replicar acidentalmente decisões que só faziam sentido pra um grupo específico.

Se quiser, posso te ajudar a montar exatamente essa lista a partir de tudo que já construímos juntos nesta conversa — é literalmente um inventário do que já existe.
