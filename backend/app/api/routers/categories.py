from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.domain.exceptions import DuplicateCategoryNameError
from app.domain.exceptions import CategoryNotFoundError
from app.domain.exceptions import CategoryInUseError
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.api.dependencies import get_unit_of_work
from app.api.schemas import CategoryResponse
from app.api.schemas import CategoryCreate
from app.api.schemas import CategoryUpdate
from app.service_layer.services import create_category
from app.service_layer.services import list_categories
from app.service_layer.services import update_category_name
from app.service_layer.services import delete_category


router = APIRouter()
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_unit_of_work)]


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories_endpoint(
    uow: UoWDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return list_categories(uow, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category_endpoint(category_id: str, uow: UoWDep):
    category = uow.repo.get_category(category_id)
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Category with id '{category_id}' not found",
        )
    return category


@router.post("/categories", status_code=201, response_model=CategoryResponse)
def create_category_endpoint(category: CategoryCreate, uow: UoWDep):
    try:
        new_category = create_category(uow=uow, name=category.name)
    except DuplicateCategoryNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return new_category


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category_endpoint(
    category_id: str, category_update: CategoryUpdate, uow: UoWDep
):
    try:
        updated_category = update_category_name(
            uow=uow,
            category_id=category_id,
            new_name=category_update.name,
        )
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DuplicateCategoryNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return updated_category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category_endpoint(category_id: str, uow: UoWDep):
    try:
        delete_category(uow=uow, category_id=category_id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except CategoryInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return None
