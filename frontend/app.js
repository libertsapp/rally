/* Vôlei — frontend leve (sem build), consome a API FastAPI em backend/. */

// Dev local (dois servidores separados, frontend na porta 5500) aponta pro
// uvicorn direto; em qualquer outro caso (vercel dev, produção) a API mora
// na mesma origem, sob /api — sem precisar mexer nisso a cada deploy.
const API_BASE = window.API_BASE || (window.location.port === '5500' ? 'http://127.0.0.1:8000' : '/api');

/* ---------------- estado ---------------- */
const state = {
  tab: 'inicio',
  sub: null,
  config: null,
  jogadores: [],
  checkins: [],
  draftTeams: null,
  draftGrupos: null,
  placar: { nomeA: 'Time A', nomeB: 'Time B', a: 0, b: 0 },
  usuario: null, // { id, email, tipo, organizacao_id } — null enquanto não logado
};

/* ---------------- api helper ---------------- */
async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (window.Clerk?.session) {
    try {
      const token = await window.Clerk.session.getToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    } catch (e) { /* sessão expirou ou afins — segue sem token, a API trata como anônimo */ }
  }
  const resp = await fetch(API_BASE + path, { headers, ...options });
  if (!resp.ok) {
    let detail = resp.statusText;
    try { detail = (await resp.json()).detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  if (resp.status === 204) return null;
  return resp.json();
}
const get = (path) => api(path);
const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) });
const put = (path, body) => api(path, { method: 'PUT', body: JSON.stringify(body) });
const del = (path) => api(path, { method: 'DELETE' });

function toast(msg, isError) {
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = 'toast';
  if (isError) el.style.background = 'var(--danger)', el.style.color = '#fff';
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}
async function tryRun(fn, okMsg) {
  try {
    await fn();
    if (okMsg) toast(okMsg);
  } catch (e) {
    toast(e.message || 'Algo deu errado.', true);
  }
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function nomeDe(p) { return p ? (p.apelido || p.nome) : '(removido)'; }
function iniciais(nome) { return (nome || '?').trim().charAt(0).toUpperCase(); }
function jogadorPorId(id) { return state.jogadores.find((p) => p.id === id); }
function anoAtual() { return String(new Date().getFullYear()); }

/* ---------------- identidade visual (Organizacao) ---------------- */
function aplicarIdentidade(org) {
  const root = document.documentElement;
  if (org.cor_primaria) root.style.setProperty('--accent', org.cor_primaria);
  document.getElementById('brand-name').textContent = org.nome || 'Vôlei';
  document.getElementById('brand-sub').textContent = org.subtitulo || 'Organização recreativa';
  if (org.cor_primaria) document.getElementById('brand-dot').style.background = org.cor_primaria;
}

/* ---------------- navegação ---------------- */
function switchTab(tab) {
  state.tab = tab;
  state.sub = null;
  document.querySelectorAll('#bottom-nav button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
  render();
}
document.getElementById('bottom-nav').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-tab]');
  if (btn) switchTab(btn.dataset.tab);
});
document.getElementById('theme-toggle').addEventListener('click', () => {
  document.body.classList.toggle('light');
});

/* ---------------- autenticação (Clerk) ---------------- */
function atualizarBotaoAuth() {
  const btn = document.getElementById('auth-btn');
  if (state.usuario) {
    btn.textContent = '👋';
    btn.title = `Sair (${state.usuario.email})`;
  } else {
    btn.textContent = '👤';
    btn.title = 'Entrar';
  }
}

async function carregarUsuarioAtual() {
  if (!window.Clerk?.session) { state.usuario = null; return; }
  try {
    state.usuario = await get('/usuarios/eu');
  } catch (e) {
    state.usuario = null;
  }
}

document.getElementById('auth-btn').addEventListener('click', async () => {
  if (!window.Clerk) { toast('Autenticação ainda carregando, tente de novo em instantes.', true); return; }
  if (state.usuario) {
    await window.Clerk.signOut();
    state.usuario = null;
    atualizarBotaoAuth();
    render();
  } else {
    window.Clerk.openSignIn({
      afterSignInUrl: window.location.href,
      afterSignUpUrl: window.location.href,
    });
  }
});

