# Constituição do Projeto (gemini.md)

## Esquemas de Dados
**Entrada (Input):**
- Arquivo `.pdf` com múltiplas páginas contendo texto no padrão `placa: VALOR`.

**Saída (Payload):**
- Arquivos `.pdf` de 1 página cada, salvos na pasta `output/` com o nome da placa (`VALOR.pdf`).
- Arquivo de log com o resultado do processamento, salvo na pasta `logs/`.

## Regras Comportamentais
- **Eficiência Primeiro:** O sistema deve priorizar a extração direta de texto (via pdfplumber).
- **Resiliência (Fallback):** O OCR (via pytesseract) atua **apenas** quando a extração direta falha.
- **Tolerância a falhas:** O script não deve parar caso uma página falhe; ele deve documentar o erro e prosseguir.
- **Nomenclatura Segura:** Limpar caracteres inválidos do nome extraído da placa. Se não achar placa, usar `PAGINA_{numero}_SEM_PLACA.pdf`.

## Invariantes Arquiteturais
- Linguagem: Python 3.
- Bibliotecas principais: `pypdf`, `pdfplumber`, `pdf2image`, `pytesseract`.
- Ambiente agnóstico (funciona em Windows, macOS e Linux).
