"""
Chapter Agent - Task 1: Extract chapters from PDF.

Uses PDF Tools to divide PDF into logical chapters.
"""

import json
from typing import List, Optional

from src.agents.base_agent import BaseAgent
from src.models.chapter import Chapter, ChapterCollection
from src.models.enums import AgentTask
from src.models.state import AgentState
from src.tools.pdf_tools import PDFExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChapterAgent(BaseAgent):
    """
    Chapter Agent - extracts chapters from PDF.

    Uses PDF Tools to:
    - Extract text from PDF
    - Detect table of contents
    - Identify chapter headings
    - Analyze document structure
    - Divide PDF into logical chapters
    """

    def __init__(self, llm_provider: str = "groq", model: Optional[str] = None):
        """
        Initialize Chapter Agent.

        Args:
            llm_provider: LLM provider (groq, anthropic, openai)
            model: Model name (if None, uses config default)
        """
        super().__init__(
            task=AgentTask.TASK_1_CHAPTER,
            llm_provider=llm_provider,
            model=model,
        )

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute chapter extraction.

        Args:
            state: Current workflow state

        Returns:
            Updated state with chapter_collection populated
        """
        logger.info(f"Extracting chapters from: {state.pdf_path}")

        with PDFExtractor(state.pdf_path) as extractor:
            # Step 1: Analyze PDF structure
            structure = extractor.analyze_structure()
            total_pages = extractor.get_page_count()

            logger.info(f"PDF has {total_pages} pages")
            logger.info(f"Structure: {structure}")

            # Step 2: Try to detect TOC
            toc = extractor.detect_toc()

            if toc:
                logger.info(f"Found TOC with {len(toc)} entries")
                chapters = self._extract_from_toc(extractor, toc, total_pages)

            else:
                logger.info("No TOC found, using heading detection")

                # Step 3: Detect headings
                headings = extractor.detect_headings()

                if headings:
                    logger.info(f"Detected {len(headings)} potential headings")
                    chapters = self._extract_from_headings(
                        extractor, headings, total_pages
                    )

                else:
                    logger.info("No headings detected, using LLM-based extraction")
                    # Step 4: Fallback to LLM-based extraction
                    chapters = self._extract_with_llm(
                        extractor, structure, total_pages
                    )

            # Final fallback: if no chapters extracted, divide equally
            if not chapters or len(chapters) == 0:
                logger.warning("All extraction methods produced no chapters, using equal division fallback")
                chapters = self._fallback_equal_division(extractor, total_pages)

            # Create chapter collection
            chapter_collection = ChapterCollection(
                chapters=chapters,
                total_pages=total_pages,
                pdf_path=state.pdf_path,
            )

            # Update state
            state.chapter_collection = chapter_collection

            logger.info(
                f"Extracted {len(chapters)} chapters, "
                f"covering {chapter_collection.get_coverage_percentage():.1f}% of document"
            )

        return state

    def _extract_from_toc(
        self, extractor: PDFExtractor, toc: List[dict], total_pages: int
    ) -> List[Chapter]:
        """
        Extract chapters from TOC.

        Args:
            extractor: PDF extractor
            toc: TOC entries
            total_pages: Total pages in PDF

        Returns:
            List of chapters
        """
        chapters = []

        # Filter for top-level entries (level 1)
        top_level_entries = [entry for entry in toc if entry["level"] == 1]

        for i, entry in enumerate(top_level_entries):
            start_page = entry["page"]

            # Determine end page (before next chapter or end of document)
            if i < len(top_level_entries) - 1:
                end_page = top_level_entries[i + 1]["page"] - 1
            else:
                end_page = total_pages

            # Extract text for this chapter
            content = extractor.extract_text((start_page, end_page))

            chapter = Chapter(
                id=f"ch{i + 1}",
                title=entry["title"],
                pages=list(range(start_page, end_page + 1)),
                content_raw=content,
                level=0,
            )

            chapter.update_metadata()
            chapters.append(chapter)

        return chapters

    def _extract_from_headings(
        self, extractor: PDFExtractor, headings: List[dict], total_pages: int
    ) -> List[Chapter]:
        """
        Extract chapters from detected headings.

        Args:
            extractor: PDF extractor
            headings: Detected headings
            total_pages: Total pages in PDF

        Returns:
            List of chapters
        """
        # Use LLM to identify which headings are chapter-level
        chapters = self._identify_chapters_from_headings(headings)

        # Extract text for each chapter
        result_chapters = []

        for i, chapter_data in enumerate(chapters):
            start_page = chapter_data["start_page"]

            # Determine end page
            if i < len(chapters) - 1:
                end_page = chapters[i + 1]["start_page"] - 1
            else:
                end_page = total_pages

            # Extract text
            content = extractor.extract_text((start_page, end_page))

            chapter = Chapter(
                id=f"ch{i + 1}",
                title=chapter_data["title"],
                pages=list(range(start_page, end_page + 1)),
                content_raw=content,
                level=0,
            )

            chapter.update_metadata()
            result_chapters.append(chapter)

        return result_chapters

    def _identify_chapters_from_headings(
        self, headings: List[dict]
    ) -> List[dict]:
        """
        Use LLM to identify which headings are chapter-level.

        Args:
            headings: List of detected headings

        Returns:
            List of chapter data dicts
        """
        # Prepare headings for LLM
        headings_text = "\n".join(
            [
                f"Page {h['page']}: {h['title']}"
                for h in headings[:20]  # Limit to first 20
            ]
        )

        system_prompt = """You are an expert at analyzing document structure.