function render() {
  const view = document.getElementById('view');
  const renderers = { inicio: renderInicio, checkin: renderCheckin, sorteio: renderSorteio, ranking: renderRanking, mais: renderMais };
  view.innerHTML = '<div class="empty">Carregando...</div>';
  (renderers[state.tab] || renderInicio)(view);
}

/* ================= INÍCIO ================= */
async function renderInicio(view) {
  try {
    const [resumo, ausentes] = await Promise.all([get('/dashboard/resumo'), get('/dashboard/ausentes')]);
    const campeao = resumo.campeao_semana;
    view.innerHTML = `
      ${campeao ? `
        <div class="panel" style="border-color:var(--accent);">
          <div class="row-sub">CAMPEÃO MAIS RECENTE — ${escapeHtml(campeao.data)}</div>
          <div style="font-family:'Archivo Black';font-size:18px;margin-top:4px;">🏆 ${escapeHtml(campeao.time_nome)}</div>
          <div class="row-sub" style="margin-top:6px;">${campeao.player_ids.map((id) => escapeHtml(nomeDe(jogadorPorId(id)))).join(', ')}</div>
        </div>
      ` : `<div class="empty">Nenhuma rodada com campeão definido ainda.</div>`}

      <div class="section-title">Resumo de ${escapeHtml(resumo.ano)}</div>
      <div class="stat-grid">
        <div class="stat"><div class="stat-num">${resumo.dias_jogados_no_ano}</div><div class="stat-cap">Dias jogados</div></div>
        <div class="stat"><div class="stat-num">${resumo.jogadores_ativos}</div><div class="stat-cap">Jogadores ativos</div></div>
        <div class="stat"><div class="stat-num">${resumo.desaparecidos}</div><div class="stat-cap">Desaparecidos</div></div>
      </div>

      ${ausentes.length ? `
        <div class="section-title">Sumidos 👻🪦</div>
        <div class="panel">${ausentes.slice(0, 6).map((a) => `
          <div class="row">
            <div class="avatar">${iniciais(a.apelido || a.nome)}</div>
            <div><div class="row-name">${escapeHtml(a.apelido || a.nome)}</div></div>
            <div class="row-right"><span class="pill ${a.status === 'aposentado' ? 'danger' : ''}">${a.dias_sem_jogar}d</span></div>
          </div>`).join('')}
        </div>
      ` : ''}
    `;
  } catch (e) {
    view.innerHTML = `<div class="empty">Não consegui carregar o início: ${escapeHtml(e.message)}</div>`;
  }
}

/* ================= CHECK-IN ================= */
async function carregarCheckinData() {
  const [config, jogadores, checkins] = await Promise.all([get('/config'), get('/jogadores'), get('/checkins')]);
  state.config = config;
  state.jogadores = jogadores;
  state.checkins = checkins;
}

