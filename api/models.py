from sqlalchemy import (
    Column, Integer, String, Numeric, Date,
    DateTime, ForeignKey, UniqueConstraint, Text, func,
)
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "categories"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), unique=True, nullable=False)
    color      = Column(String(7), nullable=False, default="#00c795")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    references = relationship("ReferenceCatalog", back_populates="category")


class Statement(Base):
    __tablename__ = "statements"
    __table_args__ = (UniqueConstraint("year", "month"),)

    id             = Column(Integer, primary_key=True)
    account_name   = Column(String(255))
    year           = Column(Integer, nullable=False)
    month          = Column(Integer, nullable=False)
    fecha_estado   = Column(String(20))
    saldo_apertura = Column(Numeric(15, 2))
    saldo_cierre   = Column(Numeric(15, 2))
    saldo_promedio = Column(Numeric(15, 2))
    filename       = Column(String(255))
    uploaded_at    = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship(
        "Transaction", back_populates="statement", cascade="all, delete-orphan"
    )


class ReferenceCatalog(Base):
    __tablename__ = "references_catalog"

    id          = Column(Integer, primary_key=True)
    descripcion = Column(String(255), unique=True, nullable=False)
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    category     = relationship("Category", back_populates="references")
    transactions = relationship("Transaction", back_populates="reference")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("statement_id", "position", name="uq_transaction_stmt_pos"),)

    id             = Column(Integer, primary_key=True)
    statement_id   = Column(Integer, ForeignKey("statements.id", ondelete="CASCADE"), nullable=False)
    position       = Column(Integer, nullable=False)   # índice 0-based en el archivo fuente
    fecha          = Column(String(10), nullable=False)
    fecha_completa = Column(Date)
    tipo           = Column(String(100))
    descripcion    = Column(String(255))
    reference_id   = Column(
        Integer, ForeignKey("references_catalog.id", ondelete="SET NULL"), nullable=True
    )
    debito         = Column(Numeric(15, 2))
    credito        = Column(Numeric(15, 2))
    saldo          = Column(Numeric(15, 2))
    nota           = Column(Text, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    statement = relationship("Statement", back_populates="transactions")
    reference = relationship("ReferenceCatalog", back_populates="transactions")
