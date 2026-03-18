"""Settings API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_unit_of_work
from app.api.schemas import SettingsResponse, UpdateSettingsRequest
from app.domain.exceptions import InvalidCurrencyError
from app.service_layer.services import get_settings, update_settings
from app.service_layer.unit_of_work import AbstractUnitOfWork

router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/settings", response_model=SettingsResponse)
def get_settings_endpoint(uow: UoWDep):
    settings = get_settings(uow)
    return SettingsResponse(primary_currency=settings.primary_currency)


@router.patch("/settings", response_model=SettingsResponse)
def update_settings_endpoint(body: UpdateSettingsRequest, uow: UoWDep):
    try:
        settings = update_settings(uow, primary_currency=body.primary_currency)
    except InvalidCurrencyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return SettingsResponse(primary_currency=settings.primary_currency)
