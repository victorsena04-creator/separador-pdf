import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def check_and_install_pyinstaller():
    """Verifica se o PyInstaller está instalado, senão o instala."""
    print("Verificando se o PyInstaller está instalado...")
    try:
        import PyInstaller
        print(f"PyInstaller detectado (Versão: {PyInstaller.__version__})")
    except ImportError:
        print("PyInstaller não encontrado. Instalando via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("PyInstaller instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao instalar o PyInstaller: {e}")
            sys.exit(1)


def limpar_diretorios_anteriores():
    """Remove pastas de build anteriores para garantir uma build limpa."""
    print("Limpando diretórios de build anteriores...")
    for pasta in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(pasta):
            try:
                shutil.rmtree(pasta)
                print(f"Diretório removido: {pasta}")
            except Exception as e:
                print(f"Aviso: Não foi possível limpar {pasta}: {e}")


def executar_pyinstaller():
    """Executa o PyInstaller usando o arquivo .spec do projeto."""
    print("\n=== Executando PyInstaller ===")
    spec_path = os.path.join(BASE_DIR, "SeparadorPDF.spec")
    if not os.path.exists(spec_path):
        print(f"Erro: Arquivo .spec não encontrado em {spec_path}")
        sys.exit(1)

    try:
        # Chama o PyInstaller como um módulo python
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            spec_path,
            "--clean",
            "--noconfirm"
        ], check=True)
        print("PyInstaller concluído com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro durante a execução do PyInstaller: {e}")
        sys.exit(1)


def compilar_instalador():
    """Tenta localizar o Inno Setup para compilar o instalador. Caso contrário, gera um ZIP portátil."""
    print("\n=== Compilando Distribuição Final ===")
    
    # Caminhos prováveis do Inno Setup no Windows
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    iscc_found = None
    
    # Verifica no PATH do sistema
    iscc_in_path = shutil.which("ISCC")
    if iscc_in_path:
        iscc_found = iscc_in_path
    else:
        # Verifica os caminhos padrões do Windows
        for path in iscc_paths:
            if os.path.exists(path):
                iscc_found = path
                break

    if iscc_found:
        print(f"Inno Setup Compiler (ISCC) detectado em: {iscc_found}")
        iss_path = os.path.join(BASE_DIR, "setup.iss")
        if os.path.exists(iss_path):
            try:
                print("Compilando instalador do Windows (.exe)...")
                subprocess.run([iscc_found, iss_path], check=True)
                print("\n[SUCCESS] Instalador gerado com sucesso!")
                print(f"O instalador está disponível na pasta 'Output' ou 'dist'.")
                return
            except subprocess.CalledProcessError as e:
                print(f"Erro ao compilar o instalador com o Inno Setup: {e}")
        else:
            print("Erro: Arquivo setup.iss não encontrado.")
    else:
        print("Inno Setup Compiler (ISCC) não foi encontrado no sistema.")

    # Fallback: Criar ZIP Portátil
    print("Gerando arquivo ZIP portátil como alternativa...")
    app_folder = os.path.join(DIST_DIR, "SeparadorPDF")
    if os.path.exists(app_folder):
        zip_output = os.path.join(DIST_DIR, "SeparadorPDF_Portatil")
        try:
            shutil.make_archive(zip_output, 'zip', DIST_DIR, "SeparadorPDF")
            print(f"\n[SUCCESS] Arquivo portátil ZIP gerado com sucesso em: {zip_output}.zip")
        except Exception as e:
            print(f"Erro ao compactar o ZIP portátil: {e}")
    else:
        print("Erro: A pasta do aplicativo compilado não foi encontrada.")


def main():
    check_and_install_pyinstaller()
    limpar_diretorios_anteriores()
    executar_pyinstaller()
    compilar_instalador()


if __name__ == "__main__":
    main()
