from typing import Optional

from sqlalchemy.orm import Session

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.domain.entity.account import Account
from app.domains.account.infrastructure.mapper.account_mapper import AccountMapper
from app.domains.account.infrastructure.orm.account_orm import AccountORM


class AccountRepositoryImpl(AccountRepositoryPort):

    def __init__(self, db: Session):
        self._db = db

    def find_by_id(self, account_id: int) -> Optional[Account]:
        orm = self._db.query(AccountORM).filter(AccountORM.id == account_id).first()
        if orm is None:
            return None
        return AccountMapper.to_entity(orm)

    def find_by_email(self, email: str) -> Optional[Account]:
        orm = self._db.query(AccountORM).filter(AccountORM.email == email).first()
        if orm is None:
            return None
        return AccountMapper.to_entity(orm)

    def find_by_kakao_id(self, kakao_id: str) -> Optional[Account]:
        orm = self._db.query(AccountORM).filter(AccountORM.kakao_id == kakao_id).first()
        if orm is None:
            return None
        return AccountMapper.to_entity(orm)

    def save(self, account: Account) -> Account:
        orm = AccountMapper.to_orm(account)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return AccountMapper.to_entity(orm)

    def update(self, account: Account) -> Account:
        orm = self._db.query(AccountORM).filter(AccountORM.id == account.id).first()
        if orm is None:
            raise ValueError("계정을 찾을 수 없습니다.")
        orm.email = account.email
        orm.kakao_id = account.kakao_id
        orm.nickname = account.nickname
        self._db.commit()
        self._db.refresh(orm)
        return AccountMapper.to_entity(orm)
