/**
 * ==============================================================================
 * ANONIMIZADOR SINERGIA - FRONTEND JAVASCRIPT
 * Entrada Universal Omnimodal (Texto • PDF • DOCX) com Fluxo de Alta Velocidade
 * ==============================================================================
 */

(function () {
  'use strict';

  // ── ESTADO GLOBAL DA APLICAÇÃO ─────────────────────────────────────────────
  const state = {
    theme: localStorage.getItem('sinergia-theme') || 'light',
    activeFile: null, // Objeto File (.pdf ou .docx) se carregado
    resultados: null, // { texto_anonimizado, texto_original, entidades_detectadas, tempo_processamento }
    highlightMode: true,
    filtroEntidadeAtual: 'ALL'
  };

  // ── ELEMENTOS DO DOM ───────────────────────────────────────────────────────
  const dom = {
    html: document.documentElement,
    appContainer: document.getElementById('app-container'),
    themeToggle: document.getElementById('btn-theme-toggle'),
    iconSun: document.getElementById('icon-sun'),
    iconMoon: document.getElementById('icon-moon'),
    privacyToggle: document.getElementById('privacy-toggle'),
    privacyCard: document.getElementById('privacy-card'),

    // Entrada Universal
    panelInput: document.getElementById('panel-input'),
    dropzoneUniversal: document.getElementById('dropzone-universal'),
    dragOverlay: document.getElementById('drag-overlay'),
    inputTexto: document.getElementById('input-texto'),
    charCounter: document.getElementById('char-counter'),
    btnAnexarArquivo: document.getElementById('btn-anexar-arquivo'),
    fileInputUniversal: document.getElementById('file-input-universal'),
    fileBadge: document.getElementById('file-badge'),
    fileBadgeName: document.getElementById('file-badge-name'),
    fileBadgeSize: document.getElementById('file-badge-size'),
    btnRemoverArquivo: document.getElementById('btn-remover-arquivo'),
    btnAnonimizar: document.getElementById('btn-anonimizar'),
    btnLimpar: document.getElementById('btn-limpar'),

    // Saída Universal
    panelOutput: document.getElementById('panel-output'),
    viewerTexto: document.getElementById('viewer-texto'),
    btnToggleHighlight: document.getElementById('btn-toggle-highlight'),
    btnCopiar: document.getElementById('btn-copiar'),
    btnDownload: document.getElementById('btn-download'),

    // Estatísticas & Auditoria (Sem Emojis)
    statsSection: document.getElementById('stats-section'),
    statTempo: document.getElementById('stat-tempo'),
    statTotalEntidades: document.getElementById('stat-total-entidades'),
    statTiposEntidades: document.getElementById('stat-tipos-entidades'),
    auditSection: document.getElementById('audit-section'),
    auditFilterChips: document.getElementById('audit-filter-chips'),
    auditTableBody: document.getElementById('audit-table-body'),
    toastContainer: document.getElementById('toast-container')
  };

  // ── 1. GERENCIADOR DE TEMA (CLARO / ESCURO) ────────────────────────────────
  function aplicarTema(tema) {
    state.theme = tema;
    dom.html.setAttribute('data-theme', tema);
    localStorage.setItem('sinergia-theme', tema);

    if (tema === 'dark') {
      dom.iconSun.style.display = 'none';
      dom.iconMoon.style.display = 'block';
    } else {
      dom.iconSun.style.display = 'block';
      dom.iconMoon.style.display = 'none';
    }
  }

  function alternarTema() {
    aplicarTema(state.theme === 'light' ? 'dark' : 'light');
  }

  // ── 2. NOTIFICAÇÕES TOAST (SEM EMOJIS, APENAS ÍCONES VETORIAIS) ───────────
  function mostrarToast(mensagem, tipo = 'success', duracaoMs = 3200) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;

    const svgIcon = tipo === 'success'
      ? `<svg class="toast-icon-svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>`
      : `<svg class="toast-icon-svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;

    toast.innerHTML = `${svgIcon} <span>${mensagem}</span>`;
    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, duracaoMs);
  }

  function copiarParaClipboard(texto, mensagemSucesso = 'Texto copiado com sucesso para a Área de Transferência.') {
    if (!texto || !texto.trim()) return;

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(texto).then(() => {
        mostrarToast(mensagemSucesso, 'success');
      }).catch(() => fallbackCopiar(texto, mensagemSucesso));
    } else {
      fallbackCopiar(texto, mensagemSucesso);
    }
  }

  function fallbackCopiar(texto, mensagemSucesso) {
    const textarea = document.createElement('textarea');
    textarea.value = texto;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      mostrarToast(mensagemSucesso, 'success');
    } catch (err) {
      mostrarToast('Não foi possível copiar o texto automaticamente.', 'error');
    }
    document.body.removeChild(textarea);
  }

  function baixarArquivoTexto(conteudo, nomeArquivo = 'documento_anonimizado.txt') {
    if (!conteudo) return;
    const blob = new Blob([conteudo], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nomeArquivo;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    mostrarToast('Download do documento iniciado.', 'success');
  }

  // ── 3. FORMATAÇÃO E DESTAQUES DE ENTIDADES ─────────────────────────────────
  function classificarTagEntidade(token) {
    const u = (token || '').toUpperCase();
    if (u.includes('NOME')) return 'tag-nome';
    if (u.includes('CPF') || u.includes('CIN') || u.includes('RG') || u.includes('CNH') || u.includes('SIAPE')) return 'tag-doc';
    if (u.includes('OAB')) return 'tag-oab';
    if (u.includes('ENDERECO') || u.includes('CEP') || u.includes('LOCATION')) return 'tag-loc';
    if (u.includes('EMAIL') || u.includes('PHONE') || u.includes('TELEFONE')) return 'tag-contato';
    return 'tag-doc';
  }

  function escaparHtml(texto) {
    if (!texto) return '';
    return texto
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function gerarHtmlComDestaques(textoAnonimizado) {
    if (!textoAnonimizado) return '';
    const textoEscapado = escaparHtml(textoAnonimizado);
    return textoEscapado.replace(/&lt;([A-Z0-9_\/\s-]+)&gt;/g, (match, p1) => {
      const classe = classificarTagEntidade(p1);
      return `<span class="entity-tag ${classe}" title="Dado Anonimizado: ${p1}">&lt;${p1}&gt;</span>`;
    });
  }

  // ── 4. GERENCIAMENTO DE ARQUIVOS (PDF & DOCX) ──────────────────────────────
  function carregarArquivo(file) {
    if (!file) return;

    const nome = file.name.toLowerCase();
    if (!nome.endsWith('.pdf') && !nome.endsWith('.docx')) {
      mostrarToast('Formato não suportado. Envie um arquivo PDF (.pdf) ou Word (.docx).', 'error');
      return;
    }

    const tamanhoMb = file.size / (1024 * 1024);
    if (tamanhoMb > 40) {
      mostrarToast('O arquivo selecionado ultrapassa o limite permitido de 40 MB.', 'error');
      return;
    }

    state.activeFile = file;
    dom.fileBadgeName.textContent = file.name;
    dom.fileBadgeSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
    dom.fileBadge.style.display = 'flex';
    dom.inputTexto.placeholder = `Arquivo "${file.name}" anexado e pronto para anonimização. Você também pode digitar observações adicionais ou acionar o botão abaixo.`;
    dom.btnAnonimizar.disabled = false;
    mostrarToast(`Arquivo "${file.name}" carregado.`, 'success');
  }

  function removerArquivo() {
    state.activeFile = null;
    dom.fileInputUniversal.value = '';
    dom.fileBadge.style.display = 'none';
    dom.inputTexto.placeholder = 'Cole o texto da peça jurídica aqui, ou arraste e solte arquivos PDF e Word (.docx)...';
    dom.btnAnonimizar.disabled = dom.inputTexto.value.trim().length === 0;
  }

  // ── 5. PROCESSAMENTO UNIVERSAL (TEXTO, PDF E DOCX) COM AUTO-COPY ───────────
  async function processarUniversal() {
    const texto = dom.inputTexto.value.trim();
    const arquivo = state.activeFile;

    if (!texto && !arquivo) {
      mostrarToast('Insira um texto ou anexe um arquivo PDF/Word para anonimizar.', 'error');
      return;
    }

    const btnOriginalHtml = dom.btnAnonimizar.innerHTML;
    dom.btnAnonimizar.disabled = true;
    dom.btnAnonimizar.innerHTML = '<span class="spinner"></span> <span>Anonimizando...</span>';

    try {
      let data = null;

      if (arquivo) {
        // Envio via endpoint de arquivo
        const formData = new FormData();
        formData.append('file', arquivo);

        const response = await fetch('/api/v1/anonimizar-arquivo', {
          method: 'POST',
          body: formData
        });

        data = await response.json();
        if (!response.ok || !data.sucesso) {
          throw new Error(data.erro || 'Falha ao processar arquivo.');
        }

        // Se o textarea estava vazio, preenche com o texto extraído
        if (!dom.inputTexto.value.trim() && data.texto_extraido) {
          dom.inputTexto.value = data.texto_extraido;
          dom.charCounter.textContent = `${data.texto_extraido.length.toLocaleString('pt-BR')} caracteres`;
        }

      } else {
        // Envio via endpoint de texto puro
        const response = await fetch('/api/v1/anonimizar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ texto, nomes_metadados: [] })
        });

        if (!response.ok) {
          throw new Error(`Erro no servidor: ${response.status}`);
        }

        data = await response.json();
        data.texto_original = texto;
        data.sucesso = true;
      }

      state.resultados = data;
      renderizarResultados(data);
      renderizarAuditoriaEEstatisticas(data);

      // Auto-cópia imediata para a área de transferência
      if (data.texto_anonimizado) {
        copiarParaClipboard(data.texto_anonimizado, 'Documento anonimizado e copiado para a Área de Transferência!');
      }

    } catch (err) {
      console.error(err);
      mostrarToast(err.message, 'error');
    } finally {
      dom.btnAnonimizar.disabled = false;
      dom.btnAnonimizar.innerHTML = btnOriginalHtml;
    }
  }

  function renderizarResultados(data) {
    if (!data) return;

    if (state.highlightMode) {
      dom.viewerTexto.innerHTML = gerarHtmlComDestaques(data.texto_anonimizado);
    } else {
      dom.viewerTexto.textContent = data.texto_anonimizado;
    }

    dom.btnCopiar.disabled = false;
    dom.btnDownload.disabled = false;
    dom.btnToggleHighlight.style.display = 'inline-flex';
  }

  function alternarHighlight() {
    state.highlightMode = !state.highlightMode;
    if (state.resultados) {
      renderizarResultados(state.resultados);
    }
  }

  function limparTudo() {
    dom.inputTexto.value = '';
    dom.charCounter.textContent = '0 caracteres';
    dom.btnAnonimizar.disabled = true;
    dom.btnCopiar.disabled = true;
    dom.btnDownload.disabled = true;
    dom.btnToggleHighlight.style.display = 'none';
    removerArquivo();

    dom.viewerTexto.innerHTML = `
      <div class="viewer-empty-state">
        <div class="empty-art-wrapper">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            <circle cx="12" cy="11" r="2.5"></circle>
            <line x1="12" y1="8.5" x2="12" y2="5"></line>
            <line x1="12" y1="13.5" x2="12" y2="17"></line>
            <line x1="9.5" y1="11" x2="6.5" y2="11"></line>
            <line x1="14.5" y1="11" x2="17.5" y2="11"></line>
          </svg>
        </div>
        <div class="empty-state-title">Proteção Inteligente de Dados</div>
        <div class="empty-state-desc">Cole um texto ou envie um arquivo PDF/Word para mascarar dados sensíveis e copiar o resultado com 1 clique.</div>
      </div>
    `;

    state.resultados = null;
    dom.statsSection.style.display = 'none';
    dom.auditSection.style.display = 'none';
  }

  // ── 6. ESTATÍSTICAS E AUDITORIA (SEM EMOJIS) ───────────────────────────────
  function renderizarAuditoriaEEstatisticas(data) {
    if (!data) return;

    const entidades = data.entidades_detectadas || [];
    const tempo = data.tempo_processamento || 0;

    dom.statTempo.textContent = `${tempo.toFixed(2)}s`;
    dom.statTotalEntidades.textContent = entidades.length;

    const contagemPorTipo = {};
    entidades.forEach(e => {
      const tipo = e.Entidade || 'OUTRO';
      contagemPorTipo[tipo] = (contagemPorTipo[tipo] || 0) + 1;
    });

    const totalTipos = Object.keys(contagemPorTipo).length;
    dom.statTiposEntidades.textContent = totalTipos;
    dom.statsSection.style.display = 'grid';

    dom.auditFilterChips.innerHTML = `
      <button class="filter-chip ${state.filtroEntidadeAtual === 'ALL' ? 'active' : ''}" data-filter="ALL">Todas (${entidades.length})</button>
    `;

    Object.entries(contagemPorTipo).sort((a, b) => b[1] - a[1]).forEach(([tipo, qtd]) => {
      const chip = document.createElement('button');
      chip.className = `filter-chip ${state.filtroEntidadeAtual === tipo ? 'active' : ''}`;
      chip.dataset.filter = tipo;
      chip.textContent = `${tipo} (${qtd})`;
      dom.auditFilterChips.appendChild(chip);
    });

    renderizarLinhasTabela(entidades, state.filtroEntidadeAtual);
    dom.auditSection.style.display = 'block';
  }

  function renderizarLinhasTabela(entidades, filtro) {
    dom.auditTableBody.innerHTML = '';

    const filtradas = filtro === 'ALL' 
      ? entidades 
      : entidades.filter(e => e.Entidade === filtro);

    if (filtradas.length === 0) {
      dom.auditTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--color-text-muted); padding: 24px;">Nenhuma entidade encontrada para este filtro.</td></tr>';
      return;
    }

    filtradas.forEach(e => {
      const tr = document.createElement('tr');
      const classe = classificarTagEntidade(e.Entidade || '');
      tr.innerHTML = `
        <td><span class="entity-tag ${classe}">${e.Entidade}</span></td>
        <td><strong>${escaparHtml(e['Texto Detectado'] || '-')}</strong></td>
        <td>${e['Início'] !== undefined ? e['Início'] : '-'}</td>
        <td>${e['Fim'] !== undefined ? e['Fim'] : '-'}</td>
        <td>${e['Score'] || '1.00'}</td>
      `;
      dom.auditTableBody.appendChild(tr);
    });
  }

  // ── 7. ROLAGEM SINCRONIZADA (SYNC SCROLL) ──────────────────────────────────
  function inicializarRolagemSincronizada() {
    let bloqueioScroll = false;

    function sincronizar(origem, destino) {
      if (bloqueioScroll) return;
      bloqueioScroll = true;

      const maxOrigem = origem.scrollHeight - origem.clientHeight;
      const maxDestino = destino.scrollHeight - destino.clientHeight;

      if (maxOrigem > 0 && maxDestino > 0) {
        const proporcao = origem.scrollTop / maxOrigem;
        destino.scrollTop = proporcao * maxDestino;
      }

      requestAnimationFrame(() => {
        bloqueioScroll = false;
      });
    }

    dom.inputTexto.addEventListener('scroll', () => sincronizar(dom.inputTexto, dom.viewerTexto));
    dom.viewerTexto.addEventListener('scroll', () => sincronizar(dom.viewerTexto, dom.inputTexto));
  }

  // ── 8. INICIALIZAÇÃO E EVENT LISTENERS ─────────────────────────────────────
  function inicializarEventos() {
    // Tema
    aplicarTema(state.theme);
    dom.themeToggle.addEventListener('click', alternarTema);

    // Banner de Privacidade
    dom.privacyToggle.addEventListener('click', () => {
      dom.privacyCard.classList.toggle('open');
    });

    // Entrada de Texto
    dom.inputTexto.addEventListener('input', () => {
      const len = dom.inputTexto.value.length;
      dom.charCounter.textContent = `${len.toLocaleString('pt-BR')} caracteres`;
      dom.btnAnonimizar.disabled = len === 0 && !state.activeFile;
    });

    dom.inputTexto.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!dom.btnAnonimizar.disabled) {
          processarUniversal();
        }
      }
    });

    // Botões de Ação
    dom.btnAnonimizar.addEventListener('click', processarUniversal);
    dom.btnLimpar.addEventListener('click', limparTudo);
    dom.btnToggleHighlight.addEventListener('click', alternarHighlight);

    dom.btnCopiar.addEventListener('click', () => {
      if (state.resultados) {
        copiarParaClipboard(state.resultados.texto_anonimizado, 'Texto copiado com sucesso para a Área de Transferência.');
      }
    });

    dom.btnDownload.addEventListener('click', () => {
      if (state.resultados) {
        baixarArquivoTexto(state.resultados.texto_anonimizado, 'documento_anonimizado_sinergia.txt');
      }
    });

    // Anexar Arquivo via Botão
    dom.btnAnexarArquivo.addEventListener('click', () => dom.fileInputUniversal.click());
    dom.fileInputUniversal.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        carregarArquivo(e.target.files[0]);
      }
    });

    dom.btnRemoverArquivo.addEventListener('click', removerArquivo);

    // Drag & Drop Universal sobre o painel de entrada
    ['dragenter', 'dragover'].forEach(eventName => {
      dom.panelInput.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dom.panelInput.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dom.panelInput.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dom.panelInput.classList.remove('dragover');
      });
    });

    dom.panelInput.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        carregarArquivo(e.dataTransfer.files[0]);
      }
    });

    // Suporte a colar arquivos diretamente do Windows Explorer (Ctrl+V)
    window.addEventListener('paste', (e) => {
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const file = e.clipboardData.files[0];
        const nome = file.name.toLowerCase();
        if (nome.endsWith('.pdf') || nome.endsWith('.docx')) {
          e.preventDefault();
          carregarArquivo(file);
        }
      }
    });

    // Filtros de Auditoria
    dom.auditFilterChips.addEventListener('click', (e) => {
      const chip = e.target.closest('.filter-chip');
      if (!chip) return;

      dom.auditFilterChips.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      state.filtroEntidadeAtual = chip.dataset.filter;
      if (state.resultados) {
        renderizarLinhasTabela(state.resultados.entidades_detectadas || [], state.filtroEntidadeAtual);
      }
    });

    // Rolagem Sincronizada
    inicializarRolagemSincronizada();
  }

  document.addEventListener('DOMContentLoaded', inicializarEventos);

})();
