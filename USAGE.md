# 📖 Usage Guide - PDF Math Agent

Complete guide for using the PDF Math Agent system to convert mathematical PDFs into navigable HTML summaries.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Agente_documentale

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Edit and add your API keys
nano .env
```

Required API keys (choose at least one):

```env
# Groq (recommended - fastest and most cost-effective)
GROQ_API_KEY=your_groq_api_key_here

# Alternative providers
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

Get API keys:
- **Groq**: https://console.groq.com/keys (Free tier available)
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys

### 3. Basic Usage

```bash
# Process a PDF with default settings
python -m src.cli process path/to/document.pdf

# Specify PDF type and theme
python -m src.cli process document.pdf --type latex_compiled --theme lecture-notes

# Use a specific LLM provider
python -m src.cli process document.pdf --provider groq
```

### 4. View Output

The generated HTML will be in `outputs/<pdf_name>/`:

```bash
# Open in browser
open outputs/document/index.html

# Or use a local server
cd outputs/document
python -m http.server 8000
# Visit http://localhost:8000
```

## 🎛️ Command Reference

### Process Command

```bash
python -m src.cli process <PDF_PATH> [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--type` | `auto` | PDF type: `latex_compiled`, `scanned`, `handwritten`, `auto` |
| `--theme` | `math-document` | CSS theme: `math-document`, `lecture-notes`, `presentation` |
| `--provider` | `groq` | LLM provider: `groq`, `anthropic`, `openai`, `mock` |
| `--output` | `outputs/<pdf_name>` | Custom output directory |
| `--no-checkpoints` | `False` | Disable checkpoint saving |

**Examples:**

```bash
# Auto-detect PDF type
python -m src.cli process algebra.pdf

# Scanned PDF with OCR
python -m src.cli process scanned_book.pdf --type scanned

# Custom output location
python -m src.cli process notes.pdf --output ~/Documents/summaries/notes

# Use lecture notes theme
python -m src.cli process lecture.pdf --theme lecture-notes

# Disable checkpointing (faster, no resume capability)
python -m src.cli process quick_test.pdf --no-checkpoints
```

### Resume Command

Resume processing from a saved checkpoint:

```bash
python -m src.cli resume <SESSION_ID>
```

**Example:**

```bash
# If processing was interrupted, resume from last checkpoint
python -m src.cli resume algebra_20250110_123456
```

### Info Command

Display system configuration and available models:

```bash
python -m src.cli info
```

## 📊 PDF Type Guide

### LaTeX Compiled (`latex_compiled`)

**Best for:** Academic papers, textbooks, professionally typeset documents

**Characteristics:**
- Clean, computer-generated text
- Embedded fonts and structure
- Mathematical formulas in vector format

**Processing:**
- Fast extraction with PyMuPDF
- High accuracy for formulas and structure
- Recommended for most mathematical documents

**Example:**
```bash
python -m src.cli process arxiv_paper.pdf --type latex_compiled
```

### Scanned (`scanned`)

**Best for:** Scanned books, photocopied documents, image-based PDFs

**Characteristics:**
- PDF contains images of pages
- No embedded text layer
- Requires OCR

**Processing:**
- Uses Tesseract OCR for text
- pix2tex for mathematical formulas
- Slower but handles non-digital documents

**Example:**
```bash
python -m src.cli process scanned_textbook.pdf --type scanned
```

### Handwritten (`handwritten`)

**Best for:** Handwritten notes, whiteboard photos

**Characteristics:**
- Handwritten mathematical content
- Variable quality
- Requires vision models

**Processing:**
- Uses Claude Vision or GPT-4V
- Best-effort transcription
- May require manual review

**Example:**
```bash
python -m src.cli process handwritten_notes.pdf --type handwritten --provider anthropic
```

### Auto (`auto`)

**Best for:** Unknown or mixed PDF types

**Processing:**
- Automatically detects PDF type
- Uses heuristics (font analysis, text extraction quality)
- Falls back to appropriate extraction method

**Example:**
```bash
python -m src.cli process unknown.pdf --type auto
```