async function renderCheckin(view) {
  try {
    await carregarCheckinData();
  } catch (e) {
    view.innerHTML = `<div class="empty">Não consegui carregar o check-in: ${escapeHtml(e.message)}</div>`;
    return;
  }
  const cfg = state.config;
  const aberto = !!cfg.checkin_data_aberta;
  const confirmadosHoje = new Set(state.checkins.filter((c) => c.data === cfg.checkin_data_aberta).map((c) => c.jogador_id));

  view.innerHTML = `
    <div class="panel">
      ${aberto
        ? `<div class="row-sub">CHECK-IN ABERTO — ${escapeHtml(cfg.checkin_data_aberta)}</div>
           <div style="margin-top:4px;font-weight:700;">${cfg.checkin_travado ? '🔒 Travado pelo admin' : `${confirmadosHoje.size} confirmado(s)`}</div>`
        : `<div class="row-sub">CHECK-IN FECHADO</div>`}
      <div class="btn-row">
        ${!aberto ? `
          <input type="date" id="nova-data-checkin" value="${new Date().toISOString().slice(0, 10)}" style="flex:1;">
          <button class="btn" id="abrir-checkin-btn">Abrir</button>
        ` : `
          <button class="btn secondary" id="fechar-checkin-btn">Fechar</button>
          <button class="btn ${cfg.checkin_travado ? '' : 'ghost'}" id="travar-checkin-btn">${cfg.checkin_travado ? 'Destravar' : 'Travar'}</button>
        `}
      </div>
    </div>

    <div class="section-title">Jogadores</div>
    <div class="panel">
      ${state.jogadores.length === 0 ? '<div class="empty">Nenhum jogador cadastrado ainda. Adicione em "Mais → Jogadores".</div>' : state.jogadores.map((p) => {
        const confirmado = confirmadosHoje.has(p.id);
        return `
        <div class="row">
          <div class="avatar">${iniciais(p.apelido || p.nome)}</div>
          <div><div class="row-name">${escapeHtml(nomeDe(p))}</div></div>
          <div class="row-right">
            <button class="btn ${confirmado ? '' : 'secondary'}" style="padding:6px 12px;font-size:12px;" data-checkin-toggle="${p.id}" ${!aberto || cfg.checkin_travado ? 'disabled' : ''}>
              ${confirmado ? '✓ Confirmado' : 'Confirmar'}
            </button>
          </div>
        </div>`;
      }).join('')}
    </div>
  `;

  document.getElementById('abrir-checkin-btn')?.addEventListener('click', () => tryRun(async () => {
    const data = document.getElementById('nova-data-checkin').value;
    await put('/config', { ...cfg, checkin_data_aberta: data, checkin_travado: false });
    await renderCheckin(view);
  }, 'Check-in aberto.'));

  document.getElementById('fechar-checkin-btn')?.addEventListener('click', () => tryRun(async () => {
    await put('/config', { ...cfg, checkin_data_aberta: '', checkin_travado: false });
    await renderCheckin(view);
  }, 'Check-in fechado.'));

  document.getElementById('travar-checkin-btn')?.addEventListener('click', () => tryRun(async () => {
    await put('/config', { ...cfg, checkin_travado: !cfg.checkin_travado });
    await renderCheckin(view);
  }));

  view.querySelectorAll('[data-checkin-toggle]').forEach((btn) => {
    btn.addEventListener('click', () => tryRun(async () => {
      const pid = btn.dataset.checkinToggle;
      const existente = state.checkins.find((c) => c.data === cfg.checkin_data_aberta && c.jogador_id === pid);
      if (existente) {
        await del(`/checkins/${existente.id}`);
      } else {
        const p = jogadorPorId(pid);
        await post('/checkins', { jogador_id: pid, jogador_nome: p.nome, estrelas: p.estrelas, sexo: p.sexo });
      }
      await renderCheckin(view);
    }));
  });
}

/* ================= SORTEIO ================= */
async function renderSorteio(view) {
  try {
    await carregarCheckinData();
  } catch (e) {
    view.innerHTML = `<div class="empty">${escapeHtml(e.message)}</div>`;
    return;
  }
  const confirmadosHoje = state.config.checkin_data_aberta
    ? new Set(state.checkins.filter((c) => c.data === state.config.checkin_data_aberta).map((c) => c.jogador_id))
    : new Set();
  const usaCheckin = confirmadosHoje.size > 0;

  view.innerHTML = `
    <div class="panel">
      <label>Quem participa</label>
      <select id="sorteio-fonte">
        <option value="checkin" ${usaCheckin ? 'selected' : ''}>Confirmados no check-in de hoje (${confirmadosHoje.size})</option>
        <option value="todos">Todos os jogadores (${state.jogadores.length})</option>
      </select>
      <div class="field-row">
        <div>
          <label>Número de times</label>
          <input type="number" id="sorteio-num-times" min="2" max="8" value="4">
        </div>
        <div>
          <label>Modo</label>
          <select id="sorteio-modo">
            <option value="auto">Automático</option>
            <option value="grupos">Grupos por nível + automático</option>
          </select>
        </div>
      </div>
      <div class="btn-row">
        <button class="btn" id="sortear-btn">Sortear times</button>
      </div>
    </div>
    <div id="sorteio-resultado"></div>
  `;

  document.getElementById('sortear-btn').addEventListener('click', () => tryRun(async () => {
    const fonte = document.getElementById('sorteio-fonte').value;
    const numTimes = parseInt(document.getElementById('sorteio-num-times').value, 10);
    const modo = document.getElementById('sorteio-modo').value;
    const ids = fonte === 'checkin' ? [...confirmadosHoje] : state.jogadores.map((p) => p.id);
    if (ids.length < numTimes) throw new Error('Poucos jogadores selecionados para esse número de times.');

    let grupos = null;
    if (modo === 'grupos') {
      grupos = await post('/sorteio/grupos', { jogador_ids: ids, num_times: numTimes });
    }
    const times = await post('/sorteio/times', { jogador_ids: ids, num_times: numTimes, grupos });
    state.draftTeams = times;
    renderResultadoSorteio(document.getElementById('sorteio-resultado'), numTimes);
  }));
}

