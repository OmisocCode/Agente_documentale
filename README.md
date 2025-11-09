# Agente_documentale
Questo progetto mira a creare un agente AI che legge un documento PDF e lo riassume in HTML.

# 📚 PDF Math Agent - Multi-Agent PDF Summarizer

Sistema multi-agente per generare riassunti HTML da PDF matematici, 
preservando formule LaTeX e struttura logica del documento.

## 🏗️ Architettura

### Pipeline Overview
```
Input PDF → Task 1 (Chapter Agent) → Task 2 (Classifier Agent) → Task 3 (Composer Agent) → Output HTML
              ↓                          ↓                           ↓
         [PDF Tools]              [LaTeX Tools]              [Template Engine]
```

### Agenti

#### 🤖 Task 1: Chapter Agent
**Responsabilità**: Divide il PDF in capitoli logici
**Tools disponibili**:
- `extract_text(page_range)`: Estrae testo da range di pagine
- `detect_toc()`: Trova indice se presente
- `detect_headings()`: Pattern matching per titoli
- `analyze_structure()`: Analisi layout per identificare sezioni

**Output**: 
```json
{
  "chapters": [
    {
      "id": "ch1",
      "title": "Capitolo 1: Introduzione",
      "pages": [1, 2, 3, 4],
      "content_raw": "..."
    }
  ]
}
```

#### 🤖 Task 2: Classifier Agent  
**Responsabilità**: Classifica ogni blocco di contenuto
**Tools disponibili**:
- `extract_formula(text)`: OCR matematico con pix2tex
- `detect_theorem_blocks()`: Pattern per teoremi/lemmi/corollari
- `detect_definitions()`: Pattern per definizioni
- `split_into_blocks()`: Segmenta testo in blocchi logici

**Output**:
```json
{
  "chapters": [
    {
      "id": "ch1",
      "blocks": [
        {
          "type": "narrative",  // narrative | theorem | definition | formula
          "content": "...",
          "action": "summarize" // summarize | verbatim | latex
        },
        {
          "type": "theorem",
          "name": "Teorema di Bézout",
          "content": "...",
          "action": "verbatim"
        },
        {
          "type": "formula",
          "latex": "x^2 + y^2 = r^2",
          "action": "latex"
        }
      ]
    }
  ]
}
```

#### 🤖 Task 3: Composer Agent
**Responsabilità**: Genera HTML navigabile con styling
**Tools disponibili**:
- `render_template(template_name, data)`: Jinja2 templating
- `select_css_theme(document_type)`: Sceglie CSS appropriato
- `inject_mathjax()`: Configura MathJax
- `generate_navigation()`: Crea indice e prev/next links

**Output**:
```
outputs/
  ├── index.html
  ├── chapter_01.html
  ├── chapter_02.html
  └── assets/ (symlink a templates/assets/)
```

### State Management

**Pattern**: Ogni task produce output validato che diventa input del successivo
```python
class AgentState:
    pdf_path: str
    pdf_type: str  # "latex_compiled" | "scanned" | "handwritten"
    
    # Dopo Task 1
    chapters: List[Chapter]
    
    # Dopo Task 2  
    classified_blocks: List[ClassifiedChapter]
    
    # Dopo Task 3
    html_files: Dict[str, str]
    output_dir: str
```

**Checkpointing**: Salva stato dopo ogni task per recovery

## 🛠️ Tools Design

### PDF Extraction Strategy
```python
def select_extraction_tool(pdf_type: str) -> Tool:
    if pdf_type == "latex_compiled":
        return PyMuPDFTool()  # Veloce, accurato
    elif pdf_type == "scanned":
        return NougatTool()   # OCR matematico
    elif pdf_type == "handwritten":
        return VisionTool()   # Claude/GPT-4V per trascrizione
```

