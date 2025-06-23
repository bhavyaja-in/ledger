"""
Database models and manager with test mode support
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

def create_models_with_prefix(prefix=""):
    """Create model classes with optional table name prefix"""
    
    # Create a new base for each prefix to avoid conflicts
    Base = declarative_base()
    
    # Create unique class names to avoid SQLAlchemy warnings
    class_suffix = prefix.replace('_', '').title() if prefix else 'Prod'
    
    # Dynamic class creation with unique names
    Institution = type(f'Institution{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}institutions',
        'id': Column(Integer, primary_key=True),
        'name': Column(String(100), nullable=False),
        'institution_type': Column(String(50), nullable=False),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    })

    ProcessedFile = type(f'ProcessedFile{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}processed_files',
        'id': Column(Integer, primary_key=True),
        'institution_id': Column(Integer, ForeignKey(f'{prefix}institutions.id'), nullable=False),
        'file_path': Column(String(500), nullable=False),
        'file_name': Column(String(200), nullable=False),
        'file_size': Column(Integer),
        'processor_type': Column(String(50), nullable=False),
        'processing_status': Column(String(20), default='processing'),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        'institution': relationship(Institution)
    })

    TransactionEnum = type(f'TransactionEnum{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}transaction_enums',
        'id': Column(Integer, primary_key=True),
        'enum_name': Column(String(100), nullable=False, unique=True),
        'patterns': Column(JSON, nullable=False),
        'category': Column(String(50), nullable=False),
        'processor_type': Column(String(50), nullable=False),
        'is_active': Column(Boolean, default=True),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    })

    TransactionSplit = type(f'TransactionSplit{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}transaction_splits',
        'id': Column(Integer, primary_key=True),
        'transaction_id': Column(Integer, ForeignKey(f'{prefix}transactions.id'), nullable=False),
        'person_name': Column(String(100), nullable=False),
        'percentage': Column(Float, nullable=False),
        'amount': Column(Float, nullable=False),
        'is_settled': Column(Boolean, default=False),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    })

    Transaction = type(f'Transaction{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}transactions',
        'id': Column(Integer, primary_key=True),
        'transaction_hash': Column(String(64), nullable=False, unique=True),
        'institution_id': Column(Integer, ForeignKey(f'{prefix}institutions.id'), nullable=False),
        'processed_file_id': Column(Integer, ForeignKey(f'{prefix}processed_files.id'), nullable=False),
        'transaction_date': Column(DateTime, nullable=False),
        'description': Column(Text, nullable=False),
        'debit_amount': Column(Float),
        'credit_amount': Column(Float),
        'balance': Column(Float),
        'reference_number': Column(String(100)),
        'transaction_type': Column(String(10), nullable=False),
        'enum_id': Column(Integer, ForeignKey(f'{prefix}transaction_enums.id')),
        'category': Column(String(50)),
        'reason': Column(Text),
        'splits': Column(JSON),
        'has_splits': Column(Boolean, default=False),
        'is_settled': Column(Boolean, default=False),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        'institution': relationship(Institution),
        'processed_file': relationship(ProcessedFile),
        'enum': relationship(TransactionEnum),
        'transaction_splits': relationship(TransactionSplit, back_populates="transaction")
    })

    # Add back reference to TransactionSplit
    TransactionSplit.transaction = relationship(Transaction, back_populates="transaction_splits")

    SkippedTransaction = type(f'SkippedTransaction{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}skipped_transactions',
        'id': Column(Integer, primary_key=True),
        'transaction_hash': Column(String(64), nullable=False, unique=True),
        'institution_id': Column(Integer, ForeignKey(f'{prefix}institutions.id'), nullable=False),
        'processed_file_id': Column(Integer, ForeignKey(f'{prefix}processed_files.id'), nullable=False),
        'raw_data': Column(JSON, nullable=False),
        'row_number': Column(Integer),
        'skip_reason': Column(Text, nullable=False),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        'institution': relationship(Institution),
        'processed_file': relationship(ProcessedFile)
    })

    ProcessingLog = type(f'ProcessingLog{class_suffix}', (Base,), {
        '__tablename__': f'{prefix}processing_logs',
        'id': Column(Integer, primary_key=True),
        'processed_file_id': Column(Integer, ForeignKey(f'{prefix}processed_files.id'), nullable=False),
        'total_transactions': Column(Integer, default=0),
        'processed_transactions': Column(Integer, default=0),
        'skipped_transactions': Column(Integer, default=0),
        'duplicate_transactions': Column(Integer, default=0),
        'duplicate_skipped': Column(Integer, default=0),
        'processing_time': Column(Float),
        'created_at': Column(DateTime, default=datetime.utcnow),
        'processed_file': relationship(ProcessedFile)
    })

    return {
        'Institution': Institution,
        'ProcessedFile': ProcessedFile,
        'TransactionEnum': TransactionEnum,
        'Transaction': Transaction,
        'TransactionSplit': TransactionSplit,
        'SkippedTransaction': SkippedTransaction,
        'ProcessingLog': ProcessingLog
    }, Base

class DatabaseManager:
    """Database manager with test mode support"""
    
    def __init__(self, config, test_mode=False):
        self.config = config
        self.test_mode = test_mode
        self.test_prefix = config.get('database', {}).get('test_prefix', 'test_')
        
        # Create engine
        db_url = config['database']['url']
        self.engine = create_engine(db_url)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Create models with appropriate prefix
        prefix = self.test_prefix if test_mode else ""
        self.models, self.base = create_models_with_prefix(prefix)
        
        # Create tables
        self.base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.Session()
    
    def get_model(self, model_name):
        """Get model class by name"""
        return self.models.get(model_name) 