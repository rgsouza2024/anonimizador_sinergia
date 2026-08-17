"""Gradio interface construction for the anonymizer app."""

import gradio as gr


CUSTOM_CSS = """
:root {
    --sinergia-font: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif;
    --sinergia-primary: #0b5cab;
    --sinergia-primary-hover: #084987;
    --sinergia-primary-active: #063868;
    --sinergia-primary-light: #e8f1fa;
    --sinergia-primary-ring: rgba(11, 92, 171, 0.25);
    --sinergia-bg-page: #f8fafc;
    --sinergia-bg-surface: #ffffff;
    --sinergia-bg-subtle: #f1f5f9;
    --sinergia-border: #cbd5e1;
    --sinergia-border-subtle: #e2e8f0;
    --sinergia-text-main: #0f172a;
    --sinergia-text-muted: #64748b;
    --sinergia-success: #16a34a;
    --sinergia-success-bg: #f0fdf4;
    --sinergia-success-border: #bbf7d0;
    --sinergia-radius-sm: 6px;
    --sinergia-radius-md: 10px;
    --sinergia-radius-lg: 14px;
    --sinergia-shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --sinergia-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
}

.dark {
    --sinergia-primary: #38bdf8;
    --sinergia-primary-hover: #0ea5e9;
    --sinergia-primary-active: #0284c7;
    --sinergia-primary-light: #082f49;
    --sinergia-primary-ring: rgba(56, 189, 248, 0.3);
    --sinergia-bg-page: #0f172a;
    --sinergia-bg-surface: #1e293b;
    --sinergia-bg-subtle: #334155;
    --sinergia-border: #475569;
    --sinergia-border-subtle: #334155;
    --sinergia-text-main: #f8fafc;
    --sinergia-text-muted: #94a3b8;
    --sinergia-success: #4ade80;
    --sinergia-success-bg: #052e16;
    --sinergia-success-border: #166534;
}

.gradio-container {
    font-family: var(--sinergia-font) !important;
    max-width: 1380px !important;
    margin: 0 auto !important;
    padding: 24px 20px !important;
}

/* Header */
#header-container {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 16px 20px;
    background: var(--sinergia-bg-surface);
    border: 1px solid var(--sinergia-border-subtle);
    border-radius: var(--sinergia-radius-lg);
    box-shadow: var(--sinergia-shadow-sm);
    margin-bottom: 16px;
}

#header-logo {
    display: flex;
    align-items: center;
    justify-content: center;
}

#header-text h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: var(--sinergia-primary) !important;
    margin: 0 0 4px 0 !important;
    line-height: 1.2 !important;
}

#header-text p {
    font-size: 0.95rem !important;
    color: var(--sinergia-text-muted) !important;
    margin: 0 !important;
}

.badge-tag {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    background: var(--sinergia-primary-light);
    color: var(--sinergia-primary);
    border-radius: 9999px;
    margin-left: 8px;
    vertical-align: middle;
}

/* Callout de Privacidade */
.privacy-accordion {
    border: 1px solid var(--sinergia-border-subtle) !important;
    border-radius: var(--sinergia-radius-md) !important;
    background: var(--sinergia-bg-surface) !important;
    margin-bottom: 20px !important;
    overflow: hidden;
}

.privacy-content {
    font-size: 0.88rem;
    color: var(--sinergia-text-muted);
    line-height: 1.6;
    padding: 6px 4px;
}

.privacy-content ul {
    margin: 4px 0;
    padding-left: 20px;
}

/* Tabs */
.gradio-container .tabs {
    border: none !important;
    margin-top: 8px;
}

.gradio-container .tab-nav {
    border-bottom: 2px solid var(--sinergia-border-subtle) !important;
    gap: 8px;
}

.gradio-container .tab-nav button {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border-radius: var(--sinergia-radius-md) var(--sinergia-radius-md) 0 0 !important;
    padding: 10px 18px !important;
    transition: all 0.2s ease !important;
}

.gradio-container .tabitem {
    padding-top: 18px !important;
    border: none !important;
}

/* Inputs & Textareas */
.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container .gr-box {
    border-radius: var(--sinergia-radius-md) !important;
    border: 1px solid var(--sinergia-border) !important;
    font-family: var(--sinergia-font) !important;
    font-size: 0.92rem !important;
    line-height: 1.5 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.gradio-container textarea:focus,
.gradio-container input[type="text"]:focus {
    border-color: var(--sinergia-primary) !important;
    box-shadow: 0 0 0 3px var(--sinergia-primary-ring) !important;
    outline: none !important;
}

/* Botões */
.gradio-container .gr-button {
    font-weight: 600 !important;
    border-radius: var(--sinergia-radius-md) !important;
    padding: 10px 20px !important;
    font-size: 0.93rem !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.gradio-container .gr-button.primary {
    background: var(--sinergia-primary) !important;
    color: #ffffff !important;
    border: 1px solid var(--sinergia-primary) !important;
    box-shadow: var(--sinergia-shadow-sm) !important;
}

.gradio-container .gr-button.primary:hover:not(:disabled) {
    background: var(--sinergia-primary-hover) !important;
    border-color: var(--sinergia-primary-hover) !important;
    transform: translateY(-1px);
    box-shadow: var(--sinergia-shadow-md) !important;
}

.gradio-container .gr-button.primary:active:not(:disabled) {
    background: var(--sinergia-primary-active) !important;
    transform: translateY(0);
}

.gradio-container .gr-button:not(.primary) {
    background: var(--sinergia-bg-surface) !important;
    color: var(--sinergia-text-main) !important;
    border: 1px solid var(--sinergia-border) !important;
}

.gradio-container .gr-button:not(.primary):hover:not(:disabled) {
    background: var(--sinergia-bg-subtle) !important;
    border-color: var(--sinergia-border) !important;
}

/* Botão de Copiar */
.btn-copiar {
    width: 100% !important;
    margin-top: 6px !important;
    font-size: 0.88rem !important;
    padding: 8px 14px !important;
    border-style: dashed !important;
}

.btn-copiar.copied-success {
    background: var(--sinergia-success-bg) !important;
    color: var(--sinergia-success) !important;
    border: 1px solid var(--sinergia-success-border) !important;
    border-style: solid !important;
}

/* Linha de Ações */
.cta-row {
    gap: 12px !important;
    margin-top: 14px !important;
    margin-bottom: 12px !important;
}

/* Card de Resumo */
.resumo-card {
    background: var(--sinergia-bg-subtle) !important;
    border: 1px solid var(--sinergia-border-subtle) !important;
    border-left: 4px solid var(--sinergia-primary) !important;
    border-radius: var(--sinergia-radius-md) !important;
    padding: 12px 16px !important;
    font-size: 0.90rem !important;
    margin-top: 8px !important;
    margin-bottom: 14px !important;
    color: var(--sinergia-text-main) !important;
}

/* Acordeões e Tabelas */
.gradio-container .gr-accordion {
    border: 1px solid var(--sinergia-border-subtle) !important;
    border-radius: var(--sinergia-radius-md) !important;
    margin-top: 12px !important;
    background: var(--sinergia-bg-surface) !important;
}

.gradio-container table {
    font-size: 0.88rem !important;
    border-radius: var(--sinergia-radius-md) !important;
}

.step-instruction {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--sinergia-text-muted);
    margin-bottom: 10px;
}
"""

