# Constituição do Projeto (gemini.md)

## Esquemas de Dados
**Entrada (Input):**
- Arquivo `.pdf` com múltiplas páginas contendo texto no padrão `placa: VALOR`.

**Saída (Payload):**
- Arquivos `.pdf` de 1 página cada, salvos na pasta `output/` com o nome formatado no padrão `PLACA-TIPO_DATA.pdf`.
- Arquivo de log com o resultado do processamento, salvo na pasta `logs/`.

## Regras Comportamentais
- **Eficiência Primeiro:** O sistema deve priorizar a extração direta de texto (via pdfplumber).
- **Resiliência (Fallback):** O OCR (via pytesseract) atua **apenas** quando a extração direta falha.
- **Tolerância a falhas:** O script não deve parar caso uma página falhe; ele deve documentar o erro e prosseguir.
- **Nomenclatura Segura:** Limpar caracteres inválidos do nome extraído da placa. O nome do arquivo salvo deve ter o padrão `PLACA-TIPO_DATA`, onde o `TIPO` é definido com base no campo `Cód. Serviço DETRAN:` (sendo `TRANSF` para códigos `001`, `003` ou `006`, `TX REM` para código `089` ou `89`, e `DÉBITOS` para outros). Se não achar placa, usar `PAGINA_{numero}_SEM_PLACA-{TIPO}_SEM_DATA.pdf`.
- **Auto-Atualização:** O aplicativo integrado com a interface de usuário CustomTkinter deve buscar por novas versões no GitHub Releases e possibilitar a atualização de forma automatizada ao usuário.

## Invariantes Arquiteturais
- Linguagem: Python 3.
- Bibliotecas principais: `pypdf`, `pdfplumber`, `pdf2image`, `pytesseract`.
- Ambiente agnóstico (funciona em Windows, macOS e Linux).
