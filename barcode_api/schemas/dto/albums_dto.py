from typing import Any

from pydantic import AnyUrl, BaseModel, ConfigDict


class DiscogsAlbum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    artist: str
    year: str
    genres: list[str] | None
    discogs_url: AnyUrl | str | None = None
    cover_image_url: AnyUrl | None = None

    @classmethod
    def from_api_result(cls, discogs_api_result: dict[str, Any]):
        title_split = discogs_api_result["title"].split("-")

        return cls(
            name=title_split[1].lstrip(),
            artist=title_split[0].rstrip(),
            year=discogs_api_result["year"],
            genres=discogs_api_result["genre"],
            url=discogs_api_result["master_url"],
            cover_image_url=discogs_api_result["cover_image"],
        )


class Album(DiscogsAlbum):
    spotify_id: str

    @classmethod
    def model_validate(cls, this_obj) -> "DiscogsAlbum":
        if isinstance(this_obj.genres, str):
            this_obj.genres = this_obj.genres.split(",")
        return super().model_validate(this_obj)