COPY_TEXT_JS = """
(texto, evt) => {
    const valor = typeof texto === "string" ? texto : "";
    if (!valor.trim()) {
        return [];
    }

    const copiarComFallback = () => {
        const areaTemporaria = document.createElement("textarea");
        areaTemporaria.value = valor;
        areaTemporaria.setAttribute("readonly", "");
        areaTemporaria.style.position = "fixed";
        areaTemporaria.style.opacity = "0";
        areaTemporaria.style.pointerEvents = "none";
        document.body.appendChild(areaTemporaria);
        areaTemporaria.focus();
        areaTemporaria.select();
        document.execCommand("copy");
        document.body.removeChild(areaTemporaria);
    };

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(valor).catch(() => copiarComFallback());
    } else {
        copiarComFallback();
    }

    // Feedback visual interativo no botão acionado
    try {
        const btn = event ? (event.target.closest('button') || event.target) : null;
        if (btn) {
            const textoOriginal = btn.innerText;
            btn.innerText = "✓ Copiado com sucesso!";
            btn.classList.add("copied-success");
            setTimeout(() => {
                btn.innerText = textoOriginal;
                btn.classList.remove("copied-success");
            }, 2000);
        }
    } catch (e) {
        // Fallback silencioso caso 'event' não esteja acessível
    }

    return [];
}
"""

INIT_LIGHT_THEME_JS = """
() => {
    document.documentElement.classList.remove('dark');
    document.body.classList.remove('dark');
    if (!localStorage.getItem('gradio-theme')) {
        localStorage.setItem('gradio-theme', 'light');
    }
}
"""


