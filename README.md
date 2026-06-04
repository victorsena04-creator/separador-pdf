# PDF Splitter por Placa

Este script divide um PDF grande em várias páginas individuais, nomeando cada arquivo final com base na "placa" encontrada dentro da respectiva página. Ele usa uma estratégia inteligente de busca:
1. Tenta extrair o texto diretamente e de forma rápida.
2. Caso a leitura direta falhe (texto como imagem), aciona automaticamente o OCR (Tesseract) como plano de contingência.

---

## 🛠 Pré-requisitos

Para que o script e o seu fallback OCR funcionem corretamente, você precisa instalar algumas dependências.

### 1. Dependências do Python
Abra o seu terminal (Prompt de Comando ou PowerShell) na pasta deste projeto e execute:
```bash
pip install -r requirements.txt
```

### 2. Dependências do Sistema (OCR e Imagens)
Como o script pode precisar transformar páginas em imagens para "ler" o texto de forma visual, duas ferramentas extras precisam estar instaladas no seu computador:

#### **A) Tesseract OCR** (O Leitor de Imagens)
- **Windows:** 
  1. Baixe o instalador do Tesseract [clicando aqui (UB-Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Durante a instalação, marque a opção para baixar os dados de idioma **Português (Portuguese)**.
  3. Adicione a pasta de instalação (geralmente `C:\Program Files\Tesseract-OCR`) nas suas **Variáveis de Ambiente** (PATH) do Windows.
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt install tesseract-ocr tesseract-ocr-por
  ```
- **macOS:**
  ```bash
  brew install tesseract
  brew install tesseract-lang
  ```

#### **B) Poppler** (O Conversor de PDF para Imagem)
- **Windows:**
  1. Baixe os binários do Poppler para Windows em [Release Poppler](https://github.com/oschwartz10612/poppler-windows/releases/).
  2. Extraia o conteúdo e coloque a pasta em um local seguro (ex: `C:\poppler`).
  3. Adicione a pasta `bin` (ex: `C:\poppler\bin`) nas suas **Variáveis de Ambiente** (PATH) do Windows.
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt install poppler-utils
  ```
- **macOS:**
  ```bash
  brew install poppler
  ```

---

## 🚀 Como Usar

1. O script vai criar as pastas necessárias na primeira vez que rodar. Para já adiantar, crie uma pasta chamada `input` (se ainda não existir) na mesma pasta onde está o arquivo `main.py`.
2. Coloque o PDF original que você quer separar dentro da pasta `input/`.
3. Rode o script no terminal:
   ```bash
   python main.py
   ```
4. O script pegará o **primeiro PDF** que encontrar na pasta `input/` e começará o trabalho.
5. Os arquivos das páginas separadas estarão na pasta `output/`.
6. Um arquivo de relatório (log) contendo todos os detalhes do que aconteceu será salvo na pasta `logs/`.

---

## 📋 Formato Esperado
Para que a placa seja identificada corretamente, o texto (seja legível por texto ou na imagem via OCR) deve conter a palavra "placa:" seguida do valor (letras, números e traços).
Exemplos de formatos que o script entende (não importa se é maiúsculo ou minúsculo):
- `placa: ABC-1234`
- `Placa: ABC1234`
- `PLACA : XYZ-9876`

Se a placa não for encontrada, não se preocupe! A página não será ignorada, mas sim salva como `PAGINA_X_SEM_PLACA.pdf`.
