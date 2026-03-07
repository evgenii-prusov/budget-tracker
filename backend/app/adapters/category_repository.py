from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.domain.model import Category
from app.adapters.orm import categories, postings
from app.service_layer.abstract_category_repository import AbstractCategoryRepository


class SqlAlchemyCategoryRepository(AbstractCategoryRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, category: Category) -> None:
        self.session.add(category)

    def get(self, category_id: str) -> Category | None:
        return (
            self.session.execute(select(Category).filter_by(category_id=category_id))
            .scalars()
            .one_or_none()
        )

    def get_by_name(self, name: str) -> Category | None:
        return self.session.execute(select(Category).filter_by(name=name)).scalars().first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Category]:
        return list(
            self.session.execute(
                select(Category)
                .order_by(categories.c.name, categories.c.category_id)
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

    def delete(self, category: Category) -> None:
        self.session.delete(category)

    def count_postings(self, category_id: str) -> int:
        return self.session.execute(
            select(func.count(postings.c.posting_id)).where(postings.c.category_id == category_id)
        ).scalar_one()
