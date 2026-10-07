from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class TextChunk:
    content: str
    index: int
    metadata: dict


class TextChunker:
    """Paragraph-aware word chunker with configurable overlap."""

    def __init__(self, chunk_size=None, overlap=None):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.overlap = settings.RAG_CHUNK_OVERLAP if overlap is None else overlap
        if self.chunk_size <= 0:
            raise ValueError('chunk_size debe ser mayor que cero.')
        if self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError('overlap debe ser menor que chunk_size y no negativo.')

    def split(self, text):
        paragraphs = [paragraph.strip() for paragraph in text.split('\n\n')
                      if paragraph.strip()]
        words = []
        paragraph_ends = set()
        for paragraph in paragraphs:
            words.extend(paragraph.split())
            paragraph_ends.add(len(words))
        if not words:
            return []

        chunks = []
        start = 0
        while start < len(words):
            target_end = min(start + self.chunk_size, len(words))
            semantic_ends = [end for end in paragraph_ends
                             if start < end <= target_end]
            end = max(semantic_ends) if semantic_ends else target_end
            content = ' '.join(words[start:end])
            chunks.append(TextChunk(
                content=content,
                index=len(chunks),
                metadata={'word_start': start, 'word_end': end},
            ))
            if end == len(words):
                break
            start = max(end - self.overlap, start + 1)
        return chunks
