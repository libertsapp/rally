/**
 * CÓDIGO DO VÔLEI MEME — script AVULSO (não vinculado à planilha).
 *
 * Diferente do script do Vôlei Terça (que fica em Extensões > Apps Script,
 * dentro da própria planilha), este aqui roda separado: vá em
 * https://script.google.com > Novo projeto, cole este código, e configure
 * abaixo o ID da MESMA planilha do Vôlei Terça (compartilhada entre os dois).
 *
 * Como é um script avulso, ele precisa saber QUAL planilha acessar — copie o
 * ID da planilha a partir da URL dela:
 * https://docs.google.com/spreadsheets/d/ESSE-TRECHO-AQUI-É-O-ID/edit
 */
const SPREADSHEET_ID = "1dBAYE5IuUPxEBW75lILO-jqTrJrM11DsFGkpHeKg0iQ";

/**
 * A planilha precisa ter QUATRO abas SÓ PRO VÔLEI MEME (nomes diferentes das
 * abas do Vôlei Terça, mesmo sendo a mesma planilha), com estes nomes EXATOS:
 *   - "JogadoresVoleiMeme"  com cabeçalho na linha 1: id | nome | apelido | foto | estrelas | sexo | porte
 *   - "RodadasVoleiMeme"    com cabeçalho na linha 1: roundId | data | timeIndex | timeNome | jogadores | vitorias | vencedor | rascunho
 *   - "ConfigVoleiMeme"     não precisa de cabeçalho — guarda ajustes gerais do app (ex: exibir estrelas ou não)
 *   - "CheckinsVoleiMeme"   com cabeçalho na linha 1: id | data | jogadorId | jogadorNome | estrelas | sexo
 *
 * PREENCHA ABAIXO o ID de uma SUBPASTA nova, criada dentro da mesma pasta de
 * fotos que o Vôlei Terça já usa — assim as fotos dos dois grupos não se
 * misturam, mas continuam organizadas dentro da mesma pasta raiz do Drive.
 * Copie o ID a partir da URL da subpasta, depois de "folders/".
 */
const DRIVE_FOLDER_ID = "1Tm98j5gmyFDoQ1XSg85JV0yB0RWJbSo4";

/**
 * SENHA DE ADMINISTRADOR DO VÔLEI MEME — use uma senha DIFERENTE da do Vôlei
 * Terça, já que são grupos e admins diferentes. Qualquer pessoa consegue
 * VISUALIZAR o dashboard normalmente, sem senha. Essa senha só é exigida
 * para GRAVAR dados sensíveis (cadastrar jogador, salvar rodada, remover
 * jogador/rodada, enviar foto, mudar configurações).
 * O check-in (confirmar presença) é livre, de propósito, e NÃO pede senha —
 * qualquer jogador precisa poder se confirmar sozinho, sem depender do admin.
 */
const ADMIN_PASSWORD = "2026vmeme";