Your task is to identify which headings represent main chapters (not sections or subsections).

Look for:
- Numbered chapters (Chapter 1, Capitolo 1, etc.)
- Clear chapter titles
- Top-level divisions

Return a JSON array of chapter objects with: title and start_page."""

        prompt = f"""Given these headings from a document, identify the main chapters:

{headings_text}

Return ONLY a JSON array, no other text."""

        try:
            response = self.call_llm(prompt, system_prompt=system_prompt)

            # Parse JSON response
            # Clean response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            chapters = json.loads(response)

            logger.info(f"LLM identified {len(chapters)} chapters")
            return chapters

        except Exception as e:
            logger.warning(f"LLM chapter identification failed: {e}")

            # Fallback: use simple heuristic
            # Treat all headings as potential chapters
            if headings and len(headings) > 0:
                return [
                    {"title": h["title"], "start_page": h["page"]} for h in headings[:10]
                ]
            else:
                logger.warning("No headings available for fallback, returning empty list")
                return []

    def _extract_with_llm(
        self, extractor: PDFExtractor, structure: dict, total_pages: int
    ) -> List[Chapter]:
        """
        Extract chapters using LLM analysis of document content.

        Args:
            extractor: PDF extractor
            structure: Document structure analysis
            total_pages: Total pages in PDF

        Returns:
            List of chapters
        """
        logger.info("Using LLM to extract chapters from content")

        # Sample pages throughout document for LLM analysis
        sample_pages = min(10, total_pages)
        step = max(1, total_pages // sample_pages)

        sample_content = []
        for page_num in range(1, total_pages + 1, step):
            page_text = extractor.extract_page(page_num)
            # Take first 500 chars of each page
            sample_content.append(f"Page {page_num}:\n{page_text[:500]}")

        content_sample = "\n\n".join(sample_content[:10])

        system_prompt = """You are an expert at analyzing document structure.
Your task is to divide a document into logical chapters based on content samples.

Return a JSON array of chapter objects with:
- title: chapter title
- start_page: starting page number
- estimated_pages: estimated number of pages in chapter"""

        prompt = f"""This document has {total_pages} pages. Based on these content samples,
identify logical chapters:

{content_sample}

Return ONLY a JSON array of chapters, no other text."""

        try:
            response = self.call_llm(prompt, system_prompt=system_prompt)

            # Parse JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()

            chapter_data = json.loads(response)

            # Create chapters
            chapters = []
            for i, data in enumerate(chapter_data):
                start_page = data.get("start_page", 1)
                estimated_pages = data.get("estimated_pages", total_pages // len(chapter_data))

                end_page = min(start_page + estimated_pages - 1, total_pages)

                # Adjust if overlapping with next chapter
                if i < len(chapter_data) - 1:
                    next_start = chapter_data[i + 1].get("start_page", end_page + 1)
                    end_page = min(end_page, next_start - 1)

                content = extractor.extract_text((start_page, end_page))

                chapter = Chapter(
                    id=f"ch{i + 1}",
                    title=data.get("title", f"Chapter {i + 1}"),
                    pages=list(range(start_page, end_page + 1)),
                    content_raw=content,
                    level=0,
                )

                chapter.update_metadata()
                chapters.append(chapter)

            return chapters

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")

            # Ultimate fallback: divide into equal parts
            logger.warning("Falling back to equal division")
            return self._fallback_equal_division(extractor, total_pages)

    def _fallback_equal_division(
        self, extractor: PDFExtractor, total_pages: int, num_chapters: int = 5
    ) -> List[Chapter]:
        """
        Fallback: divide document into equal chapters.

        Args:
            extractor: PDF extractor
            total_pages: Total pages
            num_chapters: Number of chapters to create

        Returns:
            List of chapters
        """
        # Adjust num_chapters if PDF is too small
        num_chapters = min(num_chapters, total_pages)

        if num_chapters == 0:
            # Edge case: empty PDF
            logger.error("Cannot create chapters from empty PDF")
            return []

        logger.warning(f"Dividing document into {num_chapters} equal chapters")

        pages_per_chapter = total_pages // num_chapters
        remaining_pages = total_pages % num_chapters

        chapters = []
        current_page = 1

        for i in range(num_chapters):
            start_page = current_page

            # Distribute remaining pages across first chapters
            pages_in_this_chapter = pages_per_chapter + (1 if i < remaining_pages else 0)
            end_page = start_page + pages_in_this_chapter - 1

            # Ensure at least 1 page per chapter
            if start_page > total_pages:
                break

            end_page = min(end_page, total_pages)

            content = extractor.extract_text((start_page, end_page))

            chapter = Chapter(
                id=f"ch{i + 1}",
                title=f"Section {i + 1}",
                pages=list(range(start_page, end_page + 1)),
                content_raw=content,
                level=0,
            )

            chapter.update_metadata()
            chapters.append(chapter)

            current_page = end_page + 1

        return chapters
