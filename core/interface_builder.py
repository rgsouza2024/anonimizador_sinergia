"""Gradio interface construction for the anonymizer app."""

import gradio as gr


CUSTOM_CSS = """
:root {
    --font-base: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    --color-primary: #0b5cab;
    --color-primary-hover: #084987;
    --color-bg-subtle: #f5f8fc;
    --color-border: #d8e0eb;
    --space-1: 8px;
    --space-2: 16px;
    --space-3: 24px;
    --radius-1: 10px;
}

.gradio-container {
    font-family: var(--font-base);
    padding: var(--space-3) !important;
}

#header {
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-2);
}

#header h1 {
    margin-bottom: var(--space-1) !important;
}

.gradio-container .tabs {
    margin-top: var(--space-2);
}

.gradio-container .tabitem {
    padding-top: var(--space-2);
}

.gradio-container .gr-accordion {
    margin-top: var(--space-2);
}

.gradio-container textarea,
.gradio-container input[type="text"],
.gradio-container input[type="file"],
.gradio-container table {
    border-radius: var(--radius-1) !important;
    border-color: var(--color-border) !important;
}

.gradio-container .gr-button {
    border-radius: var(--radius-1) !important;
    padding: var(--space-1) var(--space-2) !important;
}

.gradio-container .gr-button.primary {
    background: var(--color-primary) !important;
    border-color: var(--color-primary) !important;
}

.gradio-container .gr-button.primary:hover {
    background: var(--color-primary-hover) !important;
    border-color: var(--color-primary-hover) !important;
}

.gradio-container .gr-button:not(.primary) {
    background: #f2f4f7 !important;
    color: #1f2937 !important;
    border-color: #cfd8e3 !important;
}

.gradio-container .gr-button:not(.primary):hover {
    background: #e7edf4 !important;
    border-color: #b8c4d1 !important;
}

.gradio-container .cta-row {
    gap: var(--space-1);
    margin-bottom: var(--space-1);
}

.gradio-container .gr-markdown {
    margin-bottom: var(--space-2);
}

.gradio-container > .gr-markdown:nth-of-type(2) {
    background: var(--color-bg-subtle);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-1);
    padding: var(--space-2);
}

button.copy-button {
    padding: 6px !important;
    min-width: 36px !important;
    min-height: 36px !important;
}

button.copy-button > svg {
    transform: scale(1.1);
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
    with gr.Blocks(theme=gr.themes.Soft(), title="Anonimizador TRF1", css=CUSTOM_CSS) as demo:
        with gr.Row(elem_id="header"):
            with gr.Column(scale=0, min_width=120):
                gr.Image(value=logo_file_path, interactive=False, show_download_button=False, show_label=False, width=100)
            with gr.Column(scale=4):
                gr.Markdown(
                    """
                    # Anonimizador SINERGIA
                    **Anonimize textos jurídicos com apoio de NLP e regras customizadas.**
                    Desenvolvido pelo Projeto Sinergia - TRF1.
                    """
                )

        gr.Markdown(
            """
            ### Limites e privacidade
            - Esta ferramenta processa o texto enviado para detectar e anonimizar entidades.
            - PDFs digitalizados como imagem podem não conter texto extraível (OCR não incluso nesta versão).
            - Revise o resultado antes de compartilhar o documento, pois nenhum modelo acerta 100% dos casos.
            - Siga as políticas internas de privacidade e LGPD ao usar dados pessoais.
            """
        )

        with gr.Tabs():
            with gr.TabItem("Anonimizar texto"):
                gr.Markdown("### Passo 1: cole o texto original e clique em **Anonimizar texto**.")
                with gr.Row():
                    with gr.Column(scale=1):
                        texto_original_area = gr.Textbox(
                            lines=15,
                            label="Texto original",
                            placeholder="Cole ou digite o conteúdo que deseja anonimizar.",
                        )

                    with gr.Column(scale=1):
                        texto_anonimizado_area = gr.Textbox(
                            lines=15,
                            value=estado_vazio_texto_anonimizado,
                            label="Texto anonimizado",
                            interactive=False,
                            show_copy_button=True,
                        )

                with gr.Row(elem_classes=["cta-row"]):
                    btn_anonimizar_area = gr.Button("Anonimizar texto", variant="primary", size="lg", interactive=False)
                    btn_limpar_area = gr.Button("Limpar campos", variant="secondary")
                resumo_texto_area = gr.Markdown(value=resumo_vazio_texto)

                with gr.Accordion("Ver entidades detectadas", open=False):
                    resultados_df_area = gr.DataFrame(
                        label="Entidades encontradas",
                        value=dataframe_entidades_vazio_fn(),
                        interactive=False,
                    )

            with gr.TabItem("Anonimizar arquivo PDF"):
                gr.Markdown("### Passo 1: envie um PDF com texto pesquisável e clique em **Anonimizar PDF**.")
                upload_pdf = gr.File(label="Selecione o arquivo PDF", file_types=[".pdf"])
                with gr.Row(elem_classes=["cta-row"]):
                    btn_anonimizar_pdf = gr.Button("Anonimizar PDF", variant="primary", size="lg", interactive=False)
                resumo_pdf = gr.Markdown(value=resumo_vazio_pdf)
                gr.Markdown("### Passo 2: revise o texto original extraído e a versão anonimizada.")
                with gr.Row():
                    with gr.Accordion("Ver texto original extraído do PDF", open=False):
                        texto_original_pdf = gr.Textbox(
                            lines=15,
                            value=estado_vazio_pdf_original,
                            label="Texto original extraído",
                            interactive=False,
                        )
                    with gr.Column():
                        texto_anonimizado_pdf = gr.Textbox(
                            lines=14,
                            value=estado_vazio_pdf_anonimizado,
                            label="Texto anonimizado",
                            interactive=False,
                            show_copy_button=True,
                        )

        texto_original_area.change(fn=atualizar_estado_botao_texto_fn, inputs=[texto_original_area], outputs=[btn_anonimizar_area])
        upload_pdf.change(fn=atualizar_estado_botao_pdf_fn, inputs=[upload_pdf], outputs=[btn_anonimizar_pdf])
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
        btn_limpar_area.click(
            fn=limpar_texto_area_fn,
            outputs=[texto_original_area, texto_anonimizado_area, resultados_df_area, resumo_texto_area, btn_anonimizar_area],
        )
        evento_anonimizar_pdf = btn_anonimizar_pdf.click(
            fn=desativar_botao_fn,
            outputs=[btn_anonimizar_pdf],
            queue=False,
        ).then(
            fn=processar_arquivo_pdf_fn,
            inputs=[upload_pdf],
            outputs=[texto_original_pdf, texto_anonimizado_pdf, resumo_pdf],
        )
        evento_anonimizar_pdf.then(
            fn=atualizar_estado_botao_pdf_fn,
            inputs=[upload_pdf],
            outputs=[btn_anonimizar_pdf],
            queue=False,
        )

    return demo

