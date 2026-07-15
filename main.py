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


def configurar_caminhos_dep():
    """
    Configura os caminhos para o Tesseract e Poppler.
    Busca primeiro na pasta local 'bin' do aplicativo (para distribuição autossuficiente),
    depois nos locais de instalação padrões do Windows.
    Retorna o caminho do poppler_path (se encontrado) ou None.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # Se não estiver no executável do PyInstaller, usa o diretório do script
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 1. Configurar Tesseract
    tesseract_local = os.path.join(base_path, "bin", "Tesseract-OCR", "tesseract.exe")
    tesseract_padrao = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    if os.path.exists(tesseract_local):
        pytesseract.pytesseract.tesseract_cmd = tesseract_local
    elif os.path.exists(tesseract_padrao):
        pytesseract.pytesseract.tesseract_cmd = tesseract_padrao
        
    # 2. Configurar Poppler
    poppler_local = os.path.join(base_path, "bin", "poppler", "Library", "bin")
    poppler_padrao = r"C:\poppler\bin"
    
    if os.path.exists(poppler_local):
        return poppler_local
    elif os.path.exists(poppler_padrao):
        return poppler_padrao
        
    return None



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


def extrair_data_pagamento(texto):
    """
    Busca 'Data de Pagamento:', 'Data de Arrecadação:' ou 'Data da Transação:' no texto 
    e retorna a data normalizada como DD-MM-YYYY.
    Aceita formatos: DD/MM/AAAA, DDMMAAAA, DD-MM-YYYY, DD.MM.YYYY.
    Retorna 'SEM_DATA' se não encontrar.
    """
    if not texto:
        return "SEM_DATA"

    # 1. Busca por padrão com delimitadores (tolerando até 150 caracteres de distância, como tabelas)
    padrao = re.compile(
        r'(?:data\s+de\s+(?:pagamento|arrecada[çc][ãa]?o)|data\s+da\s+transa[çc]ã?o)'
        r'[\s\S]{0,150}?'
        r'(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2,4})',
        re.IGNORECASE
    )
    match = padrao.search(texto)
    if match:
        dia, mes, ano = match.group(1), match.group(2), match.group(3)
        try:
            dia_int = int(dia)
            mes_int = int(mes)
            if 1 <= dia_int <= 31 and 1 <= mes_int <= 12:
                dia = dia.zfill(2)
                mes = mes.zfill(2)
                if len(ano) == 2:
                    ano = "20" + ano
                return f"{dia}-{mes}-{ano}"
        except ValueError:
            pass

    # 2. Busca por padrão compacto (sem delimitadores) - restrito à mesma linha para evitar falsos positivos
    padrao_compacto = re.compile(
        r'(?:data\s+de\s+(?:pagamento|arrecada[çc][ãa]?o)|data\s+da\s+transa[çc]ã?o)'
        r'[ \t]*:[ \t]*'
        r'(\d{2})(\d{2})(\d{4})',
        re.IGNORECASE
    )
    match2 = padrao_compacto.search(texto)
    if match2:
        dia, mes, ano = match2.group(1), match2.group(2), match2.group(3)
        try:
            dia_int = int(dia)
            mes_int = int(mes)
            if 1 <= dia_int <= 31 and 1 <= mes_int <= 12:
                return f"{dia}-{mes}-{ano}"
        except ValueError:
            pass

    return "SEM_DATA"


def extrair_valor(texto):
    """
    Busca o valor total do pagamento no texto da página.
    """
    if not texto:
        return "SEM_VALOR"
    
    # 1. Tentar extrair valor após "Valor Total:" ou "VALOR TOTAL"
    padrao_valor_total = re.compile(r'(?:valor\s+total|valor)\s*:?\s*(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})', re.IGNORECASE)
    match = padrao_valor_total.search(texto)
    if match:
        return match.group(1)
        
    # 2. Caso de tabelas onde "Valor Total" está no cabeçalho e o valor está na linha seguinte
    linhas = texto.split("\n")
    for i, linha in enumerate(linhas):
        if "valor total" in linha.lower() and i + 1 < len(linhas):
            linha_seg = linhas[i+1]
            match_seg = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', linha_seg)
            if match_seg:
                return match_seg[-1]
                
    # 3. Fallback: procurar por qualquer valor com R$
    match_rs = re.findall(r'r\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})', texto, re.IGNORECASE)
    if match_rs:
        return match_rs[0]
        
    # 4. Fallback final: procurar por qualquer padrão de valor com vírgula no texto
    match_qualquer = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', texto)
    if match_qualquer:
        return match_qualquer[0]

    return "SEM_VALOR"


def extrair_tipo_pagamento(texto):
    """
    Busca 'Cód. Serviço DETRAN:' no texto e determina o tipo de pagamento.
    Se o código for '001', '003' ou '006', o tipo é 'TRANSF'.
    Se o código for '089' ou '89', o tipo é 'TX REM'.
    Se for outro código, o tipo é 'DÉBITOS'.
    Retorna None se não encontrar o campo.
    """
    if not texto:
        return None

    # 1. Regex flexível para capturar o código do serviço do DETRAN
    padrao = re.compile(
        r'c[oó]d\.?\s*servi[çc]o\s*detran\s*:\s*(\d+)',
        re.IGNORECASE
    )
    match = padrao.search(texto)
    if match:
        codigo = match.group(1).strip()
        try:
            codigo_int = int(codigo)
            if codigo_int in (1, 3, 6):
                return "TRANSF"
            elif codigo_int == 89:
                return "TX REM"
            else:
                return "DÉBITOS"
        except ValueError:
            if codigo in ("001", "003", "006", "1", "3", "6"):
                return "TRANSF"
            elif codigo in ("089", "89"):
                return "TX REM"
            else:
                return "DÉBITOS"

    # 2. Busca secundária por códigos de serviço no formato de tabela (ex: "084 - Autorização...")
    padrao_tabela = re.compile(
        r'\b(\d{2,3})\s*-\s*',
        re.IGNORECASE
    )
    match_tabela = padrao_tabela.search(texto)
    if match_tabela:
        codigo = match_tabela.group(1).strip()
        try:
            codigo_int = int(codigo)
            if codigo_int in (1, 3, 6):
                return "TRANSF"
            elif codigo_int == 89:
                return "TX REM"
            else:
                return "DÉBITOS"
        except ValueError:
            if codigo in ("001", "003", "006", "1", "3", "6"):
                return "TRANSF"
            elif codigo in ("089", "89"):
                return "TX REM"
            else:
                return "DÉBITOS"

    # 3. Classificação pelo valor
    valor = extrair_valor(texto)
    if valor in ("63,39", "63.39"):
        return "DÉBITOS"

    return None


def obter_nome_unico_saida(pasta_saida, nome_base, data_pagamento, placas_geradas):
    """
    Retorna o caminho de saída com placa + data + sufixo de duplicidade.
    Formato: {PLACA}_{DATA}.pdf ou {PLACA}_{DATA}_{N}.pdf
    Garante que não sobrescreva arquivos existentes no disco.
    """
    chave = f"{nome_base}_{data_pagamento}"
    if chave not in placas_geradas:
        placas_geradas[chave] = 1
        caminho = os.path.join(pasta_saida, f"{nome_base}_{data_pagamento}.pdf")
    else:
        placas_geradas[chave] += 1
        contador = placas_geradas[chave]
        caminho = os.path.join(pasta_saida, f"{nome_base}_{data_pagamento}_{contador}.pdf")

    # Garante que o arquivo físico não existe no disco (evita sobrescrever execuções anteriores ou outros arquivos)
    while os.path.exists(caminho):
        placas_geradas[chave] += 1
        contador = placas_geradas[chave]
        caminho = os.path.join(pasta_saida, f"{nome_base}_{data_pagamento}_{contador}.pdf")

    return caminho


def processar_pdf(caminho_pdf, logger, output_dir=None, progress_callback=None):
    """Processa o PDF dividindo suas páginas e identificando as placas."""
    if output_dir is None:
        output_dir = OUTPUT_DIR
    logger.info(f"Iniciando processamento do PDF: {caminho_pdf}")

    try:
        f_input = open(caminho_pdf, 'rb')
        leitor = pypdf.PdfReader(f_input)
        if leitor.is_encrypted:
            logger.error("O arquivo PDF está protegido por senha. Processamento abortado.")
            msg = f"Erro: '{os.path.basename(caminho_pdf)}' está protegido por senha."
            f_input.close()
            if progress_callback:
                progress_callback("error", msg)
            return {"erro": msg}

        total_paginas = len(leitor.pages)
        logger.info(f"Total de páginas detectadas: {total_paginas}")
    except Exception as e:
        logger.error(f"Erro ao abrir o arquivo PDF: {e}")
        msg = f"Erro ao ler o PDF: {e}"
        if 'f_input' in locals() and not f_input.closed:
            f_input.close()
        if progress_callback:
            progress_callback("error", msg)
        return {"erro": msg}

    placas_encontradas = 0
    paginas_sem_placa = 0
    placas_geradas_nesta_rodada = {}

    if progress_callback:
        progress_callback("status", f"Processando {os.path.basename(caminho_pdf)} - 0/{total_paginas} páginas")

    try:
        pdf_plumber_doc = pdfplumber.open(caminho_pdf)
    except Exception as e:
        logger.error(f"Erro ao abrir o PDF com pdfplumber: {e}")
        pdf_plumber_doc = None

    for i in range(total_paginas):
        numero_pagina = i + 1
        logger.info(f"--- Processando página {numero_pagina}/{total_paginas} ---")

        placa = None
        data_pagamento = None
        tipo_pagamento = None
        estrategia_usada = "Nenhuma"

        if pdf_plumber_doc:
            try:
                pagina = pdf_plumber_doc.pages[i]
                texto_direto = pagina.extract_text()
                placa = extrair_placa_com_regex(texto_direto)
                data_pagamento = extrair_data_pagamento(texto_direto)
                tipo_pagamento = extrair_tipo_pagamento(texto_direto)
                if placa:
                    estrategia_usada = "Extração Direta (pdfplumber)"
                    logger.info(f"Página {numero_pagina}: Placa '{placa}' encontrada via Extração Direta.")
            except Exception as e:
                logger.warning(f"Página {numero_pagina}: Falha na extração direta de texto: {e}. Tentando OCR...")

        if not placa:
            logger.info(f"Página {numero_pagina}: Iniciando fallback OCR...")
            try:
                poppler_path = configurar_caminhos_dep()
                imagens = convert_from_path(
                    caminho_pdf,
                    dpi=300,
                    first_page=numero_pagina,
                    last_page=numero_pagina,
                    poppler_path=poppler_path
                )
                if imagens:
                    imagem_pagina = imagens[0]
                    texto_ocr = pytesseract.image_to_string(imagem_pagina, lang='por')
                    placa = extrair_placa_com_regex(texto_ocr)
                    data_pagamento = extrair_data_pagamento(texto_ocr)
                    tipo_pagamento = extrair_tipo_pagamento(texto_ocr)

                    if not placa:
                        logger.info(f"Página {numero_pagina}: Não encontrada placa com lang='por'. Tentando lang='eng'...")
                        texto_ocr_eng = pytesseract.image_to_string(imagem_pagina, lang='eng')
                        placa = extrair_placa_com_regex(texto_ocr_eng)
                        if data_pagamento == "SEM_DATA":
                            data_pagamento = extrair_data_pagamento(texto_ocr_eng)
                        if not tipo_pagamento:
                            tipo_pagamento = extrair_tipo_pagamento(texto_ocr_eng)

                    if placa:
                        estrategia_usada = "OCR (pytesseract)"
                        logger.info(f"Página {numero_pagina}: Placa '{placa}' encontrada via OCR.")
            except pytesseract.TesseractNotFoundError:
                msg_erro = "Tesseract OCR não encontrado no sistema."
                logger.error(f"Página {numero_pagina}: {msg_erro}")
                if progress_callback:
                    progress_callback("warning", f"⚠️ {msg_erro}")
            except (PDFInfoNotInstalledError, PDFPageCountError) as e:
                msg_erro = "Poppler não instalado ou configurado."
                logger.error(f"Página {numero_pagina}: Poppler ausente. {e}")
                if progress_callback:
                    progress_callback("warning", f"⚠️ {msg_erro}")
            except Exception as e:
                logger.error(f"Página {numero_pagina}: Erro durante processamento de OCR: {e}")

        # Garantir que o tipo de pagamento tem um valor default
        if not tipo_pagamento:
            tipo_pagamento = "SEM_TIPO"

        if placa:
            placas_encontradas += 1
            placa_limpa = sanitizar_nome_arquivo(placa)
            nome_sanitizado = f"{placa_limpa}-{tipo_pagamento}"
            if not data_pagamento:
                data_pagamento = "SEM_DATA"
            logger.info(f"Página {numero_pagina}: Nome: {nome_sanitizado}_{data_pagamento}")
        else:
            paginas_sem_placa += 1
            nome_sanitizado = f"PAGINA_{numero_pagina}_SEM_PLACA-{tipo_pagamento}"
            data_pagamento = "SEM_DATA"
            logger.warning(f"Página {numero_pagina}: Nenhuma placa encontrada. Nomeando como: {nome_sanitizado}")

        try:
            pagina_selecionada = leitor.pages[i]
            
            escritor = pypdf.PdfWriter()
            escritor.add_page(pagina_selecionada)

            caminho_saida = obter_nome_unico_saida(output_dir, nome_sanitizado, data_pagamento, placas_geradas_nesta_rodada)

            with open(caminho_saida, 'wb') as f_saida:
                escritor.write(f_saida)
            
            logger.info(f"Página {numero_pagina}: Salva com sucesso em {caminho_saida} (Estratégia: {estrategia_usada})")
        except PermissionError as e:
            logger.error(f"Página {numero_pagina}: Permissão negada ao salvar arquivo em {output_dir}: {e}")
            if progress_callback:
                progress_callback("error", f"Erro de permissão: {e}")
        except Exception as e:
            logger.error(f"Página {numero_pagina}: Erro ao extrair e salvar a página: {e}")
            if progress_callback:
                progress_callback("error", f"Erro ao salvar: {e}")

        if progress_callback:
            progress_callback("progress", numero_pagina, total_paginas)

    if pdf_plumber_doc:
        pdf_plumber_doc.close()

    # Fechar o stream do arquivo de entrada para liberar o lock no Windows
    try:
        f_input.close()
        logger.info("Stream do arquivo PDF de entrada fechado com sucesso.")
    except Exception as e:
        logger.warning(f"Erro ao fechar o stream do arquivo de entrada: {e}")

    if total_paginas > 0 and (placas_encontradas + paginas_sem_placa) == total_paginas:
        try:
            logger.info(f"Removendo o arquivo PDF original com sucesso: {caminho_pdf}")
            os.remove(caminho_pdf)
        except Exception as e:
            logger.error(f"Erro ao tentar remover o arquivo original {caminho_pdf}: {e}")

    logger.info("=== Processamento concluído com sucesso ===")
    logger.info(f"Resumo: Páginas processadas={total_paginas}, Placas encontradas={placas_encontradas}, Sem placa={paginas_sem_placa}")

    resultado = {
        "arquivo": os.path.basename(caminho_pdf),
        "total_paginas": total_paginas,
        "placas_encontradas": placas_encontradas,
        "paginas_sem_placa": paginas_sem_placa,
        "output_dir": output_dir
    }

    if progress_callback:
        progress_callback("complete", resultado)

    return resultado


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
