/**
 * ==============================================================================
 * ANONIMIZADOR SINERGIA - FRONTEND JAVASCRIPT
 * Opção C: Layout Híbrido Flexível (Split View • Documento Focado • Inline Diff)
 * ==============================================================================
 */

(function () {
  'use strict';

  // ── ESTADO GLOBAL DA APLICAÇÃO ─────────────────────────────────────────────
  const state = {
    theme: localStorage.getItem('sinergia-theme') || 'light',
    activeTab: 'tab-texto',
    viewMode: localStorage.getItem('sinergia-view-mode') || 'split', // 'split' | 'focus' | 'diff'
    textoResultados: null, // { texto_anonimizado, texto_original, entidades_detectadas, tempo_processamento }
    pdfResultados: null,
    highlightModeTexto: true,
    filtroEntidadeAtual: 'ALL',
    focusShowingInput: false
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
    navTabs: document.querySelectorAll('.nav-tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Controles de Modo de Exibição (Opção C)
    viewModeBtns: document.querySelectorAll('.view-mode-btn'),
    btnModeSplit: document.getElementById('btn-mode-split'),
    btnModeFocus: document.getElementById('btn-mode-focus'),
    btnModeDiff: document.getElementById('btn-mode-diff'),
    btnSwitchFocusEdit: document.getElementById('btn-switch-focus-edit'),
    outputPanelTitle: document.getElementById('output-panel-title'),

    // Aba Texto
    panelInputTexto: document.getElementById('panel-input-texto'),
    panelOutputTexto: document.getElementById('panel-output-texto'),
    inputTexto: document.getElementById('input-texto'),
    charCounter: document.getElementById('char-counter'),
    btnAnonimizarTexto: document.getElementById('btn-anonimizar-texto'),
    btnLimparTexto: document.getElementById('btn-limpar-texto'),
    viewerTexto: document.getElementById('viewer-texto'),
    btnCopiarTexto: document.getElementById('btn-copiar-texto'),
    btnDownloadTexto: document.getElementById('btn-download-texto'),
    btnToggleHighlightTexto: document.getElementById('btn-toggle-highlight-texto'),

    // Aba PDF
    dropzone: document.getElementById('dropzone'),
    fileInputPdf: document.getElementById('file-input-pdf'),
    pdfFileBadge: document.getElementById('pdf-file-badge'),
    pdfFileName: document.getElementById('pdf-file-name'),
    pdfFileSize: document.getElementById('pdf-file-size'),
    btnRemoverPdf: document.getElementById('btn-remover-pdf'),
    viewerPdfOriginal: document.getElementById('viewer-pdf-original'),
    viewerPdfAnonimizado: document.getElementById('viewer-pdf-anonimizado'),
    btnCopiarPdf: document.getElementById('btn-copiar-pdf'),
    btnDownloadPdf: document.getElementById('btn-download-pdf'),

    // Estatísticas & Auditoria
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

  // ── 2. GERENCIADOR DE MODOS DE EXIBIÇÃO (OPÇÃO C) ──────────────────────────
  function aplicarModoExibicao(modo) {
    state.viewMode = modo;
    localStorage.setItem('sinergia-view-mode', modo);

    // Atualiza classes do container principal
    dom.appContainer.classList.remove('layout-split', 'layout-focus', 'layout-diff');
    dom.appContainer.classList.add(`layout-${modo}`);

    // Atualiza botões ativos
    dom.viewModeBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === modo);
    });

    // Ajustes específicos do modo
    if (modo === 'focus') {
      if (dom.btnSwitchFocusEdit) {
        dom.btnSwitchFocusEdit.style.display = state.textoResultados ? 'inline-flex' : 'none';
      }
      if (dom.outputPanelTitle) {
        dom.outputPanelTitle.innerHTML = `
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <rect x="4" y="3" width="16" height="18" rx="2" ry="2"></rect>
            <line x1="8" y1="8" x2="16" y2="8"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
          Documento Anonimizado (Visão Ampla)
        `;
      }
    } else if (modo === 'diff') {
      if (dom.btnSwitchFocusEdit) dom.btnSwitchFocusEdit.style.display = 'none';
      if (dom.outputPanelTitle) {
        dom.outputPanelTitle.innerHTML = `
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <polyline points="16 3 21 3 21 8"></polyline>
            <line x1="4" y1="20" x2="21" y2="3"></line>
            <polyline points="21 16 21 21 16 21"></polyline>
          </svg>
          Comparação Diff (Dado Suprimido vs Tag)
        `;
      }
    } else {
      // Split
      if (dom.btnSwitchFocusEdit) dom.btnSwitchFocusEdit.style.display = 'none';
      if (dom.panelInputTexto) dom.panelInputTexto.classList.remove('show-input');
      if (dom.panelOutputTexto) dom.panelOutputTexto.classList.remove('hide-output');
      if (dom.outputPanelTitle) {
        dom.outputPanelTitle.innerHTML = `
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          Texto Anonimizado
        `;
      }
    }

    // Re-renderiza o resultado na visualização adequada
    if (state.activeTab === 'tab-texto' && state.textoResultados) {
      renderizarResultadoTexto(state.textoResultados);
    } else if (state.activeTab === 'tab-pdf' && state.pdfResultados) {
      renderizarResultadoPdf(state.pdfResultados);
    }
  }

  // ── 3. GERENCIADOR DE ABAS ─────────────────────────────────────────────────
  function alternarAba(tabId) {
    state.activeTab = tabId;
    dom.navTabs.forEach(tab => {
      const active = tab.dataset.tab === tabId;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active);
    });

    dom.tabContents.forEach(content => {
      content.style.display = content.id === tabId ? 'block' : 'none';
    });

    const resultados = tabId === 'tab-texto' ? state.textoResultados : state.pdfResultados;
    if (resultados && resultados.entidades_detectadas && resultados.entidades_detectadas.length > 0) {
      renderizarAuditoriaEEstatisticas(resultados);
    } else {
      dom.statsSection.style.display = 'none';
      dom.auditSection.style.display = 'none';
    }
  }

  // ── 4. MOTOR DE DESTAQUES & INLINE DIFF ─────────────────────────────────────
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
      return `<span class="entity-tag ${classe}" title="Entidade Anonimizada: ${p1}">&lt;${p1}&gt;</span>`;
    });
  }

  function gerarHtmlDiffInline(textoOriginal, entidades) {
    if (!textoOriginal) return '';
    if (!entidades || entidades.length === 0) {
      return escaparHtml(textoOriginal);
    }

    // Ordena entidades por posição inicial (crescente)
    const sorted = [...entidades]
      .filter(e => e['Início'] !== undefined && e['Fim'] !== undefined)
      .sort((a, b) => a['Início'] - b['Início']);

    let html = '';
    let lastIdx = 0;

    for (const ent of sorted) {
      const start = ent['Início'];
      const end = ent['Fim'];
      const textDetectado = ent['Texto Detectado'] || textoOriginal.substring(start, end);
      const tipo = ent['Entidade'] || 'DADO_PESSOAL';
      const classe = classificarTagEntidade(tipo);

      if (start < lastIdx) continue; // Evita sobreposições

      // Adiciona texto intermediário
      html += escaparHtml(textoOriginal.substring(lastIdx, start));

      // Adiciona o elemento Diff
      html += `<span class="diff-del" title="Dado Original">${escaparHtml(textDetectado)}</span><span class="entity-tag ${classe} diff-ins" title="Substituído por: &lt;${tipo}&gt;">&lt;${tipo}&gt;</span>`;

      lastIdx = end;
    }

    // Adiciona resto do texto
    html += escaparHtml(textoOriginal.substring(lastIdx));
    return html;
  }

  // ── 5. TOASTS & NOTIFICAÇÕES ───────────────────────────────────────────────
  function mostrarToast(mensagem, tipo = 'success', duracaoMs = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    const icone = tipo === 'success' ? '✓' : '⚠️';
    toast.innerHTML = `<span>${icone}</span> <span>${mensagem}</span>`;

    dom.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, duracaoMs);
  }

  function copiarParaClipboard(texto, mensagemSucesso = 'Texto copiado com sucesso!') {
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
      mostrarToast('Não foi possível copiar o texto.', 'error');
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
    mostrarToast('Download iniciado!', 'success');
  }

  // ── 6. PROCESSAMENTO: ABA TEXTO ────────────────────────────────────────────
  async function processarTexto() {
    const texto = dom.inputTexto.value.trim();
    if (!texto) {
      mostrarToast('Cole ou digite um texto para anonimizar.', 'error');
      return;
    }

    const btnTextoOriginal = dom.btnAnonimizarTexto.innerHTML;
    dom.btnAnonimizarTexto.disabled = true;
    dom.btnAnonimizarTexto.innerHTML = '<span class="spinner"></span> <span>Processando...</span>';

    try {
      const response = await fetch('/api/v1/anonimizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto, nomes_metadados: [] })
      });

      if (!response.ok) {
        throw new Error(`Erro no servidor: ${response.status}`);
      }

      const data = await response.json();
      data.texto_original = texto;
      state.textoResultados = data;

      renderizarResultadoTexto(data);
      renderizarAuditoriaEEstatisticas(data);

      if (state.viewMode === 'focus') {
        aplicarModoExibicao('focus');
      }

      mostrarToast('Texto anonimizado com sucesso!', 'success');

    } catch (err) {
      console.error(err);
      mostrarToast(`Falha ao processar: ${err.message}`, 'error');
    } finally {
      dom.btnAnonimizarTexto.disabled = false;
      dom.btnAnonimizarTexto.innerHTML = btnTextoOriginal;
    }
  }

  function renderizarResultadoTexto(data) {
    if (!data) return;

    if (state.viewMode === 'diff') {
      dom.viewerTexto.innerHTML = gerarHtmlDiffInline(data.texto_original, data.entidades_detectadas);
    } else if (state.highlightModeTexto) {
      dom.viewerTexto.innerHTML = gerarHtmlComDestaques(data.texto_anonimizado);
    } else {
      dom.viewerTexto.textContent = data.texto_anonimizado;
    }

    dom.btnCopiarTexto.disabled = false;
    dom.btnDownloadTexto.disabled = false;
    dom.btnToggleHighlightTexto.style.display = state.viewMode === 'diff' ? 'none' : 'inline-flex';
    if (dom.btnSwitchFocusEdit) {
      dom.btnSwitchFocusEdit.style.display = state.viewMode === 'focus' ? 'inline-flex' : 'none';
    }
  }

  function alternarHighlightTexto() {
    state.highlightModeTexto = !state.highlightModeTexto;
    if (state.textoResultados) {
      renderizarResultadoTexto(state.textoResultados);
    }
  }

  function limparAbaTexto() {
    dom.inputTexto.value = '';
    dom.charCounter.textContent = '0 caracteres';
    dom.btnAnonimizarTexto.disabled = true;
    dom.btnCopiarTexto.disabled = true;
    dom.btnDownloadTexto.disabled = true;
    dom.btnToggleHighlightTexto.style.display = 'none';
    if (dom.btnSwitchFocusEdit) dom.btnSwitchFocusEdit.style.display = 'none';
    
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
        <div class="empty-state-desc">Cole uma peça jurídica e clique em <strong>Anonimizar Texto</strong> para identificar e mascarar dados sensíveis.</div>
      </div>
    `;
    state.textoResultados = null;
    dom.statsSection.style.display = 'none';
    dom.auditSection.style.display = 'none';
  }

  // ── 7. PROCESSAMENTO: ABA PDF ──────────────────────────────────────────────
  async function processarArquivoPdf(arquivo) {
    if (!arquivo) return;

    if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
      mostrarToast('Por favor, selecione um arquivo em formato PDF.', 'error');
      return;
    }

    const tamanhoMb = arquivo.size / (1024 * 1024);
    if (tamanhoMb > 40) {
      mostrarToast('O arquivo selecionado ultrapassa o limite de 40 MB.', 'error');
      return;
    }

    dom.pdfFileName.textContent = arquivo.name;
    dom.pdfFileSize.textContent = `${(arquivo.size / 1024).toFixed(1)} KB`;
    dom.pdfFileBadge.classList.add('active');

    dom.viewerPdfOriginal.innerHTML = '<div class="viewer-empty-state"><span class="spinner" style="border-color: var(--jf-azul); border-top-color: transparent;"></span><p>Extraindo texto do PDF...</p></div>';
    dom.viewerPdfAnonimizado.innerHTML = '<div class="viewer-empty-state"><span class="spinner" style="border-color: var(--jf-azul); border-top-color: transparent;"></span><p>Anonimizando conteúdo...</p></div>';

    const formData = new FormData();
    formData.append('file', arquivo);

    try {
      const response = await fetch('/api/v1/anonimizar-pdf', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok || !data.sucesso) {
        throw new Error(data.erro || 'Falha ao processar PDF.');
      }

      state.pdfResultados = data;
      renderizarResultadoPdf(data);
      renderizarAuditoriaEEstatisticas(data);
      mostrarToast('PDF anonimizado com sucesso!', 'success');

    } catch (err) {
      console.error(err);
      dom.viewerPdfOriginal.innerHTML = `<div class="viewer-empty-state" style="color: var(--color-error);"><p>Erro: ${err.message}</p></div>`;
      dom.viewerPdfAnonimizado.innerHTML = '<div class="viewer-empty-state"><p>Não foi possível gerar a versão anonimizada.</p></div>';
      mostrarToast(err.message, 'error');
    }
  }

  function renderizarResultadoPdf(data) {
    if (!data) return;
    dom.viewerPdfOriginal.textContent = data.texto_extraido;

    if (state.viewMode === 'diff') {
      dom.viewerPdfAnonimizado.innerHTML = gerarHtmlDiffInline(data.texto_extraido, data.entidades_detectadas);
    } else {
      dom.viewerPdfAnonimizado.innerHTML = gerarHtmlComDestaques(data.texto_anonimizado);
    }

    dom.btnCopiarPdf.disabled = false;
    dom.btnDownloadPdf.disabled = false;
  }

  function removerArquivoPdf() {
    dom.fileInputPdf.value = '';
    dom.pdfFileBadge.classList.remove('active');
    dom.viewerPdfOriginal.innerHTML = '<div class="viewer-empty-state"><p>Envie um arquivo PDF pesquisável para visualizar o conteúdo extraído.</p></div>';
    dom.viewerPdfAnonimizado.innerHTML = '<div class="viewer-empty-state"><p>O texto do PDF devidamente anonimizado aparecerá aqui após o processamento.</p></div>';
    dom.btnCopiarPdf.disabled = true;
    dom.btnDownloadPdf.disabled = true;
    state.pdfResultados = null;
    dom.statsSection.style.display = 'none';
    dom.auditSection.style.display = 'none';
  }

  // ── 8. ROLAGEM SINCRONIZADA (SYNC SCROLL) ──────────────────────────────────
  function inicializarRolagemSincronizada() {
    let bloqueioScroll = false;

    function sincronizar(origem, destino) {
      if (bloqueioScroll || state.viewMode !== 'split') return;
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

    // Sincronia na Aba Texto
    dom.inputTexto.addEventListener('scroll', () => sincronizar(dom.inputTexto, dom.viewerTexto));
    dom.viewerTexto.addEventListener('scroll', () => sincronizar(dom.viewerTexto, dom.inputTexto));

    // Sincronia na Aba PDF
    dom.viewerPdfOriginal.addEventListener('scroll', () => sincronizar(dom.viewerPdfOriginal, dom.viewerPdfAnonimizado));
    dom.viewerPdfAnonimizado.addEventListener('scroll', () => sincronizar(dom.viewerPdfAnonimizado, dom.viewerPdfOriginal));
  }

  // ── 9. ESTATÍSTICAS E AUDITORIA ────────────────────────────────────────────
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

  // ── 10. INICIALIZAÇÃO E EVENT LISTENERS ─────────────────────────────────────
  function inicializarEventos() {
    // Tema
    aplicarTema(state.theme);
    dom.themeToggle.addEventListener('click', alternarTema);

    // Modo de Exibição (Opção C)
    aplicarModoExibicao(state.viewMode);
    dom.viewModeBtns.forEach(btn => {
      btn.addEventListener('click', () => aplicarModoExibicao(btn.dataset.mode));
    });

    // Botão Voltar para Editar no modo foco
    if (dom.btnSwitchFocusEdit) {
      dom.btnSwitchFocusEdit.addEventListener('click', () => {
        state.focusShowingInput = !state.focusShowingInput;
        if (state.focusShowingInput) {
          dom.panelInputTexto.classList.add('show-input');
          dom.panelOutputTexto.classList.add('hide-output');
          dom.btnSwitchFocusEdit.innerHTML = `
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            Ver Documento
          `;
        } else {
          dom.panelInputTexto.classList.remove('show-input');
          dom.panelOutputTexto.classList.remove('hide-output');
          dom.btnSwitchFocusEdit.innerHTML = `
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Editar Texto
          `;
        }
      });
    }

    // Banner de Privacidade
    dom.privacyToggle.addEventListener('click', () => {
      dom.privacyCard.classList.toggle('open');
    });

    // Abas
    dom.navTabs.forEach(tab => {
      tab.addEventListener('click', () => alternarAba(tab.dataset.tab));
    });

    // Aba Texto
    dom.inputTexto.addEventListener('input', () => {
      const len = dom.inputTexto.value.length;
      dom.charCounter.textContent = `${len.toLocaleString('pt-BR')} caracteres`;
      dom.btnAnonimizarTexto.disabled = len === 0;
    });

    dom.inputTexto.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!dom.btnAnonimizarTexto.disabled) {
          processarTexto();
        }
      }
    });

    dom.btnAnonimizarTexto.addEventListener('click', processarTexto);
    dom.btnLimparTexto.addEventListener('click', limparAbaTexto);
    dom.btnToggleHighlightTexto.addEventListener('click', alternarHighlightTexto);

    dom.btnCopiarTexto.addEventListener('click', () => {
      if (state.textoResultados) {
        copiarParaClipboard(state.textoResultados.texto_anonimizado);
      }
    });

    dom.btnDownloadTexto.addEventListener('click', () => {
      if (state.textoResultados) {
        baixarArquivoTexto(state.textoResultados.texto_anonimizado, 'texto_anonimizado_sinergia.txt');
      }
    });

    // Aba PDF
    dom.dropzone.addEventListener('click', () => dom.fileInputPdf.click());
    dom.fileInputPdf.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        processarArquivoPdf(e.target.files[0]);
      }
    });

    dom.dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dom.dropzone.classList.add('dragover');
    });

    dom.dropzone.addEventListener('dragleave', () => {
      dom.dropzone.classList.remove('dragover');
    });

    dom.dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dom.dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        processarArquivoPdf(e.dataTransfer.files[0]);
      }
    });

    dom.btnRemoverPdf.addEventListener('click', removerArquivoPdf);

    dom.btnCopiarPdf.addEventListener('click', () => {
      if (state.pdfResultados) {
        copiarParaClipboard(state.pdfResultados.texto_anonimizado);
      }
    });

    dom.btnDownloadPdf.addEventListener('click', () => {
      if (state.pdfResultados) {
        baixarArquivoTexto(state.pdfResultados.texto_anonimizado, 'pdf_anonimizado_sinergia.txt');
      }
    });

    // Filtros de Auditoria
    dom.auditFilterChips.addEventListener('click', (e) => {
      const chip = e.target.closest('.filter-chip');
      if (!chip) return;

      dom.auditFilterChips.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      state.filtroEntidadeAtual = chip.dataset.filter;
      const resultados = state.activeTab === 'tab-texto' ? state.textoResultados : state.pdfResultados;
      if (resultados) {
        renderizarLinhasTabela(resultados.entidades_detectadas || [], state.filtroEntidadeAtual);
      }
    });

    // Rolagem Sincronizada
    inicializarRolagemSincronizada();
  }

  document.addEventListener('DOMContentLoaded', inicializarEventos);

})();