function doGet(e) {
  try {
    const players = readPlayers(ss_().getSheetByName('JogadoresVoleiMeme'));
    const rounds = readRounds(ss_().getSheetByName('RodadasVoleiMeme'));
    const settings = readSettings(ss_().getSheetByName('ConfigVoleiMeme'));
    const checkins = readCheckins(ss_().getSheetByName('CheckinsVoleiMeme'));
    return jsonOut({ players, rounds, settings, checkins });
  } catch (err) {
    return jsonOut({ error: String(err && err.message ? err.message : err) });
  }
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);

    // check-in é de propósito livre — qualquer jogador confirma presença sem senha
    if (body.action === 'addCheckin' || body.action === 'removeCheckin') {
      const lock = LockService.getScriptLock();
      lock.waitLock(15000);
      try {
        return jsonOut(body.action === 'addCheckin' ? addCheckin(body.checkin) : removeCheckin(body.id));
      } finally {
        lock.releaseLock();
      }
    }

    // contador de acessos — via POST de propósito, porque requisições POST nunca ficam
    // em cache no navegador (diferente de GET, que em alguns casos fica "preso" numa
    // resposta antiga mesmo com cache-busting, dependendo de proxy/extensão do usuário)
    if (body.action === 'incrementarAcesso') {
      const lock = LockService.getScriptLock();
      lock.waitLock(10000);
      try {
        return jsonOut(incrementarAcesso());
      } finally {
        lock.releaseLock();
      }
    }

    // toda gravação sensível (inclusive o "ping" de validação de senha) exige a senha correta
    if (body.senha !== ADMIN_PASSWORD) {
      return jsonOut({ error: 'Senha de administrador incorreta.' });
    }

    if (body.action === 'ping') {
      return jsonOut({ status: 'ok' });
    }
    if (body.action === 'uploadPhoto') {
      return jsonOut(uploadPhoto(body));
    }

    // Todas as ações abaixo MEXEM só na linha específica que mudou (nunca apagam a
    // planilha inteira), e usam um "cadeado" (LockService) pra evitar que duas
    // gravações ao mesmo tempo se atropelem — isso é o que evita perda de dados.
    const lock = LockService.getScriptLock();
    lock.waitLock(15000); // espera até 15s se outra gravação estiver em andamento
    try {
      switch (body.action) {
        case 'addPlayer':
          return jsonOut(addPlayer(body.player));
        case 'updatePlayer':
          return jsonOut(updatePlayer(body.player));
        case 'removePlayer':
          return jsonOut(removePlayer(body.id));
        case 'addRound':
          return jsonOut(addRound(body.round));
        case 'updateRound':
          return jsonOut(updateRound(body.round));
        case 'removeRound':
          return jsonOut(removeRound(body.id));
        case 'saveSettings':
          return jsonOut(saveSettingsAction(body.settings));
        default:
          return jsonOut({ error: 'Ação desconhecida: ' + body.action });
      }
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    return jsonOut({ error: String(err && err.message ? err.message : err) });
  }
}

/* ---------- check-in (livre, sem senha) ---------- */
/* ---------- contador de acessos (via POST, nunca fica em cache) ---------- */
function incrementarAcesso() {
  const sheet = ss_().getSheetByName('ConfigVoleiMeme');
  const settings = readSettings(sheet);
  settings.contadorAcessos = (settings.contadorAcessos || 0) + 1;
  writeSettings(sheet, settings);
  return { contadorAcessos: settings.contadorAcessos };
}

function readCheckins(sheet) {
  if (!sheet) return [];
  const rows = sheet.getDataRange().getValues();
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    const [id, data, jogadorId, jogadorNome, estrelas, sexo] = rows[i];
    if (!id) continue;
    const dataStr = (data instanceof Date)
      ? Utilities.formatDate(data, Session.getScriptTimeZone(), 'yyyy-MM-dd')
      : String(data);
    out.push({
      id: String(id), data: dataStr, jogadorId: String(jogadorId), jogadorNome: String(jogadorNome || ''),
      estrelas: Number(estrelas) || 0, sexo: String(sexo || '')
    });
  }
  return out;
}
function addCheckin(c) {
  const sheet = ss_().getSheetByName('CheckinsVoleiMeme');
  if (!sheet) return { error: 'Aba "Checkins" não encontrada na planilha.' };
  sheet.getRange('B:B').setNumberFormat('@');
  sheet.appendRow([c.id, c.data, c.jogadorId, c.jogadorNome || '', c.estrelas || 0, c.sexo || '']);
  return { status: 'ok' };
}
function removeCheckin(id) {
  const sheet = ss_().getSheetByName('CheckinsVoleiMeme');
  if (!sheet) return { error: 'Aba "Checkins" não encontrada na planilha.' };
  const linha = acharLinhaPorId(sheet, 0, id);
  if (linha === -1) return { error: 'Check-in não encontrado (pode já ter sido desmarcado).' };
  sheet.deleteRow(linha);
  return { status: 'ok' };
}

/* ---------- ações granulares: cada uma mexe só na própria linha ---------- */

function acharLinhaPorId(sheet, colunaId, id) {
  const valores = sheet.getDataRange().getValues();
  for (let i = 1; i < valores.length; i++) {
    if (String(valores[i][colunaId]) === String(id)) return i + 1; // linha 1-based
  }
  return -1;
}

