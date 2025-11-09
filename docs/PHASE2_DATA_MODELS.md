# Fase 2: Data Models e State Management

Documentazione completa dei modelli dati implementati nella Fase 2.

## 📋 Panoramica

La Fase 2 implementa tutti i modelli Pydantic necessari per gestire lo stato del workflow e i dati attraverso le tre task del pipeline.

## 🎯 Modelli Implementati

### 1. Enumerazioni (`src/models/enums.py`)

#### `BlockType`
Tipi di contenuto in un documento:
- `NARRATIVE`: Testo narrativo/spiegazione
- `THEOREM`: Teorema, lemma o corollario
- `DEFINITION`: Definizione matematica
- `FORMULA`: Formula/equazione matematica
- `PROOF`: Dimostrazione
- `EXAMPLE`: Esempio risolto
- `EXERCISE`: Esercizio o problema
- `REMARK`: Nota o osservazione

#### `BlockAction`
Azioni da eseguire su un blocco:
- `SUMMARIZE`: Riassumi il contenuto
- `VERBATIM`: Mantieni il contenuto così com'è
- `LATEX`: Renderizza come LaTeX (per formule)
- `SKIP`: Salta questo blocco

#### `PDFType`
Tipo di documento PDF:
- `AUTO`: Rilevamento automatico
- `LATEX_COMPILED`: PDF compilato da sorgente LaTeX
- `SCANNED`: Documento scansionato (richiede OCR)
- `HANDWRITTEN`: Documento scritto a mano (richiede vision models)
- `MIXED`: Contenuto misto

#### `ProcessingStatus`
Stato di elaborazione:
- `PENDING`: Non ancora iniziato
- `IN_PROGRESS`: In elaborazione
- `COMPLETED`: Completato con successo
- `FAILED`: Elaborazione fallita
- `CANCELLED`: Cancellato dall'utente

#### `AgentTask`
Identificatori delle task:
- `TASK_1_CHAPTER`: Estrazione capitoli (Task 1)
- `TASK_2_CLASSIFIER`: Classificazione contenuti (Task 2)
- `TASK_3_COMPOSER`: Composizione HTML (Task 3)

---

### 2. Chapter Models (`src/models/chapter.py`)

#### `Chapter`
Rappresenta un capitolo o sezione in un PDF.

**Attributi principali:**
```python
id: str                    # Identificatore unico (es. "ch1")
title: str                 # Titolo del capitolo
pages: List[int]           # Numeri di pagina (1-indexed)
content_raw: str           # Testo estratto
parent_id: Optional[str]   # ID capitolo padre (per sezioni annidate)
level: int                 # Livello di annidamento (0=capitolo, 1=sezione, etc.)
metadata: dict             # Metadati aggiuntivi
```

**Metodi utili:**
- `get_page_count()`: Numero di pagine nel capitolo
- `get_word_count()`: Conteggio parole approssimativo
- `get_page_range()`: Range pagine formattato (es. "1-5, 7-10")
- `is_nested()`: Verifica se è una sezione annidata
- `update_metadata()`: Aggiorna metadati con valori calcolati

**Validazioni:**
- Pagine sono automaticamente ordinate e deduplicate
- Page numbers devono essere positivi

**Esempio:**
```python
chapter = Chapter(
    id="ch1",
    title="Capitolo 1: Introduzione",
    pages=[1, 2, 3, 4],
    content_raw="Questo capitolo introduce...",
    level=0
)

print(chapter.get_page_range())  # "1-4"
print(chapter.get_word_count())  # Conteggio parole
```

#### `ChapterCollection`
Collezione di capitoli estratti da un PDF.

**Attributi:**
```python
chapters: List[Chapter]    # Lista di capitoli
total_pages: int           # Numero totale di pagine nel documento
pdf_path: str              # Percorso al PDF sorgente
```

**Metodi:**
- `get_chapter_by_id(chapter_id)`: Trova capitolo per ID
- `get_chapter_by_page(page_num)`: Trova capitolo contenente una pagina
- `get_coverage_percentage()`: % di documento coperto dai capitoli
- `sort_chapters_by_page()`: Ordina capitoli per pagina iniziale

