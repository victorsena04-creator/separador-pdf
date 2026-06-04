import os
import re
import sys
import glob
import logging
from datetime import datetime

# Garantir que o terminal do Windows não trave ao tentar imprimir emojis (✅, 🚨)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Importações de bibliotecas externas
try:
    import pypdf
    import pdfplumber
    from PIL import Image
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
    import pytesseract
except ImportError as e:
    print(f"🚨 Erro de Importação: Biblioteca não instalada. Instale os requerimentos rodando: pip install -r requirements.txt")
    print(f"Detalhes do erro: {e}")
    sys.exit(1)

# Definição dos caminhos das pastas
INPUT_DIR = "./input"
OUTPUT_DIR = "./output"
LOGS_DIR = "./logs"


def configurar_pastas():
    """Garante que as pastas de entrada, saída e logs existam."""
    for pasta in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
        if not os.path.exists(pasta):
            os.makedirs(pasta)


def sanitizar_nome_arquivo(nome):
    """
    Remove caracteres inválidos para nomes de arquivos no Windows/Linux/macOS,
    substitui espaços por underscores, converte para maiúsculas e limita a 100 caracteres.
    """
    if not nome:
        return ""
    # Remover caracteres inválidos: < > : " / \ | ? *
    nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
    # Substituir múltiplos espaços ou quebras de linha por um único underscore
    nome_limpo = re.sub(r'\s+', '_', nome_limpo)
    # Converter para maiúsculas
    nome_limpo = nome_limpo.upper()
    # Truncar para no máximo 100 caracteres
    return nome_limpo[:100]


def extrair_placa_com_regex(texto):
    """
    Procura por uma placa de veículo no texto.
    1. Primeiro, tenta encontrar o padrão de placa associado ao rótulo 'placa:' (até 150 caracteres de distância).
    2. Se não encontrar, tenta buscar qualquer padrão de placa brasileira solto no texto.
    """
    if not texto:
        return None
        
    # Padrão da placa brasileira (antiga: AAA-1234 / Mercosul: AAA1A23)
    regex_placa = r'([A-Z]{3}-?[0-9][A-Z0-9][0-9]{2})'
    
    # 1. Busca associada ao rótulo 'placa:' (tolerando até 150 caracteres de distância para tabelas)
    padrao_rotulado = re.compile(rf'placa\s*:\s*[\s\S]{{0,150}}?{regex_placa}', re.IGNORECASE)
    busca_rotulado = padrao_rotulado.search(texto)
    if busca_rotulado:
        return busca_rotulado.group(1).upper()
        
    # 2. Busca geral (caso a página não tenha a palavra 'placa:')
    padrao_geral = re.compile(rf'\b{regex_placa}\b', re.IGNORECASE)
    busca_geral = padrao_geral.search(texto)
    if busca_geral:
        return busca_geral.group(1).upper()
        
    return None




def obter_nome_unico_saida(pasta_saida, nome_base, placas_geradas):
    """
    Retorna o caminho de saída com base apenas nas placas já processadas nesta rodada atual.
    Se for a primeira vez que a placa aparece nesta rodada, usa o nome base.
    Caso contrário, adiciona um sufixo numérico (_2, _3, etc).
    """
    if nome_base not in placas_geradas:
        placas_geradas[nome_base] = 1
        return os.path.join(pasta_saida, f"{nome_base}.pdf")
    else:
        placas_geradas[nome_base] += 1
        contador = placas_geradas[nome_base]
        return os.path.join(pasta_saida, f"{nome_base}_{contador}.pdf")