function renderResultadoSorteio(container, numTimes) {
  const times = state.draftTeams;
  container.innerHTML = `
    <div class="section-title">Times sorteados</div>
    <div class="times-grid">
      ${times.map((ids, i) => `
        <div class="time-card">
          <h4>Time ${i + 1}</h4>
          ${ids.map((id) => `<div class="player-name">${escapeHtml(nomeDe(jogadorPorId(id)))}</div>`).join('')}
        </div>`).join('')}
    </div>

    <div class="section-title">Lançar como rodada</div>
    <div class="panel">
      <label>Data</label>
      <input type="date" id="rodada-data" value="${state.config.checkin_data_aberta || new Date().toISOString().slice(0, 10)}">
      ${times.map((_, i) => `
        <div class="field-row" style="margin-top:8px;align-items:end;">
          <div>
            <label>Vitórias — Time ${i + 1}</label>
            <input type="number" min="0" id="rodada-vitorias-${i}" value="0">
          </div>
          <div style="display:flex;align-items:center;gap:6px;padding-bottom:10px;">
            <input type="radio" name="rodada-vencedor" value="${i}" id="rodada-vencedor-${i}">
            <label for="rodada-vencedor-${i}" style="margin:0;">Campeão</label>
          </div>
        </div>`).join('')}
      <button class="btn block" id="salvar-rodada-btn">Salvar rodada</button>
    </div>
  `;

  document.getElementById('salvar-rodada-btn').addEventListener('click', () => tryRun(async () => {
    const data = document.getElementById('rodada-data').value;
    const vencedorEl = container.querySelector('input[name="rodada-vencedor"]:checked');
    const vencedor = vencedorEl ? parseInt(vencedorEl.value, 10) : -1;
    const rodadaTimes = times.map((ids, i) => ({
      nome: `Time ${i + 1}`,
      player_ids: ids,
      vitorias: parseInt(document.getElementById(`rodada-vitorias-${i}`).value, 10) || 0,
    }));
    await post('/rodadas', { data, rascunho: false, vencedor, times: rodadaTimes });
    state.draftTeams = null;
    container.innerHTML = '<div class="empty">Rodada salva! Confira no Ranking ou no Início.</div>';
  }, 'Rodada salva.'));
}

/* ================= RANKING ================= */
async function renderRanking(view) {
  const ano = state.rankingAno || anoAtual();
  view.innerHTML = `
    <div class="panel">
      <label>Ano</label>
      <input type="number" id="ranking-ano" value="${ano}">
    </div>
    <div id="ranking-tabela"><div class="empty">Carregando...</div></div>
  `;
  document.getElementById('ranking-ano').addEventListener('change', (e) => {
    state.rankingAno = e.target.value;
    carregarRanking();
  });
  await carregarRanking();

  async function carregarRanking() {
    const tabela = document.getElementById('ranking-tabela');
    try {
      const linhas = await get(`/ranking?ano=${encodeURIComponent(state.rankingAno || ano)}`);
      if (linhas.length === 0) { tabela.innerHTML = '<div class="empty">Sem rodadas nesse ano ainda.</div>'; return; }
      tabela.innerHTML = `
        <table class="simple">
          <thead><tr><th>#</th><th>Jogador</th><th>Jogos</th><th>Títulos</th><th>Vitórias</th><th>%</th></tr></thead>
          <tbody>
            ${linhas.map((l, i) => `
              <tr>
                <td>${i + 1}º</td>
                <td>${escapeHtml(l.apelido || l.nome)}</td>
                <td>${l.jogos}</td>
                <td>${l.titulos}</td>
                <td>${l.vitorias_partidas}</td>
                <td>${l.pct}%</td>
              </tr>`).join('')}
          </tbody>
        </table>`;
    } catch (e) {
      tabela.innerHTML = `<div class="empty">${escapeHtml(e.message)}</div>`;
    }
  }
}

