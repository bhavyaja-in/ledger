"""
Test database models with currency support
"""
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.models.database import create_models_with_prefix


class TestDatabaseCurrency:
    """Test currency support in database models"""

    @pytest.fixture
    def db_setup(self):
        """Set up test database with currency models"""
        engine = create_engine("sqlite:///:memory:")
        models, base = create_models_with_prefix("test_")

        # Create tables
        base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        yield {"engine": engine, "models": models, "session": session}

        session.close()

    # =====================
    # TRANSACTION MODEL TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_currency_field_exists(self, db_setup):
        """Test transaction model has currency field"""
        Transaction = db_setup["models"]["Transaction"]

        # Check currency column exists
        assert hasattr(Transaction, "currency")

        # Check column properties
        currency_column = Transaction.__table__.columns["currency"]
        assert currency_column.nullable is False
        assert str(currency_column.default.arg) == "INR"
        assert currency_column.type.length == 3

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_currency_default_inr(self, db_setup):
        """Test transaction currency defaults to INR"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test institution
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        # Create test processed file
        processed_file = ProcessedFile(
            file_name="test.xlsx",
            file_path="/test/test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        # Create transaction without currency (should default to INR)
        transaction = Transaction(
            transaction_hash="test_hash_001",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="Test transaction",
            debit_amount=1000.0,
            transaction_type="debit",
        )
        session.add(transaction)
        session.commit()

        # Verify currency defaults to INR
        assert transaction.currency == "INR"

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_currency_explicit_value(self, db_setup):
        """Test transaction with explicit currency value"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test institution
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        # Create test processed file
        processed_file = ProcessedFile(
            file_name="test.xlsx",
            file_path="/test/test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        # Create transaction with explicit USD currency
        transaction = Transaction(
            transaction_hash="test_hash_002",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="USD transaction",
            debit_amount=100.0,
            transaction_type="debit",
            currency="USD",
        )
        session.add(transaction)
        session.commit()

        # Verify explicit currency is saved
        assert transaction.currency == "USD"

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_currency_multiple_currencies(self, db_setup):
        """Test multiple transactions with different currencies"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test institution
        institution = Institution(name="Multi Currency Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        # Create test processed file
        processed_file = ProcessedFile(
            file_name="multi_currency.xlsx",
            file_path="/test/multi_currency.xlsx",
            institution_id=institution.id,
            processor_type="multi_currency",
            file_size=2000,
        )
        session.add(processed_file)
        session.flush()

        # Create transactions with different currencies
        currencies_data = [
            ("USD", 100.0),
            ("EUR", 85.0),
            ("GBP", 75.0),
            ("INR", 8500.0),
            ("JPY", 15000.0),
        ]

        transactions = []
        for i, (currency, amount) in enumerate(currencies_data, 1):
            transaction = Transaction(
                transaction_hash=f"multi_currency_{i:03d}",
                institution_id=institution.id,
                processed_file_id=processed_file.id,
                transaction_date=datetime(2024, 1, 15),
                description=f"Transaction in {currency}",
                credit_amount=amount,
                transaction_type="credit",
                currency=currency,
            )
            transactions.append(transaction)
            session.add(transaction)

        session.commit()

        # Verify all currencies are saved correctly
        for transaction, (expected_currency, _) in zip(transactions, currencies_data):
            assert transaction.currency == expected_currency

    # =====================
    # TRANSACTION SPLIT MODEL TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_split_currency_field_exists(self, db_setup):
        """Test transaction split model has currency field"""
        TransactionSplit = db_setup["models"]["TransactionSplit"]

        # Check currency column exists
        assert hasattr(TransactionSplit, "currency")

        # Check column properties
        currency_column = TransactionSplit.__table__.columns["currency"]
        assert currency_column.nullable is False
        assert str(currency_column.default.arg) == "INR"
        assert currency_column.type.length == 3

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_split_currency_default_inr(self, db_setup):
        """Test transaction split currency defaults to INR"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        TransactionSplit = models["TransactionSplit"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test data
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        processed_file = ProcessedFile(
            file_name="test.xlsx",
            file_path="/test/test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        transaction = Transaction(
            transaction_hash="split_test_001",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="Split transaction",
            debit_amount=1000.0,
            transaction_type="debit",
            currency="INR",
        )
        session.add(transaction)
        session.flush()

        # Create split without currency (should default to INR)
        split = TransactionSplit(
            transaction_id=transaction.id, person_name="alice", percentage=50.0, amount=500.0
        )
        session.add(split)
        session.commit()

        # Verify currency defaults to INR
        assert split.currency == "INR"

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_split_currency_explicit_value(self, db_setup):
        """Test transaction split with explicit currency value"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        TransactionSplit = models["TransactionSplit"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test data
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        processed_file = ProcessedFile(
            file_name="test.xlsx",
            file_path="/test/test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        transaction = Transaction(
            transaction_hash="split_test_002",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="USD split transaction",
            debit_amount=100.0,
            transaction_type="debit",
            currency="USD",
        )
        session.add(transaction)
        session.flush()

        # Create split with explicit USD currency
        split = TransactionSplit(
            transaction_id=transaction.id,
            person_name="bob",
            percentage=30.0,
            amount=30.0,
            currency="USD",
        )
        session.add(split)
        session.commit()

        # Verify explicit currency is saved
        assert split.currency == "USD"

    @pytest.mark.unit
    @pytest.mark.database
    def test_transaction_split_currency_consistency(self, db_setup):
        """Test transaction and split currency consistency"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        TransactionSplit = models["TransactionSplit"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test data
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        processed_file = ProcessedFile(
            file_name="test.xlsx",
            file_path="/test/test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        # Create EUR transaction
        transaction = Transaction(
            transaction_hash="consistency_test_001",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="EUR split transaction",
            debit_amount=100.0,
            transaction_type="debit",
            currency="EUR",
        )
        session.add(transaction)
        session.flush()

        # Create multiple splits with same currency as transaction
        splits_data = [("alice", 40.0, 40.0), ("bob", 35.0, 35.0), ("charlie", 25.0, 25.0)]

        splits = []
        for person, percentage, amount in splits_data:
            split = TransactionSplit(
                transaction_id=transaction.id,
                person_name=person,
                percentage=percentage,
                amount=amount,
                currency="EUR",  # Same as transaction
            )
            splits.append(split)
            session.add(split)

        session.commit()

        # Verify all splits have same currency as transaction
        for split in splits:
            assert split.currency == transaction.currency == "EUR"

    # =====================
    # QUERY TESTS
    # =====================

    @pytest.mark.unit
    @pytest.mark.database
    def test_query_transactions_by_currency(self, db_setup):
        """Test querying transactions by currency"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test data
        institution = Institution(name="Multi Currency Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        processed_file = ProcessedFile(
            file_name="query_test.xlsx",
            file_path="/test/query_test.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        # Create transactions with different currencies
        currencies = ["USD", "EUR", "INR", "USD", "EUR"]
        transactions = []

        for i, currency in enumerate(currencies, 1):
            transaction = Transaction(
                transaction_hash=f"query_test_{i:03d}",
                institution_id=institution.id,
                processed_file_id=processed_file.id,
                transaction_date=datetime(2024, 1, 15),
                description=f"Transaction {i}",
                credit_amount=100.0,
                transaction_type="credit",
                currency=currency,
            )
            transactions.append(transaction)
            session.add(transaction)

        session.commit()

        # Query transactions by currency
        usd_transactions = session.query(Transaction).filter(Transaction.currency == "USD").all()
        eur_transactions = session.query(Transaction).filter(Transaction.currency == "EUR").all()
        inr_transactions = session.query(Transaction).filter(Transaction.currency == "INR").all()

        # Verify query results
        assert len(usd_transactions) == 2
        assert len(eur_transactions) == 2
        assert len(inr_transactions) == 1

        # Verify currencies
        for tx in usd_transactions:
            assert tx.currency == "USD"
        for tx in eur_transactions:
            assert tx.currency == "EUR"
        for tx in inr_transactions:
            assert tx.currency == "INR"

    @pytest.mark.unit
    @pytest.mark.database
    def test_query_splits_by_currency(self, db_setup):
        """Test querying transaction splits by currency"""
        models = db_setup["models"]
        session = db_setup["session"]

        Transaction = models["Transaction"]
        TransactionSplit = models["TransactionSplit"]
        Institution = models["Institution"]
        ProcessedFile = models["ProcessedFile"]

        # Create test data
        institution = Institution(name="Test Bank", institution_type="bank")
        session.add(institution)
        session.flush()

        processed_file = ProcessedFile(
            file_name="splits_query.xlsx",
            file_path="/test/splits_query.xlsx",
            institution_id=institution.id,
            processor_type="test",
            file_size=1000,
        )
        session.add(processed_file)
        session.flush()

        # Create transactions
        transaction1 = Transaction(
            transaction_hash="splits_query_001",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="USD transaction",
            debit_amount=100.0,
            transaction_type="debit",
            currency="USD",
        )

        transaction2 = Transaction(
            transaction_hash="splits_query_002",
            institution_id=institution.id,
            processed_file_id=processed_file.id,
            transaction_date=datetime(2024, 1, 15),
            description="EUR transaction",
            debit_amount=100.0,
            transaction_type="debit",
            currency="EUR",
        )

        session.add(transaction1)
        session.add(transaction2)
        session.flush()

        # Create splits with different currencies
        splits_data = [
            (transaction1.id, "alice", "USD"),
            (transaction1.id, "bob", "USD"),
            (transaction2.id, "charlie", "EUR"),
            (transaction2.id, "dave", "EUR"),
        ]

        for tx_id, person, currency in splits_data:
            split = TransactionSplit(
                transaction_id=tx_id,
                person_name=person,
                percentage=50.0,
                amount=50.0,
                currency=currency,
            )
            session.add(split)

        session.commit()

        # Query splits by currency
        usd_splits = (
            session.query(TransactionSplit).filter(TransactionSplit.currency == "USD").all()
        )
        eur_splits = (
            session.query(TransactionSplit).filter(TransactionSplit.currency == "EUR").all()
        )

        # Verify query results
        assert len(usd_splits) == 2
        assert len(eur_splits) == 2

        # Verify currencies and persons
        usd_persons = [split.person_name for split in usd_splits]
        eur_persons = [split.person_name for split in eur_splits]

        assert set(usd_persons) == {"alice", "bob"}
        assert set(eur_persons) == {"charlie", "dave"}