**Validazioni:**
- Verifica che i capitoli non abbiano pagine sovrapposte
- Solleva `ValueError` se trova overlap

**Esempio:**
```python
collection = ChapterCollection(
    chapters=[ch1, ch2, ch3],
    total_pages=100,
    pdf_path="geometria.pdf"
)

coverage = collection.get_coverage_percentage()  # 85.0%
ch = collection.get_chapter_by_page(15)  # Trova capitolo con pagina 15
```

---

### 3. Block Models (`src/models/block.py`)

#### `ClassifiedBlock`
Blocco di contenuto classificato all'interno di un capitolo.

**Attributi:**
```python
type: BlockType                # Tipo di blocco
content: str                   # Contenuto testuale
action: BlockAction            # Azione da eseguire
name: Optional[str]            # Nome (es. "Teorema di Bézout")
latex: Optional[str]           # Formula LaTeX se applicabile
confidence: float              # Score di confidenza (0-1)
needs_review: bool             # Flag per revisione manuale
metadata: dict                 # Metadati aggiuntivi
```

**Validazioni automatiche:**
- Blocchi con `confidence < 0.6` sono automaticamente flaggati per review
- Blocchi `FORMULA` senza LaTeX sono flaggati per review

**Metodi:**
- `is_mathematical()`: Verifica se contiene contenuto matematico
- `should_preserve_verbatim()`: Verifica se preservare il contenuto
- `should_summarize()`: Verifica se riassumere
- `get_display_name()`: Nome visualizzato (name o tipo)

**Esempio:**
```python
block = ClassifiedBlock(
    type=BlockType.THEOREM,
    content="Siano a e b due interi...",
    action=BlockAction.VERBATIM,
    name="Teorema di Bézout",
    confidence=0.95
)

if block.is_mathematical():
    print(f"Teorema matematico: {block.get_display_name()}")
```

#### `ClassifiedChapter`
Capitolo con blocchi di contenuto classificati.

**Attributi:**
```python
chapter_id: str                      # Riferimento all'ID del Chapter originale
title: str                           # Titolo capitolo
blocks: List[ClassifiedBlock]        # Blocchi classificati
summary: Optional[str]               # Riassunto del capitolo (opzionale)
metadata: dict                       # Metadati
```

**Metodi:**
- `get_blocks_by_type(block_type)`: Filtra blocchi per tipo
- `get_blocks_needing_review()`: Blocchi che richiedono revisione
- `get_formulas()`: Tutti i blocchi formula
- `get_theorems()`: Tutti i blocchi teorema
- `get_definitions()`: Tutte le definizioni
- `has_mathematical_content()`: Verifica presenza contenuto matematico
- `get_confidence_stats()`: Statistiche di confidenza (min, max, avg, median)

**Esempio:**
```python
chapter = ClassifiedChapter(
    chapter_id="ch1",
    title="Introduzione",
    blocks=[block1, block2, block3]
)

theorems = chapter.get_theorems()
stats = chapter.get_confidence_stats()
print(f"Confidenza media: {stats['avg']:.2f}")
```

#### `ClassifiedDocument`
Documento completo con tutti i capitoli classificati.

**Attributi:**
```python
pdf_path: str                        # Percorso al PDF sorgente
chapters: List[ClassifiedChapter]    # Capitoli classificati
total_blocks: int                    # Numero totale di blocchi
metadata: dict                       # Metadati del documento
```

**Metodi:**
- `get_chapter_by_id(chapter_id)`: Trova capitolo per ID
- `get_all_blocks_needing_review()`: Tutti i blocchi da rivedere
- `get_document_stats()`: Statistiche del documento

**Esempio:**
```python
doc = ClassifiedDocument(
    pdf_path="geometria.pdf",
    chapters=[classified_ch1, classified_ch2]
)

stats = doc.get_document_stats()
print(f"Totale teoremi: {stats['total_theorems']}")
print(f"Blocchi da rivedere: {stats['total_needing_review']}")
```

---

