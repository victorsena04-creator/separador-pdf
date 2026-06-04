# Descobertas e Restrições

- **Objetivo Inicial**: Criar uma aplicação Python `pdf_splitter` que divide um PDF em várias páginas, renomeando cada arquivo com base na "placa" extraída.
- **Ferramentas sugeridas**: pypdf, pdfplumber, pdf2image, pytesseract.
- **Estratégia de Extração**: Cascata. Tentar extração direta e, se falhar, usar OCR como fallback.
- **Estrutura Tabular do PDF**: Identificamos que o PDF de exemplo traz o rótulo "Placa:" e o valor em linhas diferentes por conta de uma estrutura de tabela que mistura dados horizontalmente. A distância varia de 54 a 56 caracteres entre o rótulo e a placa real, exigindo uma regex tolerante a distâncias de até 150 caracteres.
- **Páginas Órfãs (Sem Rótulo)**: Algumas páginas de continuação no PDF contêm apenas o código da placa de veículo e nenhuma palavra "Placa:". Solucionamos usando uma busca de emergência geral no texto baseado no padrão exato da placa.
- **Problema de PATH no Windows**: A instalação do Poppler nas variáveis de ambiente do Windows não é refletida em terminais que já estejam abertos. Contudo, a melhoria na regex eliminou a necessidade de conversão de imagem (OCR), evitando o acionamento do Poppler.
