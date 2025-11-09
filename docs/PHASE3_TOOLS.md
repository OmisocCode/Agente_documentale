# Fase 3: Tools Development

Documentazione completa dei tools implementati nella Fase 3 per le tre task del pipeline.

## 📋 Panoramica

La Fase 3 implementa tutti i tools necessari per i tre agenti:
1. **PDF Tools** - Chapter Agent (Task 1)
2. **LaTeX Tools** - Classifier Agent (Task 2)
3. **Template Tools** - Composer Agent (Task 3)

---

## 🔧 1. PDF Tools (`src/tools/pdf_tools.py`)

### `PDFExtractor`

Classe principale per estrazione e analisi PDF usando PyMuPDF (fitz).

#### Inizializzazione

```python
from src.tools import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    text = extractor.extract_text()
```

#### Metodi Principali

##### `extract_text(page_range=None)`
Estrae testo da un range di pagine.

```python
# Tutte le pagine
text = extractor.extract_text()

# Pagine specifiche (1-indexed, inclusive)
text = extractor.extract_text((1, 5))  # Pagine 1-5
```

**Parametri:**
- `page_range`: Tuple `(start, end)` (1-indexed) o `None` per tutte le pagine

**Returns:** Testo estratto come stringa

##### `extract_page(page_num)`
Estrae testo da una singola pagina.

```python
page_text = extractor.extract_page(3)  # Pagina 3
```

##### `detect_toc()`
Rileva il TOC (Table of Contents) dal metadata PDF.

```python
toc = extractor.detect_toc()
if toc:
    for entry in toc:
        print(f"Level {entry['level']}: {entry['title']} (page {entry['page']})")
```

**Returns:** Lista di dict con `level`, `title`, `page` o `None`

**Esempio output:**
```python
[
    {"level": 1, "title": "Chapter 1: Introduction", "page": 1},
    {"level": 2, "title": "1.1 Background", "page": 3},
    {"level": 1, "title": "Chapter 2: Methods", "page": 10},
]
```

##### `detect_headings(page_range=None, patterns=None)`
Rileva titoli usando pattern matching regex.

```python
headings = extractor.detect_headings()
for heading in headings:
    print(f"Page {heading['page']}: {heading['title']}")
```

**Parametri:**
- `page_range`: Range di pagine da analizzare
- `patterns`: Lista custom di regex patterns

**Pattern di default:**
- `^Chapter\s+\d+[:\.]?\s+(.+)$` - Chapter 1: Title
- `^Capitolo\s+\d+[:\.]?\s+(.+)$` - Capitolo 1: Titolo
- `^\d+\.\s+([A-Z][^\n]{3,})$` - 1. Title
- `^\d+\.\d+\s+([A-Z][^\n]{3,})$` - 1.1 Title
- `^[A-Z][A-Z\s]{10,}$` - ALL CAPS HEADING
- `^§\s*\d+[:\.]?\s+(.+)$` - § 1: Title

##### `analyze_structure(sample_pages=5)`
Analizza la struttura del documento (font, layout).

```python
structure = extractor.analyze_structure()
print(f"Avg font size: {structure['avg_font_size']}")
print(f"Font range: {structure['font_size_range']}")
```

**Returns:** Dict con statistiche:
- `total_pages`: Totale pagine
- `avg_font_size`: Dimensione media font
- `max_font_size`: Dimensione massima
- `min_font_size`: Dimensione minima
- `font_size_range`: Range dimensioni
- `avg_blocks_per_page`: Media blocchi per pagina
- `most_common_fonts`: Font più comuni

##### `search_text(query, case_sensitive=False)`
Ricerca full-text nel documento.

```python
matches = extractor.search_text("Teorema")
for match in matches:
    print(f"Found on page {match['page']}")
```

##### `extract_images(page_num)`
Estrae immagini da una pagina.

```python
images = extractor.extract_images(5)
for img_bytes in images:
    # Salva o processa immagine
    with open(f"image_{i}.png", "wb") as f:
        f.write(img_bytes)
```

#### Funzioni di Convenienza

```python
from src.tools import (
    extract_text_from_pdf,
    detect_pdf_toc,
    analyze_pdf_structure,
)

# Estrazione veloce
text = extract_text_from_pdf("doc.pdf", page_range=(1, 10))

# TOC veloce
toc = detect_pdf_toc("doc.pdf")

# Analisi struttura
structure = analyze_pdf_structure("doc.pdf")
```

---

## 📐 2. LaTeX Tools (`src/tools/latex_tools.py`)

### `LaTeXProcessor`

Classe per rilevamento e estrazione di strutture matematiche.

#### Inizializzazione

```python
from src.tools import LaTeXProcessor

processor = LaTeXProcessor()
```

