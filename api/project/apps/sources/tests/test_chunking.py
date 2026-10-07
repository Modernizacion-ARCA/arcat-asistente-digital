from sources.chunking import TextChunker


def test_chunker_prioriza_limites_de_parrafo_y_conserva_overlap():
    text = 'uno dos tres cuatro\n\ncinco seis siete ocho\n\nnueve diez once doce'

    chunks = TextChunker(chunk_size=8, overlap=2).split(text)

    assert [chunk.content for chunk in chunks] == [
        'uno dos tres cuatro cinco seis siete ocho',
        'siete ocho nueve diez once doce',
    ]
    assert chunks[0].metadata == {'word_start': 0, 'word_end': 8}
    assert chunks[1].index == 1
