# Descobertas e Restrições

- **Objetivo Inicial**: Criar uma aplicação Python `pdf_splitter` que divide um PDF em várias páginas, renomeando cada arquivo com base na "placa" extraída.
- **Ferramentas sugeridas**: pypdf, pdfplumber, pdf2image, pytesseract.
- **Estratégia de Extração**: Cascata. Tentar extração direta e, se falhar, usar OCR como fallback.
- **Estrutura Tabular do PDF**: Identificamos que o PDF de exemplo traz o rótulo "Placa:" e o valor em linhas diferentes por conta de uma estrutura de tabela que mistura dados horizontalmente. A distância varia de 54 a 56 caracteres entre o rótulo e a placa real, exigindo uma regex tolerante a distâncias de até 150 caracteres.
- **Páginas Órfãs (Sem Rótulo)**: Algumas páginas de continuação no PDF contêm apenas o código da placa de veículo e nenhuma palavra "Placa:". Solucionamos usando uma busca de emergência geral no texto baseado no padrão exato da placa.
- **Problema de PATH no Windows**: A instalação do Poppler nas variáveis de ambiente do Windows não é refletida em terminais que já estejam abertos. Contudo, a melhoria na regex eliminou a necessidade de conversão de imagem (OCR), evitando o acionamento do Poppler.
- **Detecção do Tipo de Pagamento**: Identificamos que o padrão do DETRAN exibe "Cód. Serviço DETRAN: [código]" nos comprovantes. Uma Regex flexível `c[oó]d\.?\s*servi[çc]o\s*detran\s*:\s*(\d+)` foi implementada para aceitar variações ortográficas e de acentuação, com conversão para inteiro para classificar com segurança `001`, `003` e `006` como `TRANSF` e outros códigos como `DÉBITOS`.
- **Auto-Atualização via Executável**: Para que um executável Windows atualize a si mesmo, o fluxo ideal é baixar o novo instalador (`SeparadorPDF_Instalador.exe`) para a pasta temporária do sistema, executá-lo em uma nova thread/processo e imediatamente finalizar o processo em execução para evitar bloqueios de escrita sobre o arquivo executável na pasta de instalação. A API de Releases do GitHub fornece uma forma limpa de expor o metadado (`tag_name`) e o binário (`browser_download_url`).