### 4. State Models (`src/models/state.py`)

#### `TaskResult`
Risultato di una singola task dell'agente.

**Attributi:**
```python
task: AgentTask                      # Identificatore task
status: ProcessingStatus             # Stato elaborazione
started_at: Optional[datetime]       # Timestamp inizio
completed_at: Optional[datetime]     # Timestamp completamento
duration_seconds: Optional[float]    # Durata in secondi
error: Optional[str]                 # Messaggio errore se fallita
metadata: dict                       # Metadati task
```

**Metodi:**
- `start()`: Marca task come iniziata
- `complete()`: Marca task come completata
- `fail(error_message)`: Marca task come fallita
- `is_completed()`: Verifica se completata
- `is_failed()`: Verifica se fallita

#### `AgentState`
Stato globale del workflow PDF processing.

**Attributi principali:**
```python
# Identificatori
session_id: str                      # ID sessione univoco
pdf_path: str                        # Percorso al PDF input
pdf_type: PDFType                    # Tipo di PDF

# Timestamps
created_at: datetime                 # Creazione stato
updated_at: datetime                 # Ultimo aggiornamento

# Output Task 1
chapter_collection: Optional[ChapterCollection]

# Output Task 2
classified_document: Optional[ClassifiedDocument]

# Output Task 3
html_files: Dict[str, str]           # chapter_id -> file_path
output_dir: Optional[str]            # Directory output

# Tracking
task_results: Dict[str, TaskResult]  # Risultati per ogni task
current_task: Optional[AgentTask]    # Task corrente
metadata: dict                       # Metadati aggiuntivi
```

**Metodi chiave:**

**Gestione Task:**
- `start_task(task)`: Inizia una task
- `complete_task(task)`: Completa una task
- `fail_task(task, error)`: Marca task come fallita
- `get_task_result(task)`: Ottieni risultato task
- `is_task_completed(task)`: Verifica se completata

**Workflow:**
- `get_next_task()`: Ottieni prossima task da eseguire
- `get_completed_tasks()`: Lista task completate
- `get_progress_percentage()`: Percentuale di completamento (0-100)
- `get_total_duration()`: Durata totale in secondi

**Validazione:**
- `validate_task1_output()`: Valida output Task 1
- `validate_task2_output()`: Valida output Task 2
- `validate_task3_output()`: Valida output Task 3

**Utilità:**
- `get_summary()`: Riepilogo dello stato
- `update_timestamp()`: Aggiorna timestamp

**Esempio completo:**
```python
# Crea stato iniziale
state = AgentState(
    session_id="20240109_143022_abc123",
    pdf_path="geometria.pdf",
    pdf_type=PDFType.LATEX_COMPILED
)

# Task 1
state.start_task(AgentTask.TASK_1_CHAPTER)
# ... esegui estrazione capitoli ...
state.chapter_collection = collection
state.complete_task(AgentTask.TASK_1_CHAPTER)

# Task 2
state.start_task(AgentTask.TASK_2_CLASSIFIER)
# ... esegui classificazione ...
state.classified_document = classified_doc
state.complete_task(AgentTask.TASK_2_CLASSIFIER)

# Task 3
state.start_task(AgentTask.TASK_3_COMPOSER)
# ... genera HTML ...
state.html_files = {"ch1": "output/ch1.html"}
state.output_dir = "output/"
state.complete_task(AgentTask.TASK_3_COMPOSER)

# Verifica progresso
print(f"Progresso: {state.get_progress_percentage()}%")  # 100%
summary = state.get_summary()
```

---

### 5. Checkpoint Manager (`src/utils/checkpoint_manager.py`)

#### `CheckpointManager`
Gestisce il salvataggio e caricamento dello stato del workflow.

**Metodi principali:**

**Salvataggio:**
```python
save(state: AgentState, task: Optional[AgentTask] = None, metadata: dict = None) -> Path
```
Salva lo stato in formato JSON.

**Caricamento:**
```python
load(session_id: str, task: Optional[AgentTask] = None) -> Optional[AgentState]
load_latest(session_id: str) -> Optional[AgentState]
```

