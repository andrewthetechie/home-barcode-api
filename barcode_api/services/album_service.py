import re
from functools import cached_property
from http import HTTPStatus
from logging import Logger
from typing import Annotated, Any

from async_property import async_property
from httpx import AsyncClient
from pydantic import StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession

from barcode_api.core.config import Config
from barcode_api.core.errors import BarcodeAPIBaseException
from barcode_api.models.albums import Album
from barcode_api.schemas.dto.albums_dto import DiscogsAlbum
from barcode_api.services._base import BarcodeServiceBase

SpotifyAlbumID = Annotated[str, StringConstraints(strip_whitespace=True, max_length=22, min_length=22)]

# Strips out any (##) from the artist
DISCOGS_ARTIST_CLEANUP_REGEX = re.compile(r"\(\d+\)")


class AlbumService(BarcodeServiceBase):
    class NotFoundError(BarcodeAPIBaseException):
        pass

    class NoSpotifyFoundError(NotFoundError):
        ERROR_TEXT = "No spotify album found for %s - %s"
        pass

    class NoDiscogsAlbumFoundError(NotFoundError):
        ERROR_TEXT = "No Discogs album found for barcode %s"
        pass

    MODEL = Album

    def __init__(self, config: Config, logger: Logger, db_session: AsyncSession) -> None:
        super().__init__(config, logger, db_session)
        self.spotify_service = SpotifyLookupService(config, logger)
        self.discogs_service = DiscogsLookupService(config, logger)

    async def _lookup_album(self, barcode: str) -> Album | None:
        discogs_albums = await self.discogs_service.search(barcode=barcode)
        if len(discogs_albums) == 0:
            raise self.__class__.NoDiscogsAlbumFoundError(self.__class__.NoDiscogsAlbumFoundError.ERROR_TEXT % barcode)
        cleaned_artist = DISCOGS_ARTIST_CLEANUP_REGEX.sub("", discogs_albums[0].artist).strip()
        spotify_id = await self.spotify_service.get_album_id(cleaned_artist, discogs_albums[0].name)
        if spotify_id is None:
            raise self.__class__.NoSpotifyFoundError(
                self.__class__.NoSpotifyFoundError.ERROR_TEXT % (cleaned_artist, discogs_albums[0].name)
            )
        url = None if discogs_albums[0].discogs_url is None else str(discogs_albums[0].discogs_url)
        cover_url = None if discogs_albums[0].cover_image_url is None else str(discogs_albums[0].cover_image_url)
        album = Album(
            barcode=barcode,
            artist=cleaned_artist,
            name=discogs_albums[0].name,
            year=discogs_albums[0].year,
            genres=",".join(discogs_albums[0].genres),
            spotify_id=spotify_id,
            discogs_url=url,
            cover_image_url=cover_url,
        )
        return album

    async def search(self, barcode: str) -> tuple[SpotifyAlbumID, DiscogsAlbum]:
        album = await self._get_fom_cache(value=barcode)
        if album is None:
            album = await self._lookup_album(barcode)
            await self._add_to_cache(album)

        return album


class HttpxService:
    def __init__(self, config: Config, logger: Logger, httpx_client_config: dict[str, Any] | None = None) -> None:
        self._config: Config = config
        self._logger: Logger = logger
        self.httpx_client_config = httpx_client_config if httpx_client_config is not None else dict()

    def _get_httpx_client(self):
        return AsyncClient(**self.httpx_client_config)


class DiscogsLookupService(HttpxService):
    DISCOGS_SEARCH_URL = "https://api.discogs.com/database/search"

    @cached_property
    def headers(self):
        return {
            "Authorization": f"Discogs token={self._config.discogs_token}",
            "User-Agent": "HomeBarcodeAPI/0.1 +https://github.com/andrewthetechie/home-barcode-api",
        }

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
        if response.status_code == HTTPStatus.OK:
            return response.json()["access_token"]
        else:
            self._logger.error("Error getting spotify token %s %s", response.status_code, response.json())
            exception_msg = "Failed to get Spotify token"
            raise Exception(exception_msg)

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

        if response.status_code == HTTPStatus.OK:
            albums = response.json().get("albums", {}).get("items", [])
            if albums:
                album_id = albums[0]["id"]
                return album_id
            else:
                return None  # No album found
        else:
            self._logger.error("Error getting album ID %s %s", response.status_code, response.json())
            err_msg = f"Spotify API request failed with status code {response.status_code}"
            raise Exception(err_msg)