#### Metodi Principali

##### `extract_formula(text, confidence_threshold=0.5)`
Estrae formule LaTeX dal testo.

```python
text = "The formula $x^2 + y^2 = r^2$ defines a circle."
formulas = processor.extract_formula(text)

for formula in formulas:
    print(f"LaTeX: {formula['latex']}")
    print(f"Confidence: {formula['confidence']}")
```

**Supporta:**
- Inline math: `$...$`
- Display math: `$$...$$`, `\[...\]`
- Environments: `\begin{equation}...\end{equation}`, `\begin{align}...\end{align}`

**Returns:** Lista di dict con:
- `latex`: Formula LaTeX estratta
- `raw_match`: Match originale completo
- `start`, `end`: Posizioni nel testo
- `confidence`: Score di confidenza (0-1)
- `pattern`: Pattern regex che ha matchato

**Confidence Scoring:**
Il processor calcola automaticamente la confidenza basandosi su:
- Presenza di comandi LaTeX (`\frac`, `\sum`, `\int`, etc.)
- Operatori matematici (`^`, `_`, `=`, etc.)
- Simboli matematici

##### `detect_theorem_blocks(text)`
Rileva blocchi di teoremi, lemmi, corollari.

```python
theorems = processor.detect_theorem_blocks(text)

for thm in theorems:
    print(f"{thm['type']}: {thm['name']}")
    print(f"Content: {thm['content'][:100]}...")
```

**Pattern supportati:**
- Theorem, Teorema, Lemma, Corollary, Corollario, Proposition
- Thm. 1, Theorem 1:, etc.

##### `detect_definitions(text)`
Rileva blocchi di definizioni.

```python
definitions = processor.detect_definitions(text)
```

**Pattern supportati:**
- Definition, Definizione, Def.
- "We define...", "Si definisce..."

##### `detect_proofs(text)`
Rileva blocchi di dimostrazioni.

```python
proofs = processor.detect_proofs(text)
```

**Pattern supportati:**
- Proof, Dimostrazione, Dim.

##### `detect_examples(text)`
Rileva blocchi di esempi.

```python
examples = processor.detect_examples(text)
```

##### `detect_remarks(text)`
Rileva blocchi di note/osservazioni.

```python
remarks = processor.detect_remarks(text)
```

**Pattern supportati:**
- Remark, Nota, Note, Observation, Osservazione

##### `split_into_blocks(text, min_block_size=100)`
Segmenta il testo in blocchi logici classificati.

```python
blocks = processor.split_into_blocks(chapter_text)

for block in blocks:
    print(f"{block['type']}: {block['content'][:50]}...")
```

**Processo:**
1. Rileva tutti i blocchi strutturati (teoremi, definizioni, etc.)
2. Rileva formule
3. Identifica testo narrativo negli spazi tra blocchi strutturati
4. Assegna azione appropriata a ogni blocco

**Returns:** Lista di dict con:
- `type`: BlockType enum
- `content`: Contenuto del blocco
- `name`: Nome (per teoremi/definizioni)
- `latex`: Formula LaTeX (per formule)
- `confidence`: Score di confidenza
- `action`: BlockAction suggerita (summarize/verbatim/latex)

##### `clean_latex(latex)`
Normalizza e pulisce stringhe LaTeX.

```python
dirty = "  x  =  y  +  z  "
clean = processor.clean_latex(dirty)  # "x = y + z"
```

**Operazioni:**
- Rimuove whitespace extra
- Rimuove commenti LaTeX
- Normalizza spaziatura attorno a operatori

##### `extract_unicode_math(text)`
Estrae espressioni matematiche con simboli Unicode.

```python
text = "The sum ∑ᵢ₌₁ⁿ i² = n(n+1)(2n+1)/6"
unicode_math = processor.extract_unicode_math(text)
```

Supporta: ∑, ∏, ∫, ∂, ∇, √, ±, ×, ÷, ≤, ≥, ≠, ≈, ∞, α, β, γ, etc.

#### Funzioni di Convenienza

```python
from src.tools import (
    extract_formulas_from_text,
    split_text_into_blocks,
)

formulas = extract_formulas_from_text(text)
blocks = split_text_into_blocks(chapter_text)
```

---

## 🎨 3. Template Tools (`src/tools/template_tools.py`)

### `TemplateRenderer`

Classe per rendering HTML con Jinja2 e MathJax.

#### Inizializzazione

```python
from src.tools import TemplateRenderer

renderer = TemplateRenderer(template_dir="src/templates")
```

#### Metodi Principali

##### `render_template(template_name, context)`
Renderizza un template Jinja2.