**Gestione:**
```python
list_checkpoints(session_id: Optional[str] = None) -> List[dict]
delete_checkpoint(session_id: str, task: Optional[AgentTask] = None) -> bool
delete_session(session_id: str) -> int
```

**Recovery:**
```python
auto_recover(session_id: str) -> Optional[AgentState]
```
Tenta di recuperare dallo stato più recente valido (Task 3 → Task 2 → Task 1).

**Pulizia:**
```python
cleanup_old_checkpoints(days: int = 7) -> int
```

**Esempio completo:**
```python
from src.utils import get_checkpoint_manager
from src.models import AgentState, AgentTask

# Ottieni manager
manager = get_checkpoint_manager(checkpoint_dir="checkpoints")

# Salva checkpoint dopo Task 1
manager.save(state, AgentTask.TASK_1_CHAPTER, metadata={"note": "Extraction complete"})

# Lista checkpoints disponibili
checkpoints = manager.list_checkpoints("session_123")
for cp in checkpoints:
    print(f"Task: {cp['task']}, Saved: {cp['saved_at']}")

# Carica checkpoint specifico
state = manager.load("session_123", AgentTask.TASK_1_CHAPTER)

# Auto-recovery da ultimo checkpoint valido
state = manager.auto_recover("session_123")

# Pulizia checkpoints vecchi
deleted = manager.cleanup_old_checkpoints(days=7)
print(f"Deleted {deleted} old checkpoints")
```

---

## 🧪 Testing

### Unit Tests Implementati

**`tests/unit/test_models.py`**:
- ✅ Test creazione e validazione `Chapter`
- ✅ Test ordinamento e deduplicazione pagine
- ✅ Test formattazione page range
- ✅ Test `ChapterCollection` e validazione overlap
- ✅ Test `ClassifiedBlock` e auto-flagging bassa confidenza
- ✅ Test filtri per tipo di blocco
- ✅ Test statistiche confidenza
- ✅ Test `AgentState` lifecycle (start/complete/fail)
- ✅ Test sequenza task e progresso
- ✅ Test timing delle task

**`tests/unit/test_checkpoint.py`**:
- ✅ Test salvataggio checkpoint
- ✅ Test caricamento checkpoint
- ✅ Test load_latest
- ✅ Test list_checkpoints
- ✅ Test delete_checkpoint e delete_session
- ✅ Test auto_recover
- ✅ Test checkpoint con metadata custom

### Eseguire i Test

```bash
# Tutti i test
pytest tests/unit/ -v

# Test specifici
pytest tests/unit/test_models.py -v
pytest tests/unit/test_checkpoint.py -v

# Con coverage
pytest tests/unit/ --cov=src/models --cov=src/utils --cov-report=html
```

---

## 📊 Diagramma Flusso Dati

```
PDF Input
    ↓
┌─────────────────────────────────────────┐
│ AgentState (session_id, pdf_path)      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Task 1: Chapter Agent                   │
│ Output: ChapterCollection               │
│   └─ List[Chapter]                      │
└─────────────────────────────────────────┘
    ↓ (checkpoint saved)
┌─────────────────────────────────────────┐
│ Task 2: Classifier Agent                │
│ Output: ClassifiedDocument              │
│   └─ List[ClassifiedChapter]            │
│       └─ List[ClassifiedBlock]          │
└─────────────────────────────────────────┘
    ↓ (checkpoint saved)
┌─────────────────────────────────────────┐
│ Task 3: Composer Agent                  │
│ Output: html_files + output_dir         │
└─────────────────────────────────────────┘
    ↓ (checkpoint saved)
HTML Output
```

---

## ✅ Fase 2 Completata

**Risultati:**
- ✅ 5 enumerazioni definite
- ✅ 7 modelli Pydantic implementati
- ✅ Sistema checkpoint completo
- ✅ 40+ test unitari
- ✅ Validazioni automatiche
- ✅ Documentazione completa

**Prossimo Step: Fase 3 - Tools Development**
- PDF extraction tools
- LaTeX processing tools
- Template rendering tools