/* ================= MAIS (menu + sub-telas) ================= */
async function renderMais(view) {
  const subs = {
    jogadores: renderJogadoresSub,
    config: renderConfigSub,
    hall: renderHallSub,
    placar: renderPlacarSub,
    organizacoes: renderOrganizacoesSub,
  };
  if (state.sub && subs[state.sub]) { await subs[state.sub](view); return; }

  const itens = [
    ['jogadores', '👤', 'Jogadores', 'Cadastrar, editar e remover'],
    ['placar', '🔴', 'Placar ao vivo', 'Contagem em tela cheia'],
    ['hall', '🏆', 'Hall da Fama', 'Campeões por mês e por ano'],
    ['config', '⚙️', 'Identidade e configurações', 'Cores, nome, prazos de ausência'],
  ];
  if (state.usuario?.tipo === 'superadmin') {
    itens.push(['organizacoes', '🏢', 'Organizações', 'Criar grupos e convidar admins']);
  }

  view.innerHTML = `
    <div class="section-title">Mais</div>
    <div class="panel" style="padding:0;">
      ${itens.map(([key, icon, title, sub]) => `
        <div class="row" data-open-sub="${key}" style="cursor:pointer;">
          <div class="avatar">${icon}</div>
          <div><div class="row-name">${title}</div><div class="row-sub">${sub}</div></div>
          <div class="row-right">›</div>
        </div>`).join('')}
    </div>
    ${state.usuario ? `<div class="empty">Logado como ${escapeHtml(state.usuario.email)} (${state.usuario.tipo})</div>` : ''}
  `;
  view.querySelectorAll('[data-open-sub]').forEach((row) => {
    row.addEventListener('click', () => { state.sub = row.dataset.openSub; render(); });
  });
}

/* ---- Organizações (só superadmin) ---- */
async function renderOrganizacoesSub(view) {
  view.innerHTML = `${subHeader('Organizações')}<div class="empty">Carregando...</div>`;
  wireVoltar(view);
  let lista;
  try {
    lista = await get('/organizacoes');
  } catch (e) {
    view.innerHTML = `${subHeader('Organizações')}<div class="empty">${escapeHtml(e.message)}</div>`;
    wireVoltar(view);
    return;
  }

  view.innerHTML = `
    ${subHeader('Organizações')}
    <div class="panel">
      <label>Nome do novo grupo</label>
      <input type="text" id="nova-org-nome">
      <label>Slug (identificador único, ex: volei-de-terca)</label>
      <input type="text" id="nova-org-slug">
      <button class="btn block" id="criar-org-btn">Criar organização</button>
    </div>
    <div class="panel">
      ${lista.map((o) => `
        <div class="row">
          <div class="avatar">${iniciais(o.nome)}</div>
          <div><div class="row-name">${escapeHtml(o.nome)}</div><div class="row-sub">${escapeHtml(o.slug)}</div></div>
          <div class="row-right"><button class="btn ghost" style="padding:6px 10px;font-size:12px;" data-convidar="${o.id}">+ admin</button></div>
        </div>`).join('')}
    </div>
  `;
  wireVoltar(view);
  document.getElementById('criar-org-btn').addEventListener('click', () => tryRun(async () => {
    const nome = document.getElementById('nova-org-nome').value.trim();
    const slug = document.getElementById('nova-org-slug').value.trim();
    if (!nome || !slug) throw new Error('Preencha nome e slug.');
    await post('/organizacoes', { nome, slug });
    await renderOrganizacoesSub(view);
  }, 'Organização criada.'));
  view.querySelectorAll('[data-convidar]').forEach((btn) => {
    btn.addEventListener('click', () => tryRun(async () => {
      const email = prompt('E-mail do admin a convidar:');
      if (!email) return;
      await post(`/organizacoes/${btn.dataset.convidar}/admins`, { email });
    }, 'Admin convidado.'));
  });
}

function subHeader(titulo) {
  return `<button class="btn ghost" id="voltar-mais-btn" style="margin-bottom:12px;">‹ Mais</button><div class="section-title" style="margin-top:0;">${titulo}</div>`;
}
function wireVoltar(view, after) {
  document.getElementById('voltar-mais-btn').addEventListener('click', () => { state.sub = null; render(); });
  if (after) after();
}