def criar_interface_gradio(
    logo_file_path,
    estado_vazio_texto_anonimizado,
    estado_vazio_pdf_original,
    estado_vazio_pdf_anonimizado,
    resumo_vazio_texto,
    resumo_vazio_pdf,
    dataframe_entidades_vazio_fn,
    atualizar_estado_botao_texto_fn,
    atualizar_estado_botao_pdf_fn,
    desativar_botao_fn,
    processar_texto_area_fn,
    limpar_texto_area_fn,
    processar_arquivo_pdf_fn,
):
    with gr.Blocks(title="Anonimizador SINERGIA - TRF1") as demo:
        # Header Institucional
        with gr.Row(elem_id="header-container"):
            with gr.Column(scale=0, min_width=90, elem_id="header-logo"):
                gr.Image(
                    value=logo_file_path,
                    interactive=False,
                    show_label=False,
                    show_download_button=False,
                    show_fullscreen_button=False,
                    width=85,
                )
            with gr.Column(scale=4, elem_id="header-text"):
                gr.Markdown(
                    """
                    # Anonimizador SINERGIA <span class="badge-tag">v0.97 Beta</span>
                    Anonimização inteligente de documentos jurídicos com apoio de NLP e preservação de contexto processual.
                    """
                )

        # Banner de Privacidade Colapsável
        with gr.Accordion("ℹ️ Orientações de Privacidade, Limites e LGPD", open=False, elem_classes=["privacy-accordion"]):
            gr.Markdown(
                """
                <div class="privacy-content">
                    <ul>
                        <li><strong>Processamento Local:</strong> O conteúdo enviado é processado para identificação de PIIs sensíveis (nomes de partes, CPFs, RGs, endereços, etc.).</li>
                        <li><strong>PDFs Digitalizados:</strong> Documentos digitalizados exclusivamente como imagem requerem texto pesquisável (OCR prévio).</li>
                        <li><strong>Revisão Humana:</strong> Recomenda-se a conferência prévia do texto antes da expedição formal da peça.</li>
                        <li><strong>Conformidade:</strong> Em conformidade com a LGPD e resoluções do CNJ para proteção de dados no Poder Judiciário.</li>
                    </ul>
                </div>
                """
            )

        with gr.Tabs():
            # ── ABA 1: Anonimizar Texto ──────────────────────────────────────────
            with gr.TabItem("📝 Anonimizar texto"):
                gr.Markdown("Cole o texto da peça jurídica abaixo e clique em **Anonimizar texto**.", elem_classes=["step-instruction"])
                with gr.Row():
                    with gr.Column(scale=1):
                        texto_original_area = gr.Textbox(
                            lines=16,
                            label="Texto original",
                            placeholder="Cole ou digite aqui o despacho, sentença, petição ou acórdão a ser anonimizado...",
                        )

                    with gr.Column(scale=1):
                        texto_anonimizado_area = gr.Textbox(
                            lines=16,
                            value=estado_vazio_texto_anonimizado,
                            label="Texto anonimizado",
                            interactive=False,
                        )
                        btn_copiar_texto_area = gr.Button(
                            "📋 Copiar texto anonimizado",
                            variant="secondary",
                            elem_classes=["btn-copiar"],
                        )

                with gr.Row(elem_classes=["cta-row"]):
                    btn_anonimizar_area = gr.Button("🔒 Anonimizar texto", variant="primary", size="lg", interactive=False)
                    btn_limpar_area = gr.Button("🗑️ Limpar campos", variant="secondary")

                resumo_texto_area = gr.Markdown(value=resumo_vazio_texto, elem_classes=["resumo-card"])

                with gr.Accordion("🔍 Ver entidades detectadas e auditoria", open=False):
                    resultados_df_area = gr.DataFrame(
                        label="Entidades identificadas no texto",
                        value=dataframe_entidades_vazio_fn(),
                        interactive=False,
                    )

            # ── ABA 2: Anonimizar PDF ────────────────────────────────────────────
            with gr.TabItem("📄 Anonimizar arquivo PDF"):
                gr.Markdown("Selecione um arquivo PDF com texto pesquisável (até 40MB e 500 páginas).", elem_classes=["step-instruction"])
                upload_pdf = gr.File(
                    label="Upload do arquivo PDF",
                    file_types=[".pdf"],
                    height=130,
                )
                with gr.Row(elem_classes=["cta-row"]):
                    btn_anonimizar_pdf = gr.Button(
                        "🔄 Reprocessar PDF",
                        variant="primary",
                        size="lg",
                        interactive=False,
                        visible=False,
                    )

                resumo_pdf = gr.Markdown(value=resumo_vazio_pdf, elem_classes=["resumo-card"], min_height=56)

                gr.Markdown("Comparação entre o texto extraído e a versão anonimizada:", elem_classes=["step-instruction"])
                with gr.Row():
                    with gr.Column(scale=1):
                        texto_original_pdf = gr.Textbox(
                            lines=16,
                            value=estado_vazio_pdf_original,
                            label="Texto original extraído do PDF",
                            interactive=False,
                        )
                    with gr.Column(scale=1):
                        texto_anonimizado_pdf = gr.Textbox(
                            lines=16,
                            value=estado_vazio_pdf_anonimizado,
                            label="Texto anonimizado",
                            interactive=False,
                        )
                        btn_copiar_texto_pdf = gr.Button(
                            "📋 Copiar texto anonimizado",
                            variant="secondary",
                            elem_classes=["btn-copiar"],
                        )

                with gr.Accordion("🔍 Ver entidades detectadas no PDF", open=False):
                    resultados_df_pdf = gr.DataFrame(
                        label="Entidades identificadas no PDF",
                        value=dataframe_entidades_vazio_fn(),
                        interactive=False,
                    )

        # ── Event Handlers: Aba Texto ──────────────────────────────────────────
        texto_original_area.change(
            fn=atualizar_estado_botao_texto_fn,
            inputs=[texto_original_area],
            outputs=[btn_anonimizar_area],
        )

        evento_anonimizar_texto = btn_anonimizar_area.click(
            fn=desativar_botao_fn,
            outputs=[btn_anonimizar_area],
            queue=False,
        ).then(
            fn=processar_texto_area_fn,
            inputs=[texto_original_area],
            outputs=[texto_anonimizado_area, resultados_df_area, resumo_texto_area],
        )
        evento_anonimizar_texto.then(
            fn=atualizar_estado_botao_texto_fn,
            inputs=[texto_original_area],
            outputs=[btn_anonimizar_area],
            queue=False,
        )

        btn_copiar_texto_area.click(
            fn=None,
            inputs=[texto_anonimizado_area],
            outputs=[],
            js=COPY_TEXT_JS,
            queue=False,
        )

        btn_limpar_area.click(
            fn=limpar_texto_area_fn,
            outputs=[texto_original_area, texto_anonimizado_area, resultados_df_area, resumo_texto_area, btn_anonimizar_area],
        )

        # ── Event Handlers: Aba PDF ────────────────────────────────────────────
        upload_pdf.upload(
            fn=lambda: gr.update(visible=False, interactive=False),
            outputs=[btn_anonimizar_pdf],
            queue=False,
        ).then(
            fn=processar_arquivo_pdf_fn,
            inputs=[upload_pdf],
            outputs=[texto_original_pdf, texto_anonimizado_pdf, resultados_df_pdf, resumo_pdf, btn_anonimizar_pdf],
        )

        def limpar_pdf_ao_remover():
            return (
                estado_vazio_pdf_original,
                estado_vazio_pdf_anonimizado,
                dataframe_entidades_vazio_fn(),
                resumo_vazio_pdf,
                gr.update(visible=False, interactive=False),
            )

        upload_pdf.clear(
            fn=limpar_pdf_ao_remover,
            outputs=[texto_original_pdf, texto_anonimizado_pdf, resultados_df_pdf, resumo_pdf, btn_anonimizar_pdf],
            queue=False,
        )

        btn_anonimizar_pdf.click(
            fn=desativar_botao_fn,
            outputs=[btn_anonimizar_pdf],
            queue=False,
        ).then(
            fn=processar_arquivo_pdf_fn,
            inputs=[upload_pdf],
            outputs=[texto_original_pdf, texto_anonimizado_pdf, resultados_df_pdf, resumo_pdf, btn_anonimizar_pdf],
        )

        btn_copiar_texto_pdf.click(
            fn=None,
            inputs=[texto_anonimizado_pdf],
            outputs=[],
            js=COPY_TEXT_JS,
            queue=False,
        )

        demo.load(
            fn=None,
            inputs=None,
            outputs=None,
            js=INIT_LIGHT_THEME_JS,
            queue=False,
        )

    demo.theme = gr.themes.Soft()
    demo.css = CUSTOM_CSS
    return demo
