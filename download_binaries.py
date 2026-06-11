import os
import sys
import json
import urllib.request
import zipfile
import subprocess
import shutil

# Garantir que a pasta bin existe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
os.makedirs(BIN_DIR, exist_ok=True)

# URL da API de Releases do GitHub
POPPLER_RELEASES_URL = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"
TESSERACT_RELEASES_URL = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"

# Headers para a requisição da API
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_latest_github_release_asset(api_url, file_extension):
    """Obtém a URL de download do asset com a extensão informada na última release."""
    print(f"Buscando informações da release em: {api_url}")
    req = urllib.request.Request(api_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(file_extension):
                    return asset.get("browser_download_url"), asset.get("name")
    except Exception as e:
        print(f"Erro ao consultar a API do GitHub: {e}")
    return None, None


def download_file(url, dest_path):
    """Baixa um arquivo mostrando o progresso."""
    print(f"Baixando: {url} -> {dest_path}")
    
    def reporthook(blocknum, blocksize, totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = min(100, readsofar * 100 / totalsize)
            sys.stdout.write(f"\rProgresso: {percent:.2f}% ({readsofar}/{totalsize} bytes)")
        else:
            sys.stdout.write(f"\rLido: {readsofar} bytes")
        sys.stdout.flush()

    urllib.request.urlretrieve(url, dest_path, reporthook)
    print("\nDownload concluído!")


def instalar_poppler():
    """Baixa e extrai o Poppler."""
    print("\n=== Configurando Poppler ===")
    dest_folder = os.path.join(BIN_DIR, "poppler")
    if os.path.exists(dest_folder):
        print("Poppler já parece estar instalado localmente.")
        return

    url, filename = get_latest_github_release_asset(POPPLER_RELEASES_URL, ".zip")
    if not url:
        print("Não foi possível encontrar a release do Poppler.")
        return

    zip_path = os.path.join(BIN_DIR, filename)
    download_file(url, zip_path)

    print(f"Extraindo {filename}...")
    temp_extract = os.path.join(BIN_DIR, "poppler_temp")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)

    # A pasta zip extraída geralmente contém uma subpasta como "Release-XX.XX.X-X" ou similar.
    # Vamos encontrar essa subpasta e renomeá-la para "poppler".
    subfolders = [f for f in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, f))]
    if subfolders:
        src_path = os.path.join(temp_extract, subfolders[0])
        shutil.move(src_path, dest_folder)
        print(f"Poppler configurado com sucesso em: {dest_folder}")
    else:
        print("Erro: Nenhuma subpasta encontrada no ZIP extraído do Poppler.")

    # Limpar temporários
    shutil.rmtree(temp_extract, ignore_errors=True)
    os.remove(zip_path)


def instalar_tesseract():
    """Baixa e instala o Tesseract OCR silenciosamente na pasta bin."""
    print("\n=== Configurando Tesseract OCR ===")
    dest_folder = os.path.join(BIN_DIR, "Tesseract-OCR")
    if os.path.exists(dest_folder) and os.path.exists(os.path.join(dest_folder, "tesseract.exe")):
        print("Tesseract OCR já parece estar instalado localmente.")
        return

    url, filename = get_latest_github_release_asset(TESSERACT_RELEASES_URL, ".exe")
    if not url:
        # Fallback para url conhecida se falhar a API
        url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
        filename = "tesseract-ocr-w64-setup-5.4.0.20240606.exe"
        print(f"Usando URL fallback estável para Tesseract.")

    exe_path = os.path.join(BIN_DIR, filename)
    download_file(url, exe_path)

    print("Executando instalação silenciosa do Tesseract (isso pode levar de 1 a 2 minutos)...")
    # Inno Setup flags: /VERYSILENT /SUPPRESSMSGBOXES /DIR="caminho"
    try:
        processo = subprocess.run(
            [exe_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", f'/DIR={dest_folder}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print(f"Tesseract OCR configurado com sucesso em: {dest_folder}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao rodar instalador silencioso do Tesseract: {e}")
        print("Tentando executar instalação normal...")
        subprocess.run([exe_path])

    # Deletar instalador após conclusão
    if os.path.exists(exe_path):
        os.remove(exe_path)


def main():
    if sys.platform != "win32":
        print("Este script foi projetado para rodar apenas no Windows.")
        sys.exit(1)

    try:
        instalar_poppler()
        instalar_tesseract()
        print("\n[SUCCESS] Todas as dependências foram configuradas com sucesso na pasta 'bin'!")
    except Exception as e:
        print(f"\n[ERROR] Ocorreu um erro geral durante a configuração das dependências: {e}")


if __name__ == "__main__":
    main()
