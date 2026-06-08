import os
import sys
import threading
import glob
import logging
from datetime import datetime

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError as e:
    print(f"Erro: Biblioteca customtkinter ausente. Execute: pip install customtkinter")
    print(f"Detalhes: {e}")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as pdf_processor

BG_WINDOW = "#F0F0F0"
BG_SURFACE = "#FFFFFF"
BG_FIELD = "#E8E8E8"
BORDER_LIGHT = "#CCCCCC"
TEXT_PRIMARY = "#333333"
TEXT_SECONDARY = "#555555"
TEXT_MUTED = "#888888"
TEXT_STATUS = "#666666"
BTN_PRIMARY_BG = "#4A4A4A"
BTN_PRIMARY_TEXT = "#FFFFFF"
BTN_SECONDARY_BG = "#D0D0D0"
BTN_SECONDARY_TEXT = "#333333"


class PDFSplitterApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Separador de PDF")
        self.app.geometry("580x480")
        self.app.resizable(False, False)
        self.app.configure(fg_color=BG_WINDOW)

        self.input_dir = ""
        self.output_dir = ""
        self.processando = False

        ctk.set_appearance_mode("light")
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self.app, fg_color=BG_WINDOW, corner_radius=0)
        container.pack(fill="both", expand=True, padx=36, pady=32)

        title_frame = ctk.CTkFrame(container, fg_color="transparent")
        title_frame.pack(fill="x")

        ctk.CTkLabel(
            title_frame, text="Separador de PDF",
            font=("Inter", 20, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkFrame(container, fg_color=BORDER_LIGHT, height=1, corner_radius=0).pack(fill="x", pady=(16, 0))

        io_card = ctk.CTkFrame(container, fg_color=BG_SURFACE, corner_radius=8)
        io_card.pack(fill="x", pady=(16, 0))

        ctk.CTkLabel(
            io_card, text="Pasta de Entrada",
            font=("Inter", 13, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(20, 0))

        input_row = ctk.CTkFrame(io_card, fg_color="transparent")
        input_row.pack(fill="x", padx=20, pady=(8, 0))

        self.input_entry = ctk.CTkEntry(
            input_row, placeholder_text="C:\\...\\input",
            fg_color=BG_FIELD, text_color=TEXT_MUTED,
            border_color=BORDER_LIGHT, border_width=1,
            corner_radius=4, height=36,
            font=("Inter", 13)
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.configure(state="normal")

        ctk.CTkButton(
            input_row, text="Selecionar",
            fg_color=BTN_SECONDARY_BG, text_color=BTN_SECONDARY_TEXT,
            hover_color="#C0C0C0", corner_radius=4,
            width=100, height=36, font=("Inter", 13, "bold"),
            command=self._selecionar_input
        ).pack(side="right")

        ctk.CTkLabel(
            io_card, text="Pasta de Sa\u00edda",
            font=("Inter", 13, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", padx=20, pady=(16, 0))

        output_row = ctk.CTkFrame(io_card, fg_color="transparent")
        output_row.pack(fill="x", padx=20, pady=(8, 20))

        self.output_entry = ctk.CTkEntry(
            output_row, placeholder_text="C:\\...\\output",
            fg_color=BG_FIELD, text_color=TEXT_MUTED,
            border_color=BORDER_LIGHT, border_width=1,
            corner_radius=4, height=36,
            font=("Inter", 13)
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            output_row, text="Selecionar",
            fg_color=BTN_SECONDARY_BG, text_color=BTN_SECONDARY_TEXT,
            hover_color="#C0C0C0", corner_radius=4,
            width=100, height=36, font=("Inter", 13, "bold"),
            command=self._selecionar_output
        ).pack(side="right")

        exec_row = ctk.CTkFrame(container, fg_color="transparent")
        exec_row.pack(fill="x", pady=(20, 0))

        self.exec_btn = ctk.CTkButton(
            exec_row, text="EXECUTAR SEPARAÇÃO",
            fg_color=BTN_PRIMARY_BG, text_color=BTN_PRIMARY_TEXT,
            hover_color="#333333", corner_radius=8,
            height=48, font=("Inter", 16, "bold"),
            command=self._executar
        )
        self.exec_btn.pack(padx=40)

        self.progress_bar = ctk.CTkProgressBar(
            container,
            fg_color=BG_FIELD,
            progress_color=BTN_PRIMARY_BG,
            corner_radius=4,
            height=8
        )
        self.progress_bar.pack(fill="x", pady=(20, 0))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            container, text="Status: Aguardando...",
            font=("Inter", 12),
            text_color=TEXT_STATUS,
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(12, 0))

        self.log_text = ctk.CTkTextbox(
            container,
            fg_color=BG_SURFACE,
            text_color=TEXT_SECONDARY,
            font=("Consolas", 11),
            corner_radius=6,
            height=100,
            border_width=1,
            border_color=BORDER_LIGHT
        )
        self.log_text.pack(fill="x", pady=(8, 0))

    def _log(self, msg):
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.app.update_idletasks()

    def _selecionar_input(self):
        pasta = filedialog.askdirectory(title="Selecionar pasta de entrada")
        if pasta:
            self.input_dir = pasta
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, pasta)
            self.input_entry.configure(text_color=TEXT_PRIMARY)

    def _selecionar_output(self):
        pasta = filedialog.askdirectory(title="Selecionar pasta de sa\u00edda")
        if pasta:
            self.output_dir = pasta
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, pasta)
            self.output_entry.configure(text_color=TEXT_PRIMARY)

    def _progress_callback(self, tipo, *args):
        if tipo == "status":
            self.app.after(0, lambda: self.status_label.configure(text=f"Status: {args[0]}"))
            self.app.after(0, lambda: self._log(args[0]))
        elif tipo == "progress":
            pagina, total = args
            valor = pagina / total
            self.app.after(0, lambda: self.progress_bar.configure(fg_color=BG_FIELD))
            self.app.after(0, lambda: self.progress_bar.set(valor))
        elif tipo == "complete":
            resultado = args[0]
            msg = (
                f"Concluído: {resultado['arquivo']} | "
                f"{resultado['total_paginas']} páginas | "
                f"{resultado['placas_encontradas']} placas | "
                f"{resultado['paginas_sem_placa']} sem placa"
            )
            self.app.after(0, lambda: self._log(f"✅ {msg}"))
            self.app.after(0, lambda: self.status_label.configure(
                text=f"Status: Concluído - {resultado['placas_encontradas']} placas encontradas"
            ))
            self.app.after(0, self._finalizar_processamento)
        elif tipo == "error":
            self.app.after(0, lambda: self._log(f"❌ {args[0]}"))
            self.app.after(0, lambda: self.status_label.configure(text=f"Status: Erro"))
        elif tipo == "warning":
            self.app.after(0, lambda: self._log(f"⚠️ {args[0]}"))

    def _finalizar_processamento(self):
        self.processando = False
        self.exec_btn.configure(state="normal", text="EXECUTAR SEPARAÇÃO")
        self.progress_bar.set(1)
        self.app.after(1500, lambda: self.progress_bar.set(0))

    def _executar(self):
        if self.processando:
            return

        input_dir = self.input_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        if not input_dir:
            messagebox.showwarning("Aviso", "Selecione a pasta de entrada.")
            return
        if not output_dir:
            messagebox.showwarning("Aviso", "Selecione a pasta de sa\u00edda.")
            return
        if not os.path.isdir(input_dir):
            messagebox.showerror("Erro", "Pasta de entrada inv\u00e1lida.")
            return

        os.makedirs(output_dir, exist_ok=True)

        self.processando = True
        self.exec_btn.configure(state="disabled", text="PROCESSANDO...")
        self.progress_bar.set(0)
        self.log_text.delete("1.0", "end")
        self.status_label.configure(text="Status: Iniciando...")

        threading.Thread(target=self._processar_em_thread, args=(input_dir, output_dir), daemon=True).start()

    def _processar_em_thread(self, input_dir, output_dir):
        arquivos_pdf = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))

        if not arquivos_pdf:
            self.app.after(0, lambda: messagebox.showwarning(
                "Aviso", "Nenhum arquivo PDF encontrado na pasta de entrada."
            ))
            self.app.after(0, lambda: self.status_label.configure(text="Status: Nenhum PDF encontrado"))
            self.app.after(0, self._finalizar_processamento)
            return

        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"app_{timestamp}.log")

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        logger = logging.getLogger("pdf_splitter_gui")
        logger.info("=== Iniciando PDF Splitter GUI ===")

        self.app.after(0, lambda: self._log(f"Processando {len(arquivos_pdf)} arquivos..."))

        for idx, pdf_path in enumerate(arquivos_pdf):
            self.app.after(0, lambda p=pdf_path, i=idx, t=len(arquivos_pdf): self._log(
                f"\n--- Arquivo {i+1}/{t}: {os.path.basename(p)} ---"
            ))

            pdf_processor.processar_pdf(
                pdf_path, logger,
                output_dir=output_dir,
                progress_callback=self._progress_callback
            )

        self.app.after(0, lambda: self._log(f"\nProcessamento de {len(arquivos_pdf)} arquivo(s) concluído!"))
        self.app.after(0, self._finalizar_processamento)

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    app = PDFSplitterApp()
    app.run()
