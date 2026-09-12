# Inventário de Funcionalidades — Núcleo vs. Configurável vs. Específico
### Base para o escopo da Fase 1 da plataforma

Esse documento puxa **tudo** que já foi construído no Vôlei de Terça e no Vôlei Meme e classifica em três baldes:

- 🟢 **NÚCLEO** — todo grupo novo vai querer isso. Constrói uma vez na plataforma, todo tenant ganha.
- 🟡 **CONFIGURÁVEL POR GRUPO** — a funcionalidade é núcleo, mas hoje está "hardcoded" pro Terça/Meme. Na plataforma, vira uma configuração que cada admin ajusta pro próprio grupo.
- 🔴 **ESPECÍFICO DESTE GRUPO** — só existe porque foi pedido assim por vocês dois. Não é prioridade replicar como funcionalidade de plataforma (mas nada impede um admin configurar algo parecido).

---

## 🟢 NÚCLEO — o motor do produto

### Jogadores
- Cadastro (nome, apelido opcional, foto, nota de 0–5 com meio-ponto, sexo, porte P/M/G opcional)
- Edição e remoção
- Emblema "Cabeça de Chave" pra nota máxima

### Sorteio
- **Automático** — cota exata de mulheres por time, teto de jogadores nota máxima por time, equilíbrio de soma de notas, equilíbrio de altura (quando porte estiver preenchido), anti-repetição de duplas recentes
- **Manual** — grupos por nível (com a regra de cascata: grupo sempre do tamanho de um time, mulheres completam o último grupo com os homens de menor nota), arrastar pra ajustar, roleta por jogador
- **Automático por Grupos** (híbrido) — monta grupos por nível, mas distribui via algoritmo automático, garantindo que ninguém do mesmo grupo caia no mesmo time
- Seleção de participantes com busca
- Importar jogadores direto do check-in aberto

### Rodadas
- Lançar rodada (times, vencedor, vitórias de partida por time)
- Salvar como rascunho / editar rascunho depois
- Edição de rodada já lançada
- Convidados avulsos (nome, sexo, nota) numa rodada específica

### Check-in
- Abrir/fechar por data, sem senha pra confirmar presença
- Travar inclusões/exclusões
- Convidados no check-in

### Histórico e Ranking
- Lista paginada de rodadas
- Ranking anual (rodadas jogadas, vezes campeão, vitórias de partida, % de aproveitamento) com seletor de ano
- Clique no nome abre perfil; clique no número de vitórias/campeão mostra detalhe (datas)
- Exportar ranking em CSV

### Dashboard
- Campeão da semana em destaque
- Estatísticas gerais (dias jogados no ano, jogadores ativos, "desaparecidos")
- Gráfico "mais vezes na foto" (pódio + lista), com seletor de ano e tratamento de empate
- Duplas mais sorteadas juntas, com seletor de ano
- Panelas (times mais desequilibrados), com seletor de ano
- Lista de jogadores ausentes há mais de 100 dias

### Perfil do jogador
- Estatísticas (rodadas, vezes na foto, vitórias, aproveitamento)
- Gráfico de evolução (média móvel de 5 rodadas), com explicação ao tocar
- Parceiros mais frequentes (clicáveis, trocam de perfil ao clicar)
- Últimas rodadas jogadas

### Gamificação
- Emblemas automáticos: melhor do ano (foto), time desequilibrado a favor, time desequilibrado contra (nota 3+, ano atual), dupla mais recorrente, ausência prolongada
- Hall da Fama — TOP1 por mês e por ano, com empates agrupados

### Placar ao vivo
- Dois lados com cor customizável, nomes editáveis, contagem por toque/arraste, reset, tela cheia, otimizado pra celular deitado

### Plataforma / UX
- Instalável como app (PWA)
- Modo claro/escuro
- Navegação inferior no celular (itens principais + "Mais")
- Compartilhamento nativo pro WhatsApp (times, grupos, confirmados, resumo semanal)
- Sistema de dica/tooltip tocável
- Proteção de escrita por senha de admin (mascarada)
- Botão de relatar bug/sugestão

---

## 🟡 CONFIGURÁVEL POR GRUPO — núcleo, mas precisa virar setting

| Hoje (hardcoded) | Vira, na plataforma |
|---|---|
| Paleta de cores (navy/dourado no Terça, roxo/neon no Meme) | Seletor de cores no painel do admin, salvo por organização |
| Nome do grupo, subtítulo, logo | Campos de configuração de identidade, upload de logo |
| Ícone do app (bolinha estilizada) | Gerado a partir da cor escolhida, ou upload próprio |
| Link de rede social no rodapé | Campo de configuração (Instagram, ou qualquer link) |
| Número de WhatsApp do "relatar bug" | Nesse caso, esse contato deveria ser da **plataforma** (suporte), não do admin de cada grupo — repensar esse fluxo |
| Faixas de altura P/M/G em cm | Provavelmente ok fixo (é físico, não muda por grupo) — mas o rótulo/emoji do emblema pode ser customizável |
| Nomes/emojis dos emblemas (Mochila, Defunto, Paneleiro...) | Núcleo é "ter emblemas automáticos"; o texto/emoji específico pode virar customizável, pra cada grupo ter a própria "personalidade" |
| Número de dias pra virar RIP/Defunto (60/100) | Configuração numérica por grupo |
| Link fixo do site no resumo semanal | Gerado automaticamente a partir do slug da organização |

---

## 🔴 ESPECÍFICO DESTE GRUPO — não é prioridade de plataforma

- O conteúdo específico da página **Info** (textos explicativos escritos pensando no Terça/Meme)
- A piada/tom de humor específico de alguns nomes de emblema (isso é "voz de marca" do Heleno, não uma decisão de produto universal)
- Qualquer texto fixo em português informal — plataforma pode precisar de i18n (outro idioma) no futuro, o que hoje nem é uma questão
- A escolha específica de 4 itens na barra inferior (Início/Check-in/Sorteio/Ranking) — outro grupo pode preferir outra combinação; isso também tende a virar 🟡 configurável mais pra frente, mas não é bloqueio pra Fase 1

---

## O que isso significa pra Fase 1 (reconstrução em Python/FastAPI)

**Objetivo da Fase 1:** replicar tudo que está marcado 🟢, com os itens 🟡 já nascendo como **campos de configuração no banco** (mesmo que, no início, só um admin — você — consiga editá-los por trás). Isso evita o retrabalho de "construir fixo, depois quebrar tudo de novo pra virar configurável".

**Não vale a pena** gastar tempo replicando os itens 🔴 na estrutura da plataforma — eles continuam existindo como *conteúdo*, não como *funcionalidade*, e cada admin escreve o próprio quando personalizar o grupo dele.

### Sugestão de ordem de construção dentro da Fase 1
1. Jogadores + Rodadas + Check-in (a base de dados que tudo depende)
2. Sorteio automático (o algoritmo é o ativo técnico mais valioso — vale isolar como um módulo Python bem testado, independente do resto)
3. Histórico + Ranking + Dashboard
4. Perfil + Gamificação + Hall da Fama
5. Placar ao vivo (é o mais isolado/independente — pode até vir em paralelo)
6. PWA + identidade visual configurável por último, já validando o modelo de tenant desde o início