```python
html = renderer.render_template("chapter.html", {
    "title": "Chapter 1",
    "content": "..."
})
```

##### `render_chapter(chapter, css_theme="math-document", include_mathjax=True, navigation=None)`
Renderizza un capitolo completo HTML.

```python
from src.models import ClassifiedChapter

html = renderer.render_chapter(
    chapter=classified_chapter,
    css_theme="math-document",
    include_mathjax=True,
    navigation={"prev": {...}, "next": {...}}
)
```

**Parametri:**
- `chapter`: ClassifiedChapter object
- `css_theme`: Nome tema CSS (math-document, lecture-notes, presentation)
- `include_mathjax`: Include configurazione MathJax
- `navigation`: Dict con link prev/next/index

**Context automatico:**
- `chapter`: Oggetto capitolo
- `title`: Titolo
- `css_theme`: Tema CSS
- `mathjax_config`: Configurazione MathJax
- `has_math`: Boolean, presenza contenuto matematico
- `block_stats`: Statistiche blocchi (totale, teoremi, formule, etc.)

##### `render_index(chapters, title="Document Index", css_theme="math-document")`
Renderizza pagina indice/TOC.

```python
html = renderer.render_index(
    chapters=classified_chapters,
    title="Geometria Proiettiva",
    css_theme="math-document"
)
```

##### `get_mathjax_config(version="3.2.2")`
Genera configurazione MathJax.

```python
mathjax_script = renderer.get_mathjax_config()
```

**Configurazione:**
- Inline math: `\(...\)`
- Display math: `\[...\]`, `$$...$$`
- CDN: jsdelivr.net
- Versione default: 3.2.2

##### `inject_mathjax(html, version="3.2.2")`
Inietta MathJax in HTML esistente.

```python
html_with_mathjax = renderer.inject_mathjax(html)
```

##### `select_css_theme(document_type="math-document")`
Seleziona file CSS per tipo documento.

```python
css_path = renderer.select_css_theme("math-document")
# Returns: "css/math-document.css"
```

**Temi disponibili:**
- `math-document`: Stile textbook accademico professionale
- `lecture-notes`: Stile appunti informali
- `presentation`: Stile slides/presentazioni moderno

##### `generate_navigation(chapters, current_index)`
Genera link di navigazione per un capitolo.

```python
nav = renderer.generate_navigation(all_chapters, current_index=2)

# nav = {
#     "prev": {"id": "ch2", "title": "...", "url": "ch2.html"},
#     "next": {"id": "ch4", "title": "...", "url": "ch4.html"},
#     "index": {"title": "TOC", "url": "index.html"}
# }
```

##### `create_default_templates()`
Crea template HTML di default.

```python
renderer.create_default_templates()
# Crea chapter.html e index.html in template_dir
```

#### Custom Jinja2 Filters

Il renderer aggiunge filtri personalizzati:

**`block_type_class`** - Converte BlockType in classe CSS:
```jinja2
<div class="{{ block.type|block_type_class }}">
<!-- Diventa: <div class="block-theorem"> -->
```

**`render_latex_inline`** - Wrappa LaTeX per MathJax inline:
```jinja2
{{ formula|render_latex_inline }}
<!-- Diventa: \(x^2 + y^2\) -->
```

#### Funzioni di Convenienza

```python
from src.tools import (
    render_chapter_html,
    inject_mathjax_into_html,
)

html = render_chapter_html(chapter, css_theme="lecture-notes")
html_with_math = inject_mathjax_into_html(html)
```

---

## 🎨 4. CSS Themes

### `math-document.css` - Tema Professionale

**Caratteristiche:**
- Font: Georgia, Times New Roman (serif)
- Layout: Max-width 900px, centrato
- Colori: Palette professionale blu/grigio
- Blocchi: Colorati per tipo (teorema=blu, definizione=arancione, formula=grigio)
- Navigation: Sticky top bar
- Features: Back-to-top button, responsive, print styles

**Uso ideale:** Documenti accademici, textbook, articoli scientifici

### `lecture-notes.css` - Tema Informale

**Caratteristiche:**
- Font: Comic Sans MS, handwritten-style
- Background: Effetto carta a righe
- Stile: Casual, friendly
- Colori: Toni caldi, highlight gialli

**Uso ideale:** Appunti di lezione, materiale didattico informale

### `presentation.css` - Tema Moderno

**Caratteristiche:**
- Font: Helvetica Neue, Arial (sans-serif)
- Background: Gradient viola/blu
- Layout: Card-based, box shadow
- Stile: Pulito, moderno, slide-like
- Colori: Blu scuro, accenti luminosi

**Uso ideale:** Presentazioni, slides, materiale web moderno

---

## 🧪 Testing