/* ---- Jogadores (CRUD) ---- */
async function renderJogadoresSub(view) {
  const jogadores = await get('/jogadores');
  state.jogadores = jogadores;
  view.innerHTML = `
    ${subHeader('Jogadores')}
    <div class="panel">
      <label>Nome</label>
      <input type="text" id="novo-nome">
      <div class="field-row" style="margin-top:8px;">
        <div><label>Estrelas (0–5)</label><input type="number" id="novo-estrelas" min="0" max="5" step="0.5" value="3"></div>
        <div><label>Sexo</label><select id="novo-sexo"><option value="M">M</option><option value="F">F</option></select></div>
      </div>
      <button class="btn block" id="add-jogador-btn">Adicionar jogador</button>
    </div>
    <div class="panel">
      ${jogadores.length === 0 ? '<div class="empty">Nenhum jogador ainda.</div>' : jogadores.map((p) => `
        <div class="row">
          <div class="avatar">${iniciais(p.apelido || p.nome)}</div>
          <div><div class="row-name">${escapeHtml(nomeDe(p))}</div><div class="row-sub">${p.estrelas}★ · ${p.sexo || '—'}</div></div>
          <div class="row-right"><button class="btn ghost" style="padding:6px 10px;font-size:12px;" data-del-jogador="${p.id}">Remover</button></div>
        </div>`).join('')}
    </div>
  `;
  wireVoltar(view);
  document.getElementById('add-jogador-btn').addEventListener('click', () => tryRun(async () => {
    const nome = document.getElementById('novo-nome').value.trim();
    if (!nome) throw new Error('Digite um nome.');
    await post('/jogadores', {
      nome,
      estrelas: parseFloat(document.getElementById('novo-estrelas').value) || 0,
      sexo: document.getElementById('novo-sexo').value,
    });
    await renderJogadoresSub(view);
  }, 'Jogador adicionado.'));
  view.querySelectorAll('[data-del-jogador]').forEach((btn) => {
    btn.addEventListener('click', () => tryRun(async () => {
      await del(`/jogadores/${btn.dataset.delJogador}`);
      await renderJogadoresSub(view);
    }, 'Removido.'));
  });
}

/* ---- Config / identidade ----
   Identidade (nome, cores, logo) mora em Organizacao; prazos de ausência e
   check-in são configuração operacional (Config) — dois recursos, um form. */
async function renderConfigSub(view) {
  const [cfg, org] = await Promise.all([get('/config'), get('/organizacoes/atual')]);
  state.config = cfg;
  state.organizacao = org;
  view.innerHTML = `
    ${subHeader('Identidade e configurações')}
    <div class="panel">
      <label>Nome do grupo</label>
      <input type="text" id="cfg-nome" value="${escapeHtml(org.nome)}">
      <label>Subtítulo</label>
      <input type="text" id="cfg-subtitulo" value="${escapeHtml(org.subtitulo)}">
      <div class="field-row">
        <div><label>Cor primária</label><input type="text" id="cfg-cor" value="${escapeHtml(org.cor_primaria)}" placeholder="#f0603a"></div>
        <div><label>Link de rede social</label><input type="text" id="cfg-social" value="${escapeHtml(org.link_rede_social)}"></div>
      </div>
      <div class="field-row">
        <div><label>Dias p/ RIP</label><input type="number" id="cfg-rip" value="${cfg.dias_para_rip}"></div>
        <div><label>Dias p/ aposentado</label><input type="number" id="cfg-aposentado" value="${cfg.dias_para_aposentado}"></div>
      </div>
      <button class="btn block" id="salvar-config-btn">Salvar</button>
    </div>
  `;
  wireVoltar(view);
  document.getElementById('salvar-config-btn').addEventListener('click', () => tryRun(async () => {
    const [orgAtualizada] = await Promise.all([
      put(`/organizacoes/${org.id}`, {
        nome: document.getElementById('cfg-nome').value,
        subtitulo: document.getElementById('cfg-subtitulo').value,
        cor_primaria: document.getElementById('cfg-cor').value,
        cor_secundaria: org.cor_secundaria,
        logo_url: org.logo_url,
        link_rede_social: document.getElementById('cfg-social').value,
        plano: org.plano,
      }),
      put('/config', {
        ...cfg,
        dias_para_rip: parseInt(document.getElementById('cfg-rip').value, 10) || 60,
        dias_para_aposentado: parseInt(document.getElementById('cfg-aposentado').value, 10) || 100,
      }),
    ]);
    state.organizacao = orgAtualizada;
    aplicarIdentidade(orgAtualizada);
  }, 'Configurações salvas.'));
}

