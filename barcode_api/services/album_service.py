from functools import cached_property
from logging import Logger
from typing import Annotated, Any

from async_property import async_property
from httpx import AsyncClient
from pydantic import StringConstraints

from barcode_api.core.config import Config
from barcode_api.schemas.dto.albums_dto import DiscogsAlbum
from barcode_api.services._base import BarcodeServiceBase

SpotifyAlbumID = Annotated[str, StringConstraints(strip_whitespace=True, max_length=22, min_length=22)]


class AlbumService(BarcodeServiceBase):
    def __init__(self, config: Config, logger: Logger) -> None:
        super().__init__(config, logger)
        self.spotify_service = SpotifyLookupService(config, logger)
        self.discogs_service = DiscogsLookupService(config, logger)

    async def search(self, barcode: str) -> tuple[SpotifyAlbumID, DiscogsAlbum]:
        discogs_albums = await self.discogs_service.search(barcode=barcode)
        spotify_id = await self.spotify_service.get_album_id(discogs_albums[0].artist, discogs_albums[0].name)

        return spotify_id, discogs_albums[0]


class HttpxService(BarcodeServiceBase):
    def __init__(self, config: Config, logger: Logger, httpx_client_config: dict[str, Any] | None = None) -> None:
        super().__init__(config, logger)
        self.httpx_client_config = httpx_client_config if httpx_client_config is not None else dict()

    def _get_httpx_client(self):
        return AsyncClient(**self.httpx_client_config)


class DiscogsLookupService(HttpxService):
    DISCOGS_SEARCH_URL = "https://api.discogs.com/database/search"

    @cached_property
    def headers(self):
        return {"Authorization": f"Discogs token={self._config.discogs_token}"}

    async def search(self, barcode: str) -> list[DiscogsAlbum]:
        this_search_url = f"{self.DISCOGS_SEARCH_URL}?barcode={barcode}"
        async with self._get_httpx_client() as client:
            response = await client.get(this_search_url, headers=self.headers)
        data = response.json()
        albums = data["results"]
        return [DiscogsAlbum.from_api_result(discog_result) for discog_result in albums]


class SpotifyLookupService(HttpxService):
    SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self, config: Config, logger: Logger, httpx_client_config: dict[str, Any] | None = None) -> None:
        super().__init__(config, logger, httpx_client_config)
        self.__token: str | None = None

    @async_property
    async def token(self):
        if self.__token is None:
            self.__token = await self.get_spotify_token(
                self._config.spotify_client_id, self._config.spotify_client_secret
            )
        return self.__token

    async def get_spotify_token(self, client_id, client_secret):
        # Function to get Spotify access token
        headers = {}
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with self._get_httpx_client() as client:
            response = await client.post(self.SPOTIFY_AUTH_URL, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception("Failed to get Spotify token")

    async def get_album_id(self, artist_name, album_name):
        # Function to search for the album by artist and album name

        headers = {
            "Authorization": f"Bearer {await self.token}",
        }
        params = {
            "q": f"album:{album_name} artist:{artist_name}",
            "type": "album",
            "limit": 1,  # We just want the first match
        }
        async with self._get_httpx_client() as client:
            response = await client.get(self.SPOTIFY_SEARCH_URL, headers=headers, params=params)

        if response.status_code == 200:
            albums = response.json().get("albums", {}).get("items", [])
            if albums:
                album_id = albums[0]["id"]
                return album_id
            else:
                return None  # No album found
        else:
            raise Exception(f"Spotify API request failed with status code {response.status_code}")