### Test Suite (`tests/unit/test_tools.py`)

#### LaTeX Tools Tests

```bash
pytest tests/unit/test_tools.py::TestLaTeXProcessor -v
```

**Copertura:**
- ✅ Estrazione formule inline (`$...$`)
- ✅ Estrazione formule display (`$$...$$`)
- ✅ Rilevamento teoremi
- ✅ Rilevamento definizioni
- ✅ Rilevamento dimostrazioni
- ✅ Segmentazione in blocchi
- ✅ Pulizia LaTeX
- ✅ Estrazione Unicode math
- ✅ Calcolo confidence score

#### Template Tools Tests

```bash
pytest tests/unit/test_tools.py::TestTemplateRenderer -v
```

**Copertura:**
- ✅ Creazione template di default
- ✅ Rendering capitolo
- ✅ Rendering indice
- ✅ Generazione configurazione MathJax
- ✅ Iniezione MathJax
- ✅ Selezione tema CSS
- ✅ Generazione navigazione (first/middle/last chapter)
- ✅ Conversione BlockType → CSS class
- ✅ Rendering LaTeX inline

#### PDF Tools Tests

Test placeholder - richiedono file PDF reali per testing completo.

Per testare con PDF reali:
1. Creare directory `tests/fixtures/`
2. Aggiungere sample PDF
3. Implementare test per extract_text, detect_toc, detect_headings, etc.

---

## 📊 Esempi Completi

### Esempio 1: Estrazione e Analisi PDF

```python
from src.tools import PDFExtractor

with PDFExtractor("geometria_proiettiva.pdf") as extractor:
    # Analizza struttura
    structure = extractor.analyze_structure()
    print(f"Documento: {structure['total_pages']} pagine")
    print(f"Font principale: {structure['most_common_fonts'][0]}")

    # Rileva TOC
    toc = extractor.detect_toc()
    if toc:
        print(f"Found {len(toc)} TOC entries")

    # Estrai testo capitolo 1 (pagine 1-10)
    chapter1_text = extractor.extract_text((1, 10))

    # Ricerca keyword
    matches = extractor.search_text("spazio proiettivo")
    print(f"Trovate {len(matches)} occorrenze")
```

### Esempio 2: Classificazione Blocchi

```python
from src.tools import LaTeXProcessor

processor = LaTeXProcessor()

# Segmenta capitolo in blocchi
blocks = processor.split_into_blocks(chapter_text)

# Filtra per tipo
theorems = [b for b in blocks if b['type'] == BlockType.THEOREM]
formulas = [b for b in blocks if b['type'] == BlockType.FORMULA]

print(f"Capitolo contiene:")
print(f"  {len(theorems)} teoremi")
print(f"  {len(formulas)} formule")

# Verifica formule che richiedono revisione
low_confidence = [f for f in formulas if f['confidence'] < 0.6]
print(f"  {len(low_confidence)} formule da rivedere")
```

### Esempio 3: Rendering HTML Completo

```python
from src.tools import TemplateRenderer
from src.models import ClassifiedChapter, ClassifiedBlock

# Crea renderer
renderer = TemplateRenderer()
renderer.create_default_templates()

# Prepara capitoli
chapters = [chapter1, chapter2, chapter3]  # ClassifiedChapter objects

# Renderizza index
index_html = renderer.render_index(
    chapters=chapters,
    title="Geometria Proiettiva - Riassunto",
    css_theme="math-document"
)

# Salva index
with open("output/index.html", "w") as f:
    f.write(index_html)

# Renderizza ogni capitolo
for i, chapter in enumerate(chapters):
    # Genera navigazione
    nav = renderer.generate_navigation(chapters, current_index=i)

    # Renderizza capitolo
    chapter_html = renderer.render_chapter(
        chapter=chapter,
        css_theme="math-document",
        include_mathjax=True,
        navigation=nav
    )

    # Salva
    with open(f"output/{chapter.chapter_id}.html", "w") as f:
        f.write(chapter_html)

print("HTML generato con successo!")
```

---

## ✅ Fase 3 Completata

**Risultati:**
- ✅ 3 moduli tools completi (PDF, LaTeX, Template)
- ✅ PDFExtractor con 10+ metodi
- ✅ LaTeXProcessor con pattern matching avanzato
- ✅ TemplateRenderer con Jinja2 + MathJax
- ✅ 3 temi CSS responsive e professional
- ✅ 25+ test unitari
- ✅ Template HTML estensibili
- ✅ Confidence scoring per formule
- ✅ Context managers per gestione risorse

**Prossimo Step: Fase 4 - Agent Implementation**
- Chapter Agent (Task 1)
- Classifier Agent (Task 2)
- Composer Agent (Task 3)
