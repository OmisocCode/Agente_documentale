# Testing Guide

Guida completa per eseguire i test del PDF Math Agent.

## 📋 Struttura Test

```
tests/
├── unit/                 # Unit tests (non richiedono API)
│   ├── test_models.py    # Test modelli dati
│   ├── test_checkpoint.py # Test checkpoint manager
│   └── test_tools.py     # Test tools (LaTeX, Template)
├── integration/          # Integration tests (richiedono API keys)
│   └── test_workflow.py  # Test workflow completo
└── fixtures/             # File di test (da creare)
    └── sample.pdf        # PDF di esempio
```

## 🧪 Unit Tests

I unit tests NON richiedono API keys o file PDF.

### Eseguire Tutti i Unit Tests

```bash
pytest tests/unit/ -v
```

### Eseguire Test Specifici

```bash
# Test modelli
pytest tests/unit/test_models.py -v

# Test checkpoint
pytest tests/unit/test_checkpoint.py -v

# Test tools
pytest tests/unit/test_tools.py -v
```

### Con Coverage

```bash
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing
```

Il report HTML sarà disponibile in `htmlcov/index.html`.

## 🔗 Integration Tests

I test di integrazione richiedono:
1. API keys valide (Groq, Anthropic, o OpenAI)
2. File PDF di esempio in `tests/fixtures/`

### Setup per Integration Tests

1. **Configura API Keys:**
   ```bash
   cp .env.example .env
   # Modifica .env con le tue API keys
   nano .env
   ```

2. **Aggiungi PDF di Test:**
   ```bash
   mkdir -p tests/fixtures
   # Copia un PDF di test in tests/fixtures/
   cp path/to/sample.pdf tests/fixtures/
   ```

3. **Esegui Integration Tests:**
   ```bash
   pytest tests/integration/ -v
   ```

### Note sui Test di Integrazione

- ⚠️ **Costo**: I test di integrazione effettuano chiamate LLM reali (hanno un costo)
- ⏱️ **Tempo**: Possono richiedere diversi minuti per completare
- 🔑 **API Keys**: Richiedono GROQ_API_KEY (o ANTHROPIC_API_KEY/OPENAI_API_KEY)

## 📝 Test Markers

Utilizziamo markers pytest per organizzare i test:

```bash
# Solo test veloci
pytest -m "not slow"

# Solo test che non richiedono API
pytest -m "not requires_api"

# Solo test che non richiedono PDF
pytest -m "not requires_pdf"
```

## 🎯 Test Specifici

### Test Modelli Dati

```bash
# Test Chapter model
pytest tests/unit/test_models.py::TestChapter -v

# Test AgentState
pytest tests/unit/test_models.py::TestAgentState -v

# Test ClassifiedBlock
pytest tests/unit/test_models.py::TestClassifiedBlock -v
```

### Test Tools

```bash
# Test LaTeX processor
pytest tests/unit/test_tools.py::TestLaTeXProcessor -v

# Test template renderer
pytest tests/unit/test_tools.py::TestTemplateRenderer -v
```

### Test Checkpoint

```bash
pytest tests/unit/test_checkpoint.py -v
```

## 🐛 Debug Tests

Per vedere output dettagliato durante i test:

```bash
# Con print statements
pytest tests/unit/ -v -s

# Con logging
pytest tests/unit/ -v --log-cli-level=DEBUG
```

## 📊 Coverage Report

Per generare un report di coverage completo:

```bash
# Coverage di tutti i test
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Coverage solo unit tests
pytest tests/unit/ --cov=src --cov-report=html
```

Apri `htmlcov/index.html` nel browser per vedere il report interattivo.

## ✅ Test Checklist

Prima di commitare, assicurati che:

- [ ] Tutti i unit tests passano (`pytest tests/unit/`)
- [ ] Coverage > 80% (`pytest tests/unit/ --cov=src`)
- [ ] No warnings o deprecation notices
- [ ] Code formatting OK (`black src/ tests/`)
- [ ] Type hints OK (`mypy src/`)
- [ ] Linting OK (`flake8 src/`)

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
# Assicurati di essere nella root del progetto
cd /path/to/Agente_documentale

# Installa in modalità editable
pip install -e .
```

### "API Key not found"
```bash
# Verifica che .env esista
ls -la .env

# Verifica contenuto
cat .env | grep GROQ_API_KEY
```

### "PDF file not found"
```bash
# Verifica fixtures
ls tests/fixtures/

# Aggiungi PDF di test
cp sample.pdf tests/fixtures/
```

### Test lenti
```bash
# Esegui solo test veloci
pytest tests/unit/ -v --durations=10

# Skip test lenti
pytest tests/unit/ -v -m "not slow"
```

## 📚 Risorse

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 🤝 Contributing

Quando aggiungi nuove feature:

1. Scrivi test unitari per il nuovo codice
2. Assicurati che tutti i test passino
3. Aggiungi test di integrazione se applicabile
4. Aggiorna questa documentazione se necessario