function addPlayer(p) {
  const sheet = ss_().getSheetByName('JogadoresVoleiMeme');
  sheet.appendRow([p.id, p.nome, p.apelido || '', p.foto || '', p.estrelas || 0, p.sexo || '', p.porte || '']);
  return { status: 'ok' };
}

function updatePlayer(p) {
  const sheet = ss_().getSheetByName('JogadoresVoleiMeme');
  const linha = acharLinhaPorId(sheet, 0, p.id);
  if (linha === -1) return { error: 'Jogador não encontrado na planilha (pode já ter sido removido por outra pessoa).' };
  sheet.getRange(linha, 1, 1, 7).setValues([[p.id, p.nome, p.apelido || '', p.foto || '', p.estrelas || 0, p.sexo || '', p.porte || '']]);
  return { status: 'ok' };
}

function removePlayer(id) {
  const sheet = ss_().getSheetByName('JogadoresVoleiMeme');
  const linha = acharLinhaPorId(sheet, 0, id);
  if (linha === -1) return { error: 'Jogador não encontrado (pode já ter sido removido por outra pessoa).' };
  sheet.deleteRow(linha);
  return { status: 'ok' };
}

function addRound(r) {
  const sheet = ss_().getSheetByName('RodadasVoleiMeme');
  sheet.getRange('B:B').setNumberFormat('@'); // garante que a coluna "data" não vire objeto Data
  r.times.forEach((t, idx) => {
    sheet.appendRow([r.id, r.data, idx, t.nome, (t.playerIds || []).join(','), t.vitorias || 0, idx === r.vencedor, !!r.rascunho]);
  });
  return { status: 'ok' };
}

function removeRound(id) {
  const sheet = ss_().getSheetByName('RodadasVoleiMeme');
  const valores = sheet.getDataRange().getValues();
  const linhas = [];
  for (let i = 1; i < valores.length; i++) {
    if (String(valores[i][0]) === String(id)) linhas.push(i + 1);
  }
  if (linhas.length === 0) return { error: 'Rodada não encontrada (pode já ter sido removida por outra pessoa).' };
  // apaga de baixo pra cima, senão os números das linhas seguintes mudam a cada exclusão
  linhas.sort((a, b) => b - a).forEach(linha => sheet.deleteRow(linha));
  return { status: 'ok' };
}

function updateRound(r) {
  // edita = remove as linhas antigas dessa rodada (se existirem) e insere as novas atualizadas
  const sheet = ss_().getSheetByName('RodadasVoleiMeme');
  const valores = sheet.getDataRange().getValues();
  const linhas = [];
  for (let i = 1; i < valores.length; i++) {
    if (String(valores[i][0]) === String(r.id)) linhas.push(i + 1);
  }
  linhas.sort((a, b) => b - a).forEach(linha => sheet.deleteRow(linha));
  return addRound(r);
}

function saveSettingsAction(settings) {
  // o contador de acessos é controlado só pelo doGet — nunca deixa uma gravação de
  // configuração (ex: travar o check-in) sobrescrever com um valor desatualizado
  // que o navegador do admin carregou antes de outras pessoas acessarem o site
  const sheet = ss_().getSheetByName('ConfigVoleiMeme');
  const atual = readSettings(sheet);
  settings.contadorAcessos = atual.contadorAcessos;
  writeSettings(sheet, settings);
  return { status: 'ok' };
}

function readSettings(sheet) {
  const defaults = { estrelasVisiveis: true, checkinDataAberta: '', checkinTravado: false, contadorAcessos: 0 };
  if (!sheet) return defaults;
  const rows = sheet.getDataRange().getValues();
  const out = Object.assign({}, defaults);
  for (let i = 0; i < rows.length; i++) {
    const [key, value] = rows[i];
    if (key === 'estrelasVisiveis') out.estrelasVisiveis = (String(value).toUpperCase() === 'TRUE');
    if (key === 'checkinDataAberta') out.checkinDataAberta = String(value || '');
    if (key === 'checkinTravado') out.checkinTravado = (String(value).toUpperCase() === 'TRUE');
    if (key === 'contadorAcessos') out.contadorAcessos = Number(value) || 0;
  }
  return out;
}

