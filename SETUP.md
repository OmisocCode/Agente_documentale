# Setup Guide - PDF Math Agent

Guida completa per configurare il progetto PDF Math Agent.

## 📋 Prerequisiti

- Python 3.10 o superiore
- pip o Poetry per gestione dipendenze
- Tesseract OCR (opzionale, per PDF scansionati)
- Poppler (opzionale, per conversione PDF→immagini)

## 🚀 Installazione

### 1. Clone del Repository

```bash
git clone <repository-url>
cd Agente_documentale
```

### 2. Ambiente Virtuale

```bash
# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Installazione Dipendenze

```bash
# Installazione standard
pip install -r requirements.txt

# Oppure con pyproject.toml
pip install -e .

# Per sviluppo (include testing tools)
pip install -e ".[dev]"
```

### 4. Configurazione API Keys

```bash
# Copia il file template
cp .env.example .env

# Modifica .env con le tue API keys
nano .env  # o usa il tuo editor preferito
```

**Ottieni le API Keys:**

- **Groq** (Consigliato - Veloce e gratuito): https://console.groq.com/keys
- **Anthropic** (Opzionale - Fallback): https://console.anthropic.com/
- **OpenAI** (Opzionale): https://platform.openai.com/api-keys

**Esempio .env:**
```bash
GROQ_API_KEY=gsk_your_actual_key_here
# ANTHROPIC_API_KEY=sk-ant-your_key_here  # opzionale
# OPENAI_API_KEY=sk-your_key_here  # opzionale
```

### 5. Verifica Configurazione

```bash
# Testa che tutto funzioni
python -c "from src.utils import get_config; config = get_config(); print(f'Config loaded: {config.llm.primary_provider}')"
```

## ⚙️ Configurazione Avanzata

### Personalizzazione config.yaml

Il file `config.yaml` contiene tutte le impostazioni del progetto:

```yaml
# Cambia il modello Groq predefinito
llm:
  groq:
    default_model: "llama-3.3-70b-versatile"  # o mixtral-8x7b-32768

# Personalizza percorsi output
output:
  base_dir: "outputs"
  validate_html: true

# Abilita caching per velocizzare
performance:
  cache:
    enabled: true
    ttl: 604800  # 7 giorni
```

### Installazione OCR (Opzionale)

Per processare PDF scansionati:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-ita tesseract-ocr-eng
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install tesseract tesseract-lang
brew install poppler
```

**Windows:**
- Scarica Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Scarica Poppler: http://blog.alivate.com.au/poppler-windows/
- Aggiungi i path a PATH nelle variabili d'ambiente

## 🧪 Test Installazione

### Test Rapido

```bash
# Test import moduli
python -c "from src.utils import get_logger; logger = get_logger(__name__); logger.info('Setup OK!')"

# Test configurazione
python -c "from src.utils import get_config, get_api_key; config = get_config(); print(get_api_key('groq')[:10] + '...')"
```

### Test Completo (quando implementato)

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Con coverage
pytest --cov=src --cov-report=html
```

## 📂 Struttura Progetto

```
Agente_documentale/
├── src/
│   ├── agents/          # Agent implementations
│   ├── tools/           # PDF, LaTeX, Template tools
│   ├── models/          # Pydantic data models
│   ├── utils/           # Logging, config loading
│   └── templates/       # HTML/CSS templates
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── data/
│   └── samples/         # PDF samples for testing
├── outputs/             # Generated HTML outputs
├── checkpoints/         # Workflow checkpoints
├── logs/                # Application logs
├── config.yaml          # Main configuration
├── .env                 # API keys (not committed)
└── requirements.txt     # Python dependencies
```

## 🎯 Quick Start Usage

### Esempio Base (da implementare)

```python
from src import get_config
from src.agents import PDFSummarizerWorkflow

# Carica configurazione
config = get_config()

# Crea workflow
workflow = PDFSummarizerWorkflow()

# Processa PDF
output_dir = workflow.run(
    pdf_path="data/samples/geometria_proiettiva.pdf",
    pdf_type="latex_compiled"
)

print(f"✅ HTML generato in: {output_dir}")
```

### Esempio CLI (da implementare)

```bash
# Processa PDF
pdf-math-agent process data/samples/paper.pdf --type auto --output outputs/paper

# Riprendi da checkpoint
pdf-math-agent resume --checkpoint checkpoints/task2_12345.json

# Configura logging verbose
LOG_LEVEL=DEBUG pdf-math-agent process paper.pdf
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
# Assicurati di essere nell'ambiente virtuale
source venv/bin/activate

# Reinstalla dipendenze
pip install -r requirements.txt
```

### "API Key not found"
```bash
# Verifica che .env esista e contenga le chiavi
cat .env | grep GROQ_API_KEY

# Verifica che .env sia nella directory root del progetto
ls -la | grep .env
```

### "Configuration file not found"
```bash
# Verifica che config.yaml esista
ls config.yaml

# Se necessario, specifica path custom
export CONFIG_PATH=/path/to/config.yaml
```

## 📚 Prossimi Passi

1. ✅ **Fase 1 completata**: Setup progetto e infrastruttura
2. 🚧 **Fase 2**: Implementare data models (AgentState, Chapter, etc.)
3. 🚧 **Fase 3**: Sviluppare tools (PDF extraction, LaTeX processing)
4. 🚧 **Fase 4**: Implementare i 3 agenti
5. 🚧 **Fase 5**: Orchestrazione workflow con Datapizza

## 🆘 Support

- Leggi il [README.md](README.md) per architettura e design
- Consulta la [documentazione Groq](https://console.groq.com/docs)
- Issues: Apri una issue su GitHub

---

**Fase 1 Setup completata!** 🎉
