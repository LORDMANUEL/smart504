from __future__ import annotations

import httpx
from fastapi import HTTPException, status

from app.config import Settings
from app.schemas import GoogleImageResult

_GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


async def search_google_images(
    *, query: str, settings: Settings, count: int = 8
) -> list[GoogleImageResult]:
    api_key = settings.google_cse_api_key.get_secret_value() if settings.google_cse_api_key else ""
    if not api_key or not settings.google_cse_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google image search is not configured; upload an image directly instead",
        )
    params = {
        "key": api_key,
        "cx": settings.google_cse_id,
        "q": query,
        "searchType": "image",
        "safe": "active",
        "num": min(max(count, 1), 10),
        "rights": "cc_publicdomain,cc_attribute,cc_sharealike,cc_noncommercial",
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(_GOOGLE_CSE_ENDPOINT, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Google image search failed") from exc

    results: list[GoogleImageResult] = []
    for item in payload.get("items", []):
        image = item.get("image") or {}
        link = item.get("link")
        context = image.get("contextLink")
        if not link or not context:
            continue
        results.append(
            GoogleImageResult(
                title=item.get("title") or "Image result",
                image_url=link,
                thumbnail_url=image.get("thumbnailLink"),
                source_page_url=context,
                display_link=item.get("displayLink"),
                width=image.get("width"),
                height=image.get("height"),
            )
        )
    return results
