from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class OperationType(str, Enum):
    ENTREE = "ENTREE"
    SORTIE = "SORTIE"

class UserRole(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN" # Implicitly Write + Config

class OperationCategory(str, Enum):
    LOYER = "LOYER"
    CHARGES = "CHARGES"
    TRAVAUX = "TRAVAUX"
    TAXES = "TAXES"
    ENTRETIEN = "ENTRETIEN"
    SYNDIC = "SYNDIC"
    ASSURANCE = "ASSURANCE"
    FRAIS_BANCAIRES = "FRAIS_BANCAIRES"
    REVERSEMENT = "REVERSEMENT"
    AUTRE = "AUTRE"

class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True)
    type: OperationType = Field(default=OperationType.SORTIE)
    is_reversement: bool = Field(default=False)
    description: Optional[str] = None

class Category(CategoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operations: List["Operation"] = Relationship(back_populates="category_ref")

class LotBase(SQLModel):
    name: str = Field(index=True)
    type: str = Field(default="Appartement")
    description: Optional[str] = None

class Lot(LotBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operations: List["Operation"] = Relationship(back_populates="lot")
    quote_parts: List["QuotePart"] = Relationship(back_populates="lot")

class OwnerBase(SQLModel):
    name: str = Field(index=True)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = Field(default=UserRole.READ)
    theme: str = Field(default="LIGHT")

class Owner(OwnerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: Optional[str] = None
    quote_parts: List["QuotePart"] = Relationship(back_populates="owner")
    allocations: List["Allocation"] = Relationship(back_populates="owner")

class BankAccountBase(SQLModel):
    name: str = Field(unique=True, index=True)
    iban: Optional[str] = None
    initial_balance: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)

class BankAccount(BankAccountBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operations: List["Operation"] = Relationship(back_populates="bank_account")

class QuotePart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lot_id: int = Field(foreign_key="lot.id")
    owner_id: int = Field(foreign_key="owner.id")
    numerator: int
    denominator: int
    start_date: date
    end_date: Optional[date] = None

    lot: Lot = Relationship(back_populates="quote_parts")
    owner: Owner = Relationship(back_populates="quote_parts")

class Operation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date
    lot_id: Optional[int] = Field(default=None, foreign_key="lot.id")
    bank_account_id: int = Field(foreign_key="bankaccount.id")
    type: OperationType
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    label: str
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)
    paid_by_owner_id: Optional[int] = Field(default=None, foreign_key="owner.id", description="If paid by owner (Note de frais)")
    proof_filename: Optional[str] = None

    lot: Lot = Relationship(back_populates="operations")
    bank_account: BankAccount = Relationship(back_populates="operations")
    category_ref: Optional[Category] = Relationship(back_populates="operations")
    allocations: List["Allocation"] = Relationship(back_populates="operation")

class Allocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operation_id: int = Field(foreign_key="operation.id")
    owner_id: int = Field(foreign_key="owner.id")
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=14, decimal_places=2)

    operation: Operation = Relationship(back_populates="allocations")
    owner: Owner = Relationship(back_populates="allocations")