## 🎨 CSS Themes

### Math Document (`math-document`)

**Style:** Clean, academic textbook

**Features:**
- Serif fonts for readability
- Wide margins for formulas
- Professional theorem boxes
- Good for dense mathematical content

**Use for:**
- Research papers
- Textbooks
- Formal mathematical documents

### Lecture Notes (`lecture-notes`)

**Style:** Informal, handwritten feel

**Features:**
- Sans-serif fonts
- Colorful sections
- Compact layout
- Emphasis on examples

**Use for:**
- Lecture notes
- Study guides
- Quick references

### Presentation (`presentation`)

**Style:** Slide-like, visual

**Features:**
- Large fonts
- High contrast
- Minimal text per section
- Focus on key points

**Use for:**
- Presentation materials
- Summaries
- Quick overviews

## 🔧 Advanced Usage

### Using Mock LLM for Testing

Test the workflow without API keys:

```bash
python -m src.cli process test.pdf --provider mock
```

This is useful for:
- Testing the pipeline
- Development and debugging
- CI/CD integration tests

### Checkpoint Management

Checkpoints allow resuming interrupted processing:

**Location:** `checkpoints/<session_id>_task*.json`

**Resume after interruption:**
```bash
# Find session ID from checkpoint files
ls checkpoints/

# Resume from last checkpoint
python -m src.cli resume <session_id>
```

**Disable checkpoints for speed:**
```bash
python -m src.cli process document.pdf --no-checkpoints
```

### Custom Configuration

Edit `config.yaml` to customize:

```yaml
# Processing settings
processing:
  default_pdf_type: "auto"
  max_pages_per_chapter: 50
  min_confidence_threshold: 0.7

# LLM settings
llm:
  groq:
    default_model: "llama-3.3-70b-versatile"
    temperature: 0.7
    max_tokens: 4096

# Output settings
output:
  default_theme: "math-document"
  save_intermediate_results: true
  generate_toc: true
```

### Programmatic Usage

Use as a Python library:

```python
from src.workflow import PDFSummarizerWorkflow
from src.models.enums import PDFType

# Create workflow
workflow = PDFSummarizerWorkflow(
    llm_provider="groq",
    css_theme="math-document",
    enable_checkpoints=True
)

# Process PDF
output_dir = workflow.run(
    pdf_path="algebra.pdf",
    pdf_type="latex_compiled",
    session_id="custom_session"
)

print(f"HTML generated in: {output_dir}")
```

## 📈 Performance Tips

### 1. Choose the Right Provider

**Groq:**
- Fastest processing
- Cost-effective
- Best for most use cases
- Limited context window

**Anthropic (Claude):**
- Best for complex documents
- Excellent vision capabilities
- Handles handwritten content
- Higher cost

**OpenAI (GPT-4):**
- Good balance
- Strong vision models
- Moderate cost

### 2. Optimize PDF Type Detection

Explicitly specify PDF type to skip auto-detection:

```bash
# Faster - no auto-detection
python -m src.cli process paper.pdf --type latex_compiled

# Slower - auto-detection runs
python -m src.cli process paper.pdf --type auto
```

### 3. Use Checkpoints for Long Documents

Enable checkpoints for documents > 50 pages:

```bash
python -m src.cli process long_book.pdf
# If interrupted, resume with:
python -m src.cli resume <session_id>
```

### 4. Batch Processing

Process multiple PDFs:

```bash
# Bash script
for pdf in documents/*.pdf; do
    python -m src.cli process "$pdf" --theme lecture-notes
done
```

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error:** `GROQ_API_KEY not found in environment`

**Solution:**
```bash
# Verify .env file exists
cat .env

# Check key is set
export GROQ_API_KEY=your_key_here

# Or add to .env
echo "GROQ_API_KEY=your_key_here" >> .env
```

#### 2. Chapter Extraction Failed

**Error:** `Invalid Task 1 output: no chapters extracted`

**Causes:**
- PDF has no structure (TOC, headings)
- PDF is image-only (use `--type scanned`)
- Very short document