### LaTeX Processing
- **pix2tex**: Per estrarre LaTeX da immagini di formule
- **Pattern matching**: Per formule già in Unicode (es: x₀, ∑, ∫)
- **Fallback**: Se OCR fallisce, marca formula per revisione manuale

## 🎨 Template System

### CSS Themes
- `math-document.css`: Stile textbook accademico
- `lecture-notes.css`: Stile appunti informali
- `presentation.css`: Stile slides/presentazioni

### Navigation
- Indice cliccabile con scroll-to-section
- Prev/Next chapter buttons
- Back-to-top floating button
- Mobile-responsive

## 🔧 Orchestration con Datapizza
```python
@datapizza.workflow
class PDFSummarizerWorkflow:
    def __init__(self, llm_provider="ollama"):
        self.chapter_agent = ChapterAgent(llm_provider)
        self.classifier_agent = ClassifierAgent(llm_provider)
        self.composer_agent = ComposerAgent(llm_provider)
    
    def run(self, pdf_path: str, pdf_type: str = "auto"):
        # Task 1
        state = AgentState(pdf_path=pdf_path)
        state = self.chapter_agent.execute(state)
        checkpoint.save("task1", state)
        
        # Task 2 - parallelizzabile per capitolo
        state = self.classifier_agent.execute(state)
        checkpoint.save("task2", state)
        
        # Task 3
        state = self.composer_agent.execute(state)
        checkpoint.save("task3", state)
        
        return state.output_dir
```

## 🚨 Error Handling & Robustezza

### Validation Chain
Ogni agente valida il proprio output:
- Task 1: Verifica che chapters.pages non si sovrappongano
- Task 2: Verifica che ogni block abbia type valido
- Task 3: Valida HTML generato (linting)

### Retry Strategy
- Max 3 retry per agente
- Exponential backoff
- Fallback a strategie alternative (es: se Nougat fallisce, usa PyMuPDF)

### Manual Review Flags
Marca contenuti che richiedono revisione:
```json
{
  "type": "formula",
  "latex": "???",
  "confidence": 0.3,
  "needs_review": true,
  "original_text": "[formula illeggibile]"
}
```

## 🎓 Considerazioni di Design

### Perché multi-agente vs monolitico?
- ✅ **Testabilità**: Testi ogni stage indipendentemente
- ✅ **Specializzazione**: LLM diversi per task diversi (es: GPT-4V per vision, Llama per classificazione)
- ✅ **Debugging**: Vedi esattamente dove fallisce
- ✅ **Iterazione**: Migliori un agente senza toccare gli altri
- ⚠️ **Tradeoff**: Più complesso da orchestrare, più chiamate LLM

### Quando usare lo stesso LLM vs diversi?
- **Stesso**: Se budget limitato, o task simili
- **Diversi**: 
  - Task 1: Modello veloce (Llama 3.1 8B)
  - Task 2: Modello accurato con function calling (Claude Sonnet)
  - Task 3: Modello creativo per HTML (GPT-4)

### Cost Optimization
- **Caching**: Salva risultati per PDF già processati
- **Batch processing**: Processa più capitoli insieme nel Task 2
- **Smart prompting**: Usa few-shot solo quando necessario

## 🚀 Usage
```python
from pdf_math_agent import PDFSummarizerWorkflow

workflow = PDFSummarizerWorkflow(
    llm_provider="ollama",  # o "claude"
    model="llama3.1:8b"
)

output_dir = workflow.run(
    pdf_path="geometria_proiettiva.pdf",
    pdf_type="latex_compiled"  # o "auto" per classificazione automatica
)

print(f"✅ HTML generato in: {output_dir}")
```

## 🔮 Future Enhancements
- [ ] Supporto LaTeX → PDF (render formule come immagini)
- [ ] Export Markdown oltre ad HTML
- [ ] Web UI per upload e visualizzazione
- [ ] API REST per integrazione
- [ ] Support multilingua
- [ ] Annotation layer per feedback umano
