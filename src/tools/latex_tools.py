"""
LaTeX processing tools for Classifier Agent (Task 2).

Provides tools for extracting formulas, detecting theorems, definitions,
and splitting content into logical blocks.
"""

import re
from typing import Dict, List, Optional, Tuple

from src.models.enums import BlockAction, BlockType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LaTeXProcessor:
    """
    LaTeX and mathematical content processing tools.

    Handles detection and extraction of mathematical structures
    like theorems, definitions, formulas, and proofs.
    """

    # Theorem-like environments patterns
    THEOREM_PATTERNS = [
        r"(?:Theorem|Teorema|Lemma|Corollary|Corollario|Proposition|Proposizione)\s*\d*[:\.]?\s*(.+?)(?:\n|$)",
        r"^Thm\.?\s*\d+[:\.]?\s*(.+?)(?:\n|$)",
    ]

    # Definition patterns
    DEFINITION_PATTERNS = [
        r"(?:Definition|Definizione|Def\.)\s*\d*[:\.]?\s*(.+?)(?:\n|$)",
        r"^We define\s+(.+?)(?:\n|$)",
        r"^Si definisce\s+(.+?)(?:\n|$)",
    ]

    # Proof patterns
    PROOF_PATTERNS = [
        r"^Proof[:\.]?\s*(.+)",
        r"^Dimostrazione[:\.]?\s*(.+)",
        r"^Dim\.\s*(.+)",
    ]

    # Example patterns
    EXAMPLE_PATTERNS = [
        r"^Example\s*\d*[:\.]?\s*(.+)",
        r"^Esempio\s*\d*[:\.]?\s*(.+)",
    ]

    # Remark patterns
    REMARK_PATTERNS = [
        r"^(?:Remark|Nota|Note|Observation|Osservazione)\s*\d*[:\.]?\s*(.+)",
    ]

    # Formula patterns (inline and display)
    FORMULA_PATTERNS = [
        r"\$\$(.+?)\$\$",  # Display math $$...$$
        r"\\\[(.+?)\\\]",  # Display math \[...\]
        r"\$(.+?)\$",  # Inline math $...$
        r"\\begin\{equation\}(.+?)\\end\{equation\}",  # equation environment
        r"\\begin\{align\*?\}(.+?)\\end\{align\*?\}",  # align environment
    ]

    def __init__(self):
        """Initialize LaTeX processor."""
        logger.debug("LaTeX processor initialized")

    def extract_formula(
        self, text: str, confidence_threshold: float = 0.5
    ) -> List[Dict[str, any]]:
        """
        Extract LaTeX formulas from text.

        Args:
            text: Input text containing formulas
            confidence_threshold: Minimum confidence for extraction

        Returns:
            List of extracted formulas with metadata

        Example:
            >>> processor = LaTeXProcessor()
            >>> formulas = processor.extract_formula("The formula $x^2 + y^2 = r^2$ is...")
            >>> for f in formulas:
            ...     print(f"Formula: {f['latex']}")
        """
        formulas = []

        for pattern in self.FORMULA_PATTERNS:
            matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)

            for match in matches:
                latex = match.group(1).strip()

                # Skip very short matches (likely false positives)
                if len(latex) < 2:
                    continue

                # Calculate simple confidence based on LaTeX-like content
                confidence = self._calculate_formula_confidence(latex)

                if confidence >= confidence_threshold:
                    formulas.append({
                        "latex": latex,
                        "raw_match": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": confidence,
                        "pattern": pattern,
                    })

        # Remove duplicates (same formula matched by different patterns)
        unique_formulas = []
        seen_latex = set()

        for formula in formulas:
            if formula["latex"] not in seen_latex:
                unique_formulas.append(formula)
                seen_latex.add(formula["latex"])

        logger.debug(f"Extracted {len(unique_formulas)} formulas from text")
        return unique_formulas

    def _calculate_formula_confidence(self, latex: str) -> float:
        """
        Calculate confidence score for extracted formula.

        Args:
            latex: LaTeX string

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence

        # Boost confidence for LaTeX commands
        latex_commands = [
            r"\\frac", r"\\sum", r"\\int", r"\\prod", r"\\sqrt",
            r"\\alpha", r"\\beta", r"\\gamma", r"\\delta",
            r"\\cdot", r"\\times", r"\\partial", r"\\nabla",
            r"\\in", r"\\subset", r"\\cup", r"\\cap",
            r"\\mathbb", r"\\mathcal", r"\\mathrm",
        ]

        for cmd in latex_commands:
            if cmd in latex:
                confidence += 0.05

        # Boost for mathematical operators
        math_operators = ["^", "_", "=", "+", "-", r"\leq", r"\geq"]
        for op in math_operators:
            if op in latex:
                confidence += 0.02

        # Cap at 1.0
        return min(1.0, confidence)

    def detect_theorem_blocks(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Detect theorem-like blocks (theorem, lemma, corollary, proposition).

        Args:
            text: Input text

        Returns:
            List of detected theorem blocks

        Example:
            >>> theorems = processor.detect_theorem_blocks(text)
            >>> for thm in theorems:
            ...     print(f"Theorem: {thm['name']}")
        """
        return self._detect_blocks(text, self.THEOREM_PATTERNS, BlockType.THEOREM)

    def detect_definitions(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Detect definition blocks.

        Args:
            text: Input text

        Returns:
            List of detected definitions
        """
        return self._detect_blocks(text, self.DEFINITION_PATTERNS, BlockType.DEFINITION)

    def detect_proofs(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Detect proof blocks.

        Args:
            text: Input text

        Returns:
            List of detected proofs
        """
        return self._detect_blocks(text, self.PROOF_PATTERNS, BlockType.PROOF)

    def detect_examples(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Detect example blocks.

        Args:
            text: Input text

        Returns:
            List of detected examples
        """
        return self._detect_blocks(text, self.EXAMPLE_PATTERNS, BlockType.EXAMPLE)

    def detect_remarks(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Detect remark/note blocks.

        Args:
            text: Input text

        Returns:
            List of detected remarks
        """
        return self._detect_blocks(text, self.REMARK_PATTERNS, BlockType.REMARK)

    def _detect_blocks(
        self, text: str, patterns: List[str], block_type: BlockType
    ) -> List[Dict[str, any]]:
        """
        Generic block detection using patterns.

        Args:
            text: Input text
            patterns: List of regex patterns
            block_type: Type of block to detect

        Returns:
            List of detected blocks
        """
        blocks = []

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                # Extract name/title if captured
                name = match.group(1).strip() if match.groups() else None

                # Extract full content (heuristic: until next heading or double newline)
                start_pos = match.start()
                remaining_text = text[start_pos:]

                # Find end of block (next heading pattern or double newline)
                end_match = re.search(r"\n\n|\n(?=[A-Z][a-z]+:)", remaining_text)
                if end_match:
                    content = remaining_text[: end_match.start()]
                else:
                    # Take next 500 chars as content
                    content = remaining_text[:500]

                blocks.append({
                    "type": block_type,
                    "name": name,
                    "content": content.strip(),
                    "start": start_pos,
                    "pattern": pattern,
                    "confidence": 0.85,  # High confidence for explicit markers
                })

        logger.debug(f"Detected {len(blocks)} {block_type.value} blocks")
        return blocks

    def split_into_blocks(
        self, text: str, min_block_size: int = 100
    ) -> List[Dict[str, any]]:
        """
        Split text into logical blocks.

        Attempts to identify all types of blocks (theorems, definitions,
        formulas, narrative text) and segment accordingly.

        Args:
            text: Input text
            min_block_size: Minimum size for a narrative block (characters)

        Returns:
            List of classified blocks

        Example:
            >>> blocks = processor.split_into_blocks(chapter_text)
            >>> for block in blocks:
            ...     print(f"{block['type']}: {block['content'][:50]}...")
        """
        blocks = []

        # Detect all structured blocks
        theorems = self.detect_theorem_blocks(text)
        definitions = self.detect_definitions(text)
        proofs = self.detect_proofs(text)
        examples = self.detect_examples(text)
        remarks = self.detect_remarks(text)
        formulas = self.extract_formula(text)

        # Combine all structured blocks
        structured_blocks = (
            theorems + definitions + proofs + examples + remarks
        )

        # Sort by position
        structured_blocks.sort(key=lambda b: b["start"])

        # Add formula blocks
        for formula in formulas:
            blocks.append({
                "type": BlockType.FORMULA,
                "content": formula["raw_match"],
                "latex": formula["latex"],
                "confidence": formula["confidence"],
                "action": BlockAction.LATEX,
            })

        # Add structured blocks
        for block in structured_blocks:
            action = (
                BlockAction.VERBATIM
                if block["type"] in {BlockType.THEOREM, BlockType.DEFINITION}
                else BlockAction.SUMMARIZE
            )

            blocks.append({
                "type": block["type"],
                "content": block["content"],
                "name": block.get("name"),
                "confidence": block.get("confidence", 0.8),
                "action": action,
            })

        # Fill gaps with narrative blocks
        if structured_blocks:
            # Track positions covered by structured blocks
            covered_positions = []
            for block in structured_blocks:
                start = block["start"]
                end = start + len(block["content"])
                covered_positions.append((start, end))

            # Find uncovered text (narrative)
            covered_positions.sort()
            last_end = 0

            for start, end in covered_positions:
                if start > last_end + min_block_size:
                    # Narrative block between structured blocks
                    narrative_text = text[last_end:start].strip()
                    if len(narrative_text) >= min_block_size:
                        blocks.append({
                            "type": BlockType.NARRATIVE,
                            "content": narrative_text,
                            "confidence": 0.7,
                            "action": BlockAction.SUMMARIZE,
                        })
                last_end = end

            # Final narrative block
            if last_end < len(text) - min_block_size:
                narrative_text = text[last_end:].strip()
                if len(narrative_text) >= min_block_size:
                    blocks.append({
                        "type": BlockType.NARRATIVE,
                        "content": narrative_text,
                        "confidence": 0.7,
                        "action": BlockAction.SUMMARIZE,
                    })

        else:
            # No structured blocks found - all narrative
            blocks.append({
                "type": BlockType.NARRATIVE,
                "content": text.strip(),
                "confidence": 0.6,
                "action": BlockAction.SUMMARIZE,
            })

        logger.info(f"Split text into {len(blocks)} blocks")
        return blocks

    def clean_latex(self, latex: str) -> str:
        """
        Clean and normalize LaTeX string.

        Args:
            latex: Raw LaTeX string

        Returns:
            Cleaned LaTeX
        """
        # Remove extra whitespace
        latex = re.sub(r"\s+", " ", latex)

        # Remove comments
        latex = re.sub(r"%.*$", "", latex, flags=re.MULTILINE)

        # Normalize spacing around operators
        latex = re.sub(r"\s*=\s*", " = ", latex)
        latex = re.sub(r"\s*\+\s*", " + ", latex)
        latex = re.sub(r"\s*-\s*", " - ", latex)

        return latex.strip()

    def extract_unicode_math(self, text: str) -> List[str]:
        """
        Extract mathematical expressions using Unicode symbols.

        Detects formulas written with Unicode math symbols (∑, ∫, ², etc.)

        Args:
            text: Input text

        Returns:
            List of Unicode math expressions
        """
        # Unicode math symbols
        math_symbols = r"[∑∏∫∂∇√±×÷≤≥≠≈∞αβγδεζηθλμπρσφψω₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹]"

        # Find expressions containing math symbols
        pattern = rf"\b[\w\s]*{math_symbols}[\w\s{math_symbols}]*\b"
        matches = re.findall(pattern, text)

        logger.debug(f"Found {len(matches)} Unicode math expressions")
        return [m.strip() for m in matches if m.strip()]


# Convenience functions
def extract_formulas_from_text(text: str) -> List[Dict[str, any]]:
    """
    Extract formulas from text (convenience function).

    Args:
        text: Input text

    Returns:
        List of formulas
    """
    processor = LaTeXProcessor()
    return processor.extract_formula(text)


def split_text_into_blocks(text: str) -> List[Dict[str, any]]:
    """
    Split text into blocks (convenience function).

    Args:
        text: Input text

    Returns:
        List of blocks
    """
    processor = LaTeXProcessor()
    return processor.split_into_blocks(text)
