from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from barcode_api.core.dependencies.database import DBSessionDep
from barcode_api.schemas.dto.albums_dto import Album as AlbumDTO
from barcode_api.schemas.dto.errors_dto import ErrorResponse
from barcode_api.services import AlbumService


# async for being used as an async dependency
async def get_album_service(request: Request, db_session: DBSessionDep):  # noqa: RUF029
    return AlbumService(config=request.state.config, logger=request.state.logger, db_session=db_session)


AlbumServiceDependency = Annotated[AlbumService, Depends(get_album_service)]

albums_router = APIRouter(prefix="/album", dependencies=[Depends(get_album_service)])


BarcodeQuery = Annotated[str, Query(title="The Barcode to search")]


@albums_router.get("/search", responses={"404": {"model": ErrorResponse}})
async def get_album_by_barcode(barcode: BarcodeQuery, album_service: AlbumServiceDependency) -> AlbumDTO:
    try:
        album = await album_service.search(barcode=barcode)
    except AlbumService.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AlbumDTO.model_validate(album)