/* ---- Hall da Fama ---- */
async function renderHallSub(view) {
  view.innerHTML = `${subHeader('Hall da Fama')}
    <div class="btn-row"><button class="btn secondary" data-modo="anual">Por ano</button><button class="btn ghost" data-modo="mensal">Por mês</button></div>
    <div id="hall-lista"><div class="empty">Carregando...</div></div>`;
  wireVoltar(view);
  async function carregar(modo) {
    view.querySelectorAll('[data-modo]').forEach((b) => b.classList.toggle('secondary', b.dataset.modo === modo));
    view.querySelectorAll('[data-modo]').forEach((b) => b.classList.toggle('ghost', b.dataset.modo !== modo));
    const lista = await get(`/hall-da-fama?modo=${modo}`);
    document.getElementById('hall-lista').innerHTML = lista.length === 0
      ? '<div class="empty">Sem rodadas com campeão definido ainda.</div>'
      : lista.map((item) => `
        <div class="panel">
          <div class="row-sub">${escapeHtml(item.periodo)}</div>
          ${item.vencedores.map((v) => `<div class="row"><div class="avatar">${iniciais(v.apelido || v.nome)}</div><div class="row-name">${escapeHtml(v.apelido || v.nome)}</div><div class="row-right pill win">${v.count}×</div></div>`).join('')}
        </div>`).join('');
  }
  view.querySelectorAll('[data-modo]').forEach((b) => b.addEventListener('click', () => carregar(b.dataset.modo)));
  carregar('anual');
}

/* ---- Placar ao vivo (100% client-side) ---- */
async function renderPlacarSub(view) {
  const p = state.placar;
  view.innerHTML = `${subHeader('Placar ao vivo')}
    <div class="placar-wrap">
      <div class="placar-side" data-lado="a">
        <input class="placar-name" id="placar-nome-a" value="${escapeHtml(p.nomeA)}">
        <div class="placar-num" id="placar-num-a">${p.a}</div>
        <div class="row-sub">toque para somar</div>
      </div>
      <div class="placar-side" data-lado="b">
        <input class="placar-name" id="placar-nome-b" value="${escapeHtml(p.nomeB)}">
        <div class="placar-num" id="placar-num-b">${p.b}</div>
        <div class="row-sub">toque para somar</div>
      </div>
    </div>
    <div class="btn-row">
      <button class="btn secondary" id="placar-reset">Zerar</button>
      <button class="btn ghost" id="placar-fullscreen">Tela cheia</button>
    </div>`;
  wireVoltar(view);
  view.querySelectorAll('.placar-side').forEach((el) => {
    el.addEventListener('click', (e) => {
      if (e.target.tagName === 'INPUT') return;
      const lado = el.dataset.lado;
      p[lado] += 1;
      document.getElementById(`placar-num-${lado}`).textContent = p[lado];
    });
  });
  document.getElementById('placar-nome-a').addEventListener('input', (e) => { p.nomeA = e.target.value; });
  document.getElementById('placar-nome-b').addEventListener('input', (e) => { p.nomeB = e.target.value; });
  document.getElementById('placar-reset').addEventListener('click', () => {
    p.a = 0; p.b = 0;
    document.getElementById('placar-num-a').textContent = 0;
    document.getElementById('placar-num-b').textContent = 0;
  });
  document.getElementById('placar-fullscreen').addEventListener('click', () => {
    document.documentElement.requestFullscreen?.();
  });
}

/* ---------------- init ---------------- */
(async function init() {
  try {
    const org = await get('/organizacoes/atual');
    state.organizacao = org;
    aplicarIdentidade(org);
  } catch (e) {
    toast('Não consegui conectar na API em ' + API_BASE, true);
  }

  // Clerk carrega via <script async> no index.html — pode não estar pronto ainda
  const esperarClerk = () => new Promise((resolve) => {
    if (window.Clerk) return resolve();
    const check = setInterval(() => { if (window.Clerk) { clearInterval(check); resolve(); } }, 100);
    setTimeout(() => { clearInterval(check); resolve(); }, 8000); // desiste após 8s (ex: bloqueador de script)
  });
  await esperarClerk();
  if (window.Clerk) {
    await window.Clerk.load();
    await carregarUsuarioAtual();
    atualizarBotaoAuth();
    window.Clerk.addListener(async () => {
      await carregarUsuarioAtual();
      atualizarBotaoAuth();
      render();
    });
  }

  switchTab('inicio');
})();
