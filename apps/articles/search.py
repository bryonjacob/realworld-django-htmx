"""Whoosh-backed text search index for articles.

Deliberately Django-light: imports `settings` for the index directory
and accepts an `Article` instance for indexing, but does not import
signals, views, or templates. Keep it that way — the index layer should
remain swappable.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from whoosh import index
from whoosh.fields import NUMERIC, TEXT, Schema
from whoosh.qparser import MultifieldParser, OrGroup

if TYPE_CHECKING:
    from articles.models import Article


_SCHEMA = Schema(
    id=NUMERIC(stored=True, unique=True),
    title=TEXT(field_boost=3.0, stored=False),
    summary=TEXT(field_boost=2.0, stored=False),
    content=TEXT(stored=False),
)


def _index_dir() -> Path:
    return Path(settings.SEARCH_INDEX_DIR)


def get_index() -> index.Index:
    """Open the index, creating it (and the directory) on first call."""
    path = _index_dir()
    path.mkdir(parents=True, exist_ok=True)
    if not index.exists_in(str(path)):
        return index.create_in(str(path), _SCHEMA)
    return index.open_dir(str(path))


def index_article(article: Article) -> None:
    """Add or replace the indexed document for ``article``."""
    ix = get_index()
    writer = ix.writer()
    writer.update_document(
        id=article.pk,
        title=article.title,
        summary=article.summary,
        content=article.content,
    )
    writer.commit()


def deindex_article(article_id: int) -> None:
    """Remove the indexed document for ``article_id``. No-op if absent."""
    ix = get_index()
    writer = ix.writer()
    writer.delete_by_term("id", article_id)
    writer.commit()


def query_ids(q: str, limit: int = 200) -> list[int]:
    """Return Article PKs ranked by relevance to ``q``. Empty list if blank."""
    q = q.strip()
    if not q:
        return []
    ix = get_index()
    parser = MultifieldParser(["title", "summary", "content"], schema=_SCHEMA, group=OrGroup)
    parsed = parser.parse(q)
    with ix.searcher() as searcher:
        results = searcher.search(parsed, limit=limit)
        return [int(hit["id"]) for hit in results]


def reindex_all() -> None:
    """Drop and rebuild the entire index from the Article table."""
    # Local import — avoids app-loading order issues at module import time.
    from articles.models import Article

    path = _index_dir()
    path.mkdir(parents=True, exist_ok=True)
    ix = index.create_in(str(path), _SCHEMA)
    writer = ix.writer()
    for article in Article.objects.all().iterator():
        writer.update_document(
            id=article.pk,
            title=article.title,
            summary=article.summary,
            content=article.content,
        )
    writer.commit()