**Solution:**
```bash
# Try different PDF type
python -m src.cli process doc.pdf --type scanned

# Check PDF manually
python -c "import fitz; doc = fitz.open('doc.pdf'); print(doc.get_toc())"
```

#### 3. Formula Recognition Failed

**Error:** Formulas appear as garbled text

**Causes:**
- Scanned PDF without OCR
- Handwritten formulas
- Poor scan quality

**Solution:**
```bash
# Use pix2tex OCR for formulas
python -m src.cli process doc.pdf --type scanned

# For handwritten, use vision models
python -m src.cli process doc.pdf --type handwritten --provider anthropic
```

#### 4. Out of Memory

**Error:** `MemoryError` or process killed

**Causes:**
- Very large PDF (> 500 pages)
- High-resolution scans

**Solution:**
```bash
# Process in smaller chunks (TODO: implement chunking)
# Or reduce scan resolution before processing

# Check PDF size
ls -lh document.pdf
```

### Debugging

Enable debug logging:

```bash
# Set log level in config.yaml
logging:
  level: "DEBUG"

# Or via environment variable
export LOG_LEVEL=DEBUG
python -m src.cli process document.pdf
```

View logs:

```bash
# Logs are in logs/
tail -f logs/pdf_math_agent.log
```

## 📊 Output Structure

Generated output directory structure:

```
outputs/
└── document_name/
    ├── index.html              # Main navigation page
    ├── chapter_01.html         # Chapter 1 content
    ├── chapter_02.html         # Chapter 2 content
    ├── ...
    └── assets/                 # CSS and JavaScript (symlink)
        ├── css/
        │   ├── math-document.css
        │   ├── lecture-notes.css
        │   └── presentation.css
        └── js/
            └── mathjax-config.js
```

**HTML Features:**

- ✅ MathJax for formula rendering
- ✅ Syntax highlighting for code
- ✅ Responsive design (mobile-friendly)
- ✅ Navigation sidebar
- ✅ Prev/Next chapter buttons
- ✅ Back-to-top button
- ✅ Printable CSS

## 🔬 Testing

### Run Tests

```bash
# All tests
pytest

# Integration tests only
pytest tests/test_integration_workflow.py

# With coverage
pytest --cov=src tests/

# Specific test
pytest tests/test_integration_workflow.py::TestWorkflowIntegration::test_workflow_task1_chapters_extracted -v
```

### Test with Mock LLM

No API keys required:

```bash
# Process test PDF
python -m src.cli process data/samples/test.pdf --provider mock

# Run integration tests
pytest tests/test_integration_workflow.py
```

## 📚 Examples

### Example 1: Research Paper

```bash
# Process LaTeX-compiled research paper
python -m src.cli process arxiv_paper.pdf \
  --type latex_compiled \
  --theme math-document \
  --provider groq

# Output: outputs/arxiv_paper/index.html
```

### Example 2: Scanned Textbook

```bash
# Process scanned textbook with OCR
python -m src.cli process algebra_textbook.pdf \
  --type scanned \
  --theme lecture-notes

# Note: Slower due to OCR processing
```

### Example 3: Lecture Notes

```bash
# Process lecture notes
python -m src.cli process lecture_05.pdf \
  --type auto \
  --theme lecture-notes \
  --output ~/courses/math101/lecture_05

# Open result
open ~/courses/math101/lecture_05/index.html
```

### Example 4: Batch Processing Course Materials

```bash
#!/bin/bash
# Process all PDFs in a course directory

COURSE_DIR="~/courses/math101"
OUTPUT_DIR="~/courses/math101/html"

for pdf in "$COURSE_DIR"/*.pdf; do
    filename=$(basename "$pdf" .pdf)
    echo "Processing $filename..."

    python -m src.cli process "$pdf" \
        --theme lecture-notes \
        --output "$OUTPUT_DIR/$filename"
done

echo "All lectures processed!"
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## 📄 License

See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: https://github.com/your-repo/issues
- **Documentation**: https://your-docs-site.com
- **Email**: support@example.com