def processar_pdf(caminho_pdf, logger):
    """Processa o PDF dividindo suas páginas e identificando as placas."""
    logger.info(f"Iniciando processamento do PDF: {caminho_pdf}")

    try:
        # Abrir o leitor para verificar integridade e criptografia
        with open(caminho_pdf, 'rb') as f:
            leitor = pypdf.PdfReader(f)
            if leitor.is_encrypted:
                logger.error("O arquivo PDF está protegido por senha. Processamento abortado.")
                print(f"🚨 Erro: O arquivo '{os.path.basename(caminho_pdf)}' está protegido por senha e não pode ser lido.")
                return

            total_paginas = len(leitor.pages)

        logger.info(f"Total de páginas detectadas: {total_paginas}")
    except Exception as e:
        logger.error(f"Erro ao abrir o arquivo PDF: {e}")
        print(f"🚨 Erro ao ler o arquivo PDF: {e}")
        return

    # Estatísticas do processamento
    placas_encontradas = 0
    paginas_sem_placa = 0
    placas_geradas_nesta_rodada = {}

    # Abrir com pdfplumber para extração direta de texto
    try:
        pdf_plumber_doc = pdfplumber.open(caminho_pdf)
    except Exception as e:
        logger.error(f"Erro ao abrir o PDF com pdfplumber: {e}")
        pdf_plumber_doc = None

    for i in range(total_paginas):
        numero_pagina = i + 1
        logger.info(f"--- Processando página {numero_pagina}/{total_paginas} ---")

        placa = None
        estrategia_usada = "Nenhuma"

        # Estratégia 1: Extração Direta (pdfplumber)
        if pdf_plumber_doc:
            try:
                pagina = pdf_plumber_doc.pages[i]
                texto_direto = pagina.extract_text()
                placa = extrair_placa_com_regex(texto_direto)
                if placa:
                    estrategia_usada = "Extração Direta (pdfplumber)"
                    logger.info(f"Página {numero_pagina}: Placa '{placa}' encontrada via Extração Direta.")
            except Exception as e:
                logger.warning(f"Página {numero_pagina}: Falha na extração direta de texto: {e}. Tentando OCR...")

        # Estratégia 2: OCR com Pytesseract (Fallback)
        if not placa:
            logger.info(f"Página {numero_pagina}: Iniciando fallback OCR...")
            try:
                # Converter a página específica para imagem
                imagens = convert_from_path(
                    caminho_pdf,
                    dpi=300,
                    first_page=numero_pagina,
                    last_page=numero_pagina
                )
                if imagens:
                    imagem_pagina = imagens[0]
                    # Executar OCR
                    texto_ocr = pytesseract.image_to_string(imagem_pagina, lang='por')
                    placa = extrair_placa_com_regex(texto_ocr)

                    # Se falhar em português, tenta em inglês
                    if not placa:
                        logger.info(f"Página {numero_pagina}: Não encontrada placa com lang='por'. Tentando lang='eng'...")
                        texto_ocr_eng = pytesseract.image_to_string(imagem_pagina, lang='eng')
                        placa = extrair_placa_com_regex(texto_ocr_eng)

                    if placa:
                        estrategia_usada = "OCR (pytesseract)"
                        logger.info(f"Página {numero_pagina}: Placa '{placa}' encontrada via OCR.")
            except pytesseract.TesseractNotFoundError:
                msg_erro = (
                    "O executável do Tesseract OCR não foi encontrado no sistema.\n"
                    "Por favor, certifique-se de que o Tesseract está instalado e configurado no PATH.\n"
                    "No Windows: Baixe o instalador e adicione a pasta de instalação nas Variáveis de Ambiente.\n"
                    "No Linux: execute 'sudo apt install tesseract-ocr tesseract-ocr-por'\n"
                    "No macOS: execute 'brew install tesseract'"
                )
                logger.error(f"Página {numero_pagina}: {msg_erro}")
                print(f"\n🚨 AVISO DE SISTEMA: {msg_erro}\n")
            except (PDFInfoNotInstalledError, PDFPageCountError) as e:
                msg_erro = (
                    "O Poppler não está instalado ou configurado no PATH do sistema. "
                    "Ele é necessário para converter páginas de PDF em imagem para o OCR.\n"
                    "No Windows: Baixe o Poppler para Windows, extraia e adicione a pasta 'bin' ao PATH.\n"
                    "No Linux: execute 'sudo apt install poppler-utils'\n"
                    "No macOS: execute 'brew install poppler'"
                )
                logger.error(f"Página {numero_pagina}: Poppler ausente. {e}")
                print(f"\n🚨 AVISO DE SISTEMA: {msg_erro}\n")
            except Exception as e:
                logger.error(f"Página {numero_pagina}: Erro durante processamento de OCR: {e}")

        # Definir o nome do arquivo final
        if placa:
            placas_encontradas += 1
            nome_sanitizado = sanitizar_nome_arquivo(placa)
            logger.info(f"Página {numero_pagina}: Nome sanitizado para salvar: {nome_sanitizado}")
        else:
            paginas_sem_placa += 1
            nome_sanitizado = f"PAGINA_{numero_pagina}_SEM_PLACA"
            logger.warning(f"Página {numero_pagina}: Nenhuma placa encontrada. Nomeando como: {nome_sanitizado}")

        # Salvar a página individual
        try:
            leitor_individual = pypdf.PdfReader(caminho_pdf)
            pagina_selecionada = leitor_individual.pages[i]
            
            escritor = pypdf.PdfWriter()
            escritor.add_page(pagina_selecionada)

            caminho_saida = obter_nome_unico_saida(OUTPUT_DIR, nome_sanitizado, placas_geradas_nesta_rodada)

            with open(caminho_saida, 'wb') as f_saida:
                escritor.write(f_saida)
            
            logger.info(f"Página {numero_pagina}: Salva com sucesso em {caminho_saida} (Estratégia: {estrategia_usada})")
        except PermissionError as e:
            logger.error(f"Página {numero_pagina}: Permissão negada ao salvar arquivo em {OUTPUT_DIR}: {e}")
            print(f"🚨 Erro de permissão ao salvar a página {numero_pagina} em {OUTPUT_DIR}: {e}")
        except Exception as e:
            logger.error(f"Página {numero_pagina}: Erro ao extrair e salvar a página: {e}")
            print(f"🚨 Erro ao salvar a página {numero_pagina}: {e}")

    if pdf_plumber_doc:
        pdf_plumber_doc.close()

    # Exclusão automática do PDF original após processamento completo e bem-sucedido de todas as páginas
    if total_paginas > 0 and (placas_encontradas + paginas_sem_placa) == total_paginas:
        try:
            logger.info(f"Removendo o arquivo PDF original com sucesso: {caminho_pdf}")
            os.remove(caminho_pdf)
            print(f"🗑️  Arquivo original removido com sucesso: {os.path.basename(caminho_pdf)}")
        except Exception as e:
            logger.error(f"Erro ao tentar remover o arquivo original {caminho_pdf}: {e}")
            print(f"🚨 Não foi possível remover o arquivo original da pasta 'input': {e}")

    # Exibição do resumo do processamento
    logger.info("=== Processamento concluído com sucesso ===")
    logger.info(f"Resumo: Páginas processadas={total_paginas}, Placas encontradas={placas_encontradas}, Sem placa={paginas_sem_placa}")

    print("\n✅ Processamento concluído!")
    print(f"📄 PDF processado: {os.path.basename(caminho_pdf)}")
    print(f"📑 Total de páginas: {total_paginas}")
    print(f"✅ Placas encontradas: {placas_encontradas}")
    print(f"⚠️  Páginas sem placa: {paginas_sem_placa}")
    print(f"📁 Arquivos salvos em: {OUTPUT_DIR}\n")


def main():
    configurar_pastas()

    # Configuração de Logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOGS_DIR, f"execucao_{timestamp}.log")
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )
    
    # Criar logger específico
    logger = logging.getLogger("pdf_splitter")
    
    logger.info("=== Inicializando o pdf_splitter ===")

    # Buscar arquivos .pdf na pasta input/
    arquivos_pdf = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))

    if not arquivos_pdf:
        msg = "Nenhum arquivo PDF encontrado na pasta 'input/'. Por favor, coloque um arquivo lá."
        logger.warning(msg)
        print(f"⚠️ {msg}")
        return

    # Processa apenas o primeiro arquivo encontrado
    pdf_alvo = arquivos_pdf[0]
    processar_pdf(pdf_alvo, logger)


if __name__ == "__main__":
    main()
