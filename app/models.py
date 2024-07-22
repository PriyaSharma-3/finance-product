from sqlalchemy import (Column, Integer, String, Date,Float,LargeBinary)
from datetime import datetime

from app.database import Base

class Login(Base):
    __tablename__    = "login"
    id               = Column(Integer, primary_key=True, nullable=False)
    username         = Column(String, nullable=False)
    password         = Column(String, nullable=False)


class Finance(Base):
    __tablename__           = "finance"
    id                      = Column(Integer, primary_key=True, nullable=False)
    month                   = Column(String, nullable=False)
    transaction_id          = Column(String, nullable=True)
    value_date              = Column(String, nullable=True)
    transaction_date        = Column(String, nullable=True)
    transaction_posted_date = Column(String, nullable=True)
    cheque_no_ref_no        = Column(String, nullable=True)
    transaction_remarks     = Column(String, nullable=True)
    withdrawal_amt          = Column(Float, nullable=True)
    deposit_amt             = Column(Float, nullable=True)
    balance                 = Column(Float, nullable=True)
    expenses                = Column(String, nullable=True)
    invoices_pdf             = Column(LargeBinary, nullable=True)
    invoices_filename        = Column(String, nullable=True)  # Add filename column

    def __repr__(self):
        return f"<Finance(id={self.id}, month={self.month}, transaction_id={self.transaction_id}, deposit_amt={self.deposit_amt}, withdrawal_amt={self.withdrawal_amt})>"


class Expenses(Base):
    __tablename__    = "expenses"
    id               = Column(Integer, primary_key=True, nullable=False)
    expense          = Column(String, nullable=False)
    

class Calculation(Base):
    __tablename__       = "calculation"
    id                  = Column(Integer, primary_key=True, nullable=False)
    month               = Column(String, nullable=False)
    profit              = Column(String, nullable=False)
    tax                 = Column(String, nullable=False)
    cess                = Column(String, nullable=False)
    total_tax           = Column(String, nullable=False)
    profit_after_tax    = Column(String, nullable=False)
    
    
    
class Invoice(Base):
    __tablename__    = "invoice"
    id                   = Column(Integer, primary_key=True, nullable=False)
    month                = Column(String, nullable=False)
    invoice_pdf          = Column(LargeBinary, nullable=False)
    invoice_filename     = Column(String, nullable=False)  # Add filename column