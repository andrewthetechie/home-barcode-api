from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from barcode_api.schemas.dto.albums_dto import Album
from barcode_api.services import AlbumService


async def get_album_service(request: Request):
    return AlbumService(request.state.config, request.state.logger)


AlbumServiceDependency = Annotated[AlbumService, Depends(get_album_service)]

albums_router = APIRouter(prefix="/album", dependencies=[Depends(get_album_service)])


BarcodeQuery = Annotated[str, Query(title="The Barcode to search")]


@albums_router.get("/")
async def get_album_by_barcode(barcode: BarcodeQuery, album_service: AlbumServiceDependency) -> Album:
    spotify_id, album = await album_service.search(barcode=barcode)
    return Album(**album.model_dump(), spotify_id=spotify_id)
