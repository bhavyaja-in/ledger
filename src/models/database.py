"""
Database models and manager with test mode support
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


def create_models_with_prefix(prefix=""):
    """Create model classes with optional table name prefix"""

    # Create a new base for each prefix to avoid conflicts
    Base = declarative_base()

    # Create unique class names to avoid SQLAlchemy warnings
    class_suffix = prefix.replace("_", "").title() if prefix else "Prod"

    # Dynamic class creation with unique names
    Institution = type(
        f"Institution{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}institutions",
            "id": Column(Integer, primary_key=True),
            "name": Column(String(100), nullable=False),
            "institution_type": Column(String(50), nullable=False),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        },
    )

    ProcessedFile = type(
        f"ProcessedFile{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}processed_files",
            "id": Column(Integer, primary_key=True),
            "institution_id": Column(
                Integer, ForeignKey(f"{prefix}institutions.id"), nullable=False
            ),
            "file_path": Column(String(500), nullable=False),
            "file_name": Column(String(200), nullable=False),
            "file_size": Column(Integer),
            "processor_type": Column(String(50), nullable=False),
            "processing_status": Column(String(20), default="processing"),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            "institution": relationship(Institution),
        },
    )

    TransactionEnum = type(
        f"TransactionEnum{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}transaction_enums",
            "id": Column(Integer, primary_key=True),
            "enum_name": Column(String(100), nullable=False, unique=True),
            "patterns": Column(JSON, nullable=False),
            "category": Column(String(50), nullable=False),
            "processor_type": Column(String(50), nullable=False),
            "is_active": Column(Boolean, default=True),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        },
    )

    TransactionSplit = type(
        f"TransactionSplit{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}transaction_splits",
            "id": Column(Integer, primary_key=True),
            "transaction_id": Column(
                Integer, ForeignKey(f"{prefix}transactions.id"), nullable=False
            ),
            "person_name": Column(String(100), nullable=False),
            "percentage": Column(Float, nullable=False),
            "amount": Column(Float, nullable=False),
            "currency": Column(String(3), nullable=False, default="INR"),
            "is_settled": Column(Boolean, default=False),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        },
    )

    Transaction = type(
        f"Transaction{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}transactions",
            "id": Column(Integer, primary_key=True),
            "transaction_hash": Column(String(64), nullable=False, unique=True),
            "institution_id": Column(
                Integer, ForeignKey(f"{prefix}institutions.id"), nullable=False
            ),
            "processed_file_id": Column(
                Integer, ForeignKey(f"{prefix}processed_files.id"), nullable=False
            ),
            "transaction_date": Column(DateTime, nullable=False),
            "description": Column(Text, nullable=False),
            "debit_amount": Column(Float),
            "credit_amount": Column(Float),
            "balance": Column(Float),
            "reference_number": Column(String(100)),
            "transaction_type": Column(String(10), nullable=False),
            "currency": Column(String(3), nullable=False, default="INR"),
            "enum_id": Column(Integer, ForeignKey(f"{prefix}transaction_enums.id")),
            "category": Column(String(50)),
            "transaction_category": Column(String(50)),
            "reason": Column(Text),
            "splits": Column(JSON),
            "has_splits": Column(Boolean, default=False),
            "is_settled": Column(Boolean, default=False),
            "status": Column(Enum('pending', 'processed', 'skipped', name='transaction_status'), default='pending', nullable=False),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            "institution": relationship(Institution),
            "processed_file": relationship(ProcessedFile),
            "enum": relationship(TransactionEnum),
            "transaction_splits": relationship(TransactionSplit, back_populates="transaction"),
        },
    )

    # Add back reference to TransactionSplit
    TransactionSplit.transaction = relationship(Transaction, back_populates="transaction_splits")

    SkippedTransaction = type(
        f"SkippedTransaction{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}skipped_transactions",
            "id": Column(Integer, primary_key=True),
            "transaction_hash": Column(String(64), nullable=False, unique=True),
            "institution_id": Column(
                Integer, ForeignKey(f"{prefix}institutions.id"), nullable=False
            ),
            "processed_file_id": Column(
                Integer, ForeignKey(f"{prefix}processed_files.id"), nullable=False
            ),
            "raw_data": Column(JSON, nullable=False),
            "row_number": Column(Integer),
            "skip_reason": Column(Text, nullable=False),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            "institution": relationship(Institution),
            "processed_file": relationship(ProcessedFile),
        },
    )

    ProcessingLog = type(
        f"ProcessingLog{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}processing_logs",
            "id": Column(Integer, primary_key=True),
            "processed_file_id": Column(
                Integer, ForeignKey(f"{prefix}processed_files.id"), nullable=False
            ),
            "total_transactions": Column(Integer, default=0),
            "processed_transactions": Column(Integer, default=0),
            "skipped_transactions": Column(Integer, default=0),
            "duplicate_transactions": Column(Integer, default=0),
            "duplicate_skipped": Column(Integer, default=0),
            "processing_time": Column(Float),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "processed_file": relationship(ProcessedFile),
        },
    )

    User = type(
        f"User{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}users",
            "id": Column(Integer, primary_key=True),
            "username": Column(String(100), nullable=False, unique=True),
            "password_hash": Column(String(255), nullable=False),
            "roles": Column(String(255), nullable=False, default="reviewer"),  # comma-separated roles
            "is_active": Column(Boolean, default=True),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "updated_at": Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        },
    )

    RefreshToken = type(
        f"RefreshToken{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}refresh_tokens",
            "id": Column(Integer, primary_key=True),
            "user_id": Column(Integer, ForeignKey(f"{prefix}users.id"), nullable=False),
            "token_hash": Column(String(255), nullable=False, unique=True),
            "expires_at": Column(DateTime, nullable=False),
            "is_revoked": Column(Boolean, default=False),
            "created_at": Column(DateTime, default=datetime.utcnow),
            "user": relationship(User),
        },
    )

    AuditLog = type(
        f"AuditLog{class_suffix}",
        (Base,),
        {
            "__tablename__": f"{prefix}audit_logs",
            "id": Column(Integer, primary_key=True),
            "transaction_id": Column(Integer, ForeignKey(f"{prefix}transactions.id"), nullable=False),
            "user_id": Column(Integer, ForeignKey(f"{prefix}users.id")),
            "action": Column(String(50), nullable=False),  # classify, skip, reprocess, revert
            "from_status": Column(String(20)),
            "to_status": Column(String(20)),
            "data": Column(JSON),  # Store the changes made
            "created_at": Column(DateTime, default=datetime.utcnow),
            "transaction": relationship(Transaction),
            "user": relationship(User),
        },
    )

    return {
        "Institution": Institution,
        "ProcessedFile": ProcessedFile,
        "TransactionEnum": TransactionEnum,
        "Transaction": Transaction,
        "TransactionSplit": TransactionSplit,
        "SkippedTransaction": SkippedTransaction,
        "ProcessingLog": ProcessingLog,
        "User": User,
        "RefreshToken": RefreshToken,
        "AuditLog": AuditLog,
    }, Base


class DatabaseManager:  # pylint: disable=unused-variable
    """Database manager with test mode support"""

    def __init__(self, config, test_mode=False):
        self.config = config
        self.test_mode = test_mode
        self.test_prefix = config.get("database", {}).get("test_prefix", "test_")

        # Create engine
        db_url = config["database"]["url"]
        self.engine = create_engine(db_url)

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Create models with appropriate prefix
        prefix = self.test_prefix if test_mode else ""
        self.models, self.base = create_models_with_prefix(prefix)

        # Handle schema migration for test mode
        if test_mode:
            self._ensure_test_schema_updated()
        else:
            # For production, ensure schema is updated without dropping tables
            self._ensure_production_schema_updated()

    def __str__(self):
        """String representation that sanitizes sensitive information"""
        return f"DatabaseManager(test_mode={self.test_mode}, test_prefix='{self.test_prefix}')"

    def __repr__(self):
        """Representation that sanitizes sensitive information"""
        return self.__str__()

    @property
    def __dict__(self):
        """Return sanitized dict representation that hides sensitive information"""
        # Create a copy of the actual __dict__ but sanitize sensitive data
        safe_dict = {
            "test_mode": self.test_mode,
            "test_prefix": self.test_prefix,
            "engine": self.engine,
            "Session": self.Session,
            "models": self.models,
            "base": self.base,
        }

        # Add sanitized config (without sensitive connection strings)
        if hasattr(self, "config"):
            safe_config = self.config.copy()
            if "database" in safe_config and "url" in safe_config["database"]:
                # Sanitize database URL to hide passwords and sensitive info
                db_url = safe_config["database"]["url"]
                if "?" in db_url:
                    # Remove query parameters (passwords, etc.)
                    safe_config["database"]["url"] = db_url.split("?", maxsplit=1)[0] + "?***"
                elif "@" in db_url and "://" in db_url:
                    # Hide credentials in connection string
                    parts = db_url.split("@")
                    if len(parts) > 1:
                        protocol_parts = parts[0].split("://")
                        if len(protocol_parts) > 1:
                            safe_config["database"]["url"] = f"{protocol_parts[0]}://***@{parts[1]}"

            safe_dict["config"] = safe_config

        return safe_dict

    def get_session(self):
        """Get database session"""
        return self.Session()

    def get_model(self, model_name):
        """Get model class by name"""
        return self.models.get(model_name)

    def _ensure_test_schema_updated(self):
        """Ensure test database schema is up to date by dropping and recreating tables"""
        try:
            # Check if currency column exists in transactions table
            with self.engine.connect() as conn:
                self._check_and_update_schema(conn)
        except (OSError, IOError, ImportError, Exception):  # pylint: disable=W0718
            # If we can't check, just create tables (first time setup)
            self.base.metadata.create_all(self.engine)

    def _check_and_update_schema(self, conn):
        """Check schema and update if needed"""
        test_table_name = f"{self.test_prefix}transactions"

        try:
            # First check if the table exists
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": test_table_name},
            )
            table_exists = result.fetchone() is not None

            if table_exists:
                self._update_existing_schema(conn, test_table_name)
            else:
                # Table doesn't exist, create all tables
                print("🔄 Creating test database schema...")
                self.base.metadata.create_all(self.engine)
                print("✅ Test database schema created")
        except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
            # Error checking table existence, just create tables
            print("🔄 Creating test database schema...")
            self.base.metadata.create_all(self.engine)
            print("✅ Test database schema created")

    def _update_existing_schema(self, conn, test_table_name):
        """Update existing schema if needed"""
        try:
            # Check for both currency and status columns
            # nosec B608 - This is a schema query with controlled table name
            conn.execute(text(f"SELECT currency FROM {test_table_name} LIMIT 1"))  # nosec B608
            # Check for status column
            try:
                conn.execute(text(f"SELECT status FROM {test_table_name} LIMIT 1"))  # nosec B608
                # Both columns exist, just create any missing tables
                self.base.metadata.create_all(self.engine)
            except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
                # Status column doesn't exist, add it
                print("🔄 Adding status column to transactions...")
                conn.execute(text(f"ALTER TABLE {test_table_name} ADD COLUMN status VARCHAR(20) DEFAULT 'processed'"))  # nosec B608
                conn.commit()
                # Create any missing tables (User, RefreshToken, AuditLog)
                self.base.metadata.create_all(self.engine)
                print("✅ Database schema updated with status column")
        except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
            # Currency column doesn't exist, drop and recreate test tables
            print("🔄 Updating test database schema...")
            self.base.metadata.drop_all(self.engine)
            self.base.metadata.create_all(self.engine)
    def _ensure_production_schema_updated(self):
        """Ensure production database schema is up to date without dropping tables"""
        try:
            # Check if status column exists in transactions table
            with self.engine.connect() as conn:
                self._check_and_update_production_schema(conn)
        except (OSError, IOError, ImportError, Exception):  # pylint: disable=W0718
            # If we can't check, just create tables (first time setup)
            self.base.metadata.create_all(self.engine)

    def _check_and_update_production_schema(self, conn):
        """Check production schema and update if needed"""
        table_name = "transactions"

        try:
            # First check if the table exists
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": table_name},
            )
            table_exists = result.fetchone() is not None

            if table_exists:
                self._update_production_schema(conn, table_name)
            else:
                # Table doesn't exist, create all tables
                print("🔄 Creating production database schema...")
                self.base.metadata.create_all(self.engine)
                print("✅ Production database schema created")
        except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
            # Error checking table existence, just create tables
            print("🔄 Creating production database schema...")
            self.base.metadata.create_all(self.engine)
            print("✅ Production database schema created")

    def _update_production_schema(self, conn, table_name):
        """Update production schema if needed"""
        try:
            # Check for status column
            try:
                conn.execute(text(f"SELECT status FROM {table_name} LIMIT 1"))  # nosec B608
                # Status column exists, just create any missing tables
                self.base.metadata.create_all(self.engine)
            except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
                # Status column doesn't exist, add it with appropriate default
                print("🔄 Adding status column to production transactions...")
                # For existing transactions, set status to 'processed' since they went through CLI
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN status VARCHAR(20) DEFAULT 'processed'"))  # nosec B608
                conn.commit()
                # Create any missing tables (User, RefreshToken, AuditLog)
                self.base.metadata.create_all(self.engine)
                print("✅ Production database schema updated with status column")
        except (AttributeError, TypeError, OSError, Exception):  # pylint: disable=W0718
            # Error checking column, just create missing tables
            self.base.metadata.create_all(self.engine)
