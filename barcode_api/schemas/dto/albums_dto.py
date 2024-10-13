from typing import Any

from pydantic import AnyUrl, BaseModel


class DiscogsAlbum(BaseModel):
    name: str
    artist: str
    year: str
    genres: list[str] | None
    url: AnyUrl | str | None = None
    cover_image: AnyUrl

    @classmethod
    def from_api_result(cls, discogs_api_result: dict[str, Any]):
        title_split = discogs_api_result["title"].split("-")

        return cls(
            name=title_split[1].lstrip(),
            artist=title_split[0].rstrip(),
            year=discogs_api_result["year"],
            genres=discogs_api_result["genre"],
            url=discogs_api_result["master_url"],
            cover_image=discogs_api_result["cover_image"],
        )


class Album(DiscogsAlbum):
    spotify_id: str