function writeSettings(sheet, settings) {
  if (!sheet) return;
  sheet.clearContents();
  sheet.appendRow(['estrelasVisiveis', settings.estrelasVisiveis ? 'TRUE' : 'FALSE']);
  sheet.appendRow(['checkinDataAberta', settings.checkinDataAberta || '']);
  sheet.appendRow(['checkinTravado', settings.checkinTravado ? 'TRUE' : 'FALSE']);
  sheet.appendRow(['contadorAcessos', settings.contadorAcessos || 0]);
  sheet.getRange('B:B').setNumberFormat('@'); // evita o Sheets converter a data aberta em objeto Data
}

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ss_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

function uploadPhoto(body) {
  const folder = DriveApp.getFolderById(DRIVE_FOLDER_ID);
  const bytes = Utilities.base64Decode(body.base64);
  const blob = Utilities.newBlob(bytes, body.mimeType || 'image/jpeg', body.filename || ('foto_' + Date.now() + '.jpg'));
  const file = folder.createFile(blob);
  // A permissão de acesso público vem da PASTA (compartilhada manualmente uma vez),
  // não é definida arquivo por arquivo — evita o erro "Access denied" de setSharing.
  const url = 'https://drive.google.com/thumbnail?id=' + file.getId() + '&sz=w300';
  return { url: url, fileId: file.getId() };
}

function readPlayers(sheet) {
  const rows = sheet.getDataRange().getValues();
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    const [id, nome, apelido, foto, estrelas, sexo, porte] = rows[i];
    if (!id) continue;
    out.push({
      id: String(id), nome: String(nome || ''), apelido: String(apelido || ''), foto: String(foto || ''),
      estrelas: Number(estrelas) || 0, sexo: String(sexo || ''), porte: String(porte || '')
    });
  }
  return out;
}

function readRounds(sheet) {
  const rows = sheet.getDataRange().getValues();
  const map = {};
  for (let i = 1; i < rows.length; i++) {
    const [roundId, data, timeIndex, timeNome, jogadores, vitorias, vencedor, rascunho] = rows[i];
    if (!roundId) continue;
    const rid = String(roundId);
    // o Sheets às vezes converte o texto "aaaa-mm-dd" automaticamente para um objeto Data —
    // aqui normalizamos de volta para o formato aaaa-mm-dd, senão vira uma string com fuso horário.
    const dataStr = (data instanceof Date)
      ? Utilities.formatDate(data, Session.getScriptTimeZone(), 'yyyy-MM-dd')
      : String(data);
    if (!map[rid]) {
      map[rid] = { id: rid, data: dataStr, times: [], rascunho: (rascunho === true || String(rascunho).toUpperCase() === 'TRUE') };
    }
    map[rid].times[Number(timeIndex)] = {
      nome: String(timeNome || ''),
      playerIds: jogadores ? String(jogadores).split(',').filter(Boolean) : [],
      vitorias: Number(vitorias) || 0
    };
    if (vencedor === true || vencedor === 'true') {
      map[rid].vencedor = Number(timeIndex);
    }
  }
  const rounds = Object.values(map);
  rounds.forEach(r => { if (r.vencedor === undefined) r.vencedor = -1; });
  return rounds;
}

function writePlayers(sheet, players) {
  sheet.clearContents();
  sheet.appendRow(['id', 'nome', 'apelido', 'foto', 'estrelas', 'sexo', 'porte']);
  players.forEach(p => sheet.appendRow([p.id, p.nome, p.apelido || '', p.foto || '', p.estrelas || 0, p.sexo || '', p.porte || '']));
}

function writeRounds(sheet, rounds) {
  sheet.clearContents();
  sheet.appendRow(['roundId', 'data', 'timeIndex', 'timeNome', 'jogadores', 'vitorias', 'vencedor', 'rascunho']);
  sheet.getRange('B:B').setNumberFormat('@'); // coluna "data" sempre como texto, evita o Sheets converter para objeto Data
  rounds.forEach(r => {
    r.times.forEach((t, idx) => {
      sheet.appendRow([
        r.id, r.data, idx, t.nome,
        (t.playerIds || []).join(','),
        t.vitorias || 0,
        idx === r.vencedor,
        !!r.rascunho
      ]);
    });
  });
}
