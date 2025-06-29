"""
Database Loader - Handles create and update operations
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

class DatabaseLoader:
    """Database loader for create and update operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models = db_manager.models
    
    def get_or_create_institution(self, name: str, institution_type: str):
        """Get existing institution or create new one"""
        session = self.db_manager.get_session()
        try:
            Institution = self.models['Institution']
            
            # Try to find existing
            institution = session.query(Institution).filter_by(
                name=name,
                institution_type=institution_type
            ).first()
            
            if not institution:
                # Create new
                institution = Institution(
                    name=name,
                    institution_type=institution_type
                )
                session.add(institution)
                session.commit()
                session.refresh(institution)
            
            # Return detached instance
            institution_data = {
                'id': institution.id,
                'name': institution.name,
                'institution_type': institution.institution_type
            }
            
            session.expunge(institution)
            return institution
            
        finally:
            session.close()
    
    def create_processed_file(self, institution_id: int, file_path: str, 
                            file_name: str, file_size: int, processor_type: str):
        """Create processed file record"""
        session = self.db_manager.get_session()
        try:
            ProcessedFile = self.models['ProcessedFile']
            
            processed_file = ProcessedFile(
                institution_id=institution_id,
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                processor_type=processor_type,
                processing_status='processing'
            )
            
            session.add(processed_file)
            session.commit()
            session.refresh(processed_file)
            
            # Return detached instance
            session.expunge(processed_file)
            return processed_file
            
        finally:
            session.close()
    
    def update_processed_file_status(self, processed_file_id: int, status: str):
        """Update processed file status"""
        session = self.db_manager.get_session()
        try:
            ProcessedFile = self.models['ProcessedFile']
            
            processed_file = session.query(ProcessedFile).filter_by(id=processed_file_id).first()
            if processed_file:
                processed_file.processing_status = status
                processed_file.updated_at = datetime.utcnow()
                session.commit()
            
        finally:
            session.close()
    
    def create_or_update_enum(self, enum_name: str, patterns: list, category: str, processor_type: str):
        """Create new enum or update existing one"""
        session = self.db_manager.get_session()
        try:
            TransactionEnum = self.models['TransactionEnum']
            
            # Try to find existing
            enum_obj = session.query(TransactionEnum).filter_by(
                enum_name=enum_name,
                processor_type=processor_type
            ).first()
            
            if enum_obj:
                # Update existing
                enum_obj.patterns = patterns
                enum_obj.category = category
                enum_obj.updated_at = datetime.utcnow()
            else:
                # Create new
                enum_obj = TransactionEnum(
                    enum_name=enum_name,
                    patterns=patterns,
                    category=category,
                    processor_type=processor_type
                )
                session.add(enum_obj)
            
            session.commit()
            session.refresh(enum_obj)
            
            # Return detached instance
            session.expunge(enum_obj)
            return enum_obj
            
        finally:
            session.close()
    
    def create_transaction(self, transaction_data: Dict[str, Any]):
        """Create new transaction with optional splits"""
        session = self.db_manager.get_session()
        try:
            Transaction = self.models['Transaction']
            
            # Determine if transaction has splits
            splits_data = transaction_data.get('splits')
            has_splits = bool(splits_data)
            
            transaction = Transaction(
                transaction_hash=transaction_data['transaction_hash'],
                institution_id=transaction_data['institution_id'],
                processed_file_id=transaction_data['processed_file_id'],
                transaction_date=transaction_data['transaction_date'],
                description=transaction_data['description'],
                debit_amount=transaction_data.get('debit_amount'),
                credit_amount=transaction_data.get('credit_amount'),
                balance=transaction_data.get('balance'),
                reference_number=transaction_data.get('reference_number'),
                transaction_type=transaction_data['transaction_type'],
                enum_id=transaction_data.get('enum_id'),
                category=transaction_data.get('category'),
                transaction_category=transaction_data.get('transaction_category'),
                reason=transaction_data.get('reason'),
                splits=splits_data,  # Keep legacy JSON for backwards compatibility
                has_splits=has_splits,
                is_settled=transaction_data.get('is_settled', False)
            )
            
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            
            # Create TransactionSplit records if splits exist
            if splits_data:
                transaction_amount = transaction_data.get('debit_amount') or transaction_data.get('credit_amount') or 0
                self._create_transaction_splits(session, transaction.id, splits_data, transaction_amount)
            
            # Return detached instance
            session.expunge(transaction)
            return transaction
            
        finally:
            session.close()
    
    def _create_transaction_splits(self, session, transaction_id: int, splits_data: List[Dict], transaction_amount: float):
        """Create TransactionSplit records for a transaction"""
        TransactionSplit = self.models['TransactionSplit']
        
        for split in splits_data:
            person_name = split['person'].lower().strip()
            percentage = float(split['percentage'])
            amount = transaction_amount * (percentage / 100)
            
            split_record = TransactionSplit(
                transaction_id=transaction_id,
                person_name=person_name,
                percentage=percentage,
                amount=amount,
                is_settled=False  # Default to not settled
            )
            
            session.add(split_record)
        
        session.commit()
    
    def update_split_settlement_status(self, split_id: int, is_settled: bool):
        """Update settlement status for a specific split"""
        session = self.db_manager.get_session()
        try:
            TransactionSplit = self.models['TransactionSplit']
            
            split = session.query(TransactionSplit).filter_by(id=split_id).first()
            if split:
                split.is_settled = is_settled
                split.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
            
        finally:
            session.close()
    
    def get_unsettled_amounts_by_person(self, person_name: Optional[str] = None):
        """Get unsettled amounts by person"""
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import func
            TransactionSplit = self.models['TransactionSplit']
            
            query = session.query(
                TransactionSplit.person_name,
                func.sum(TransactionSplit.amount).label('unsettled_amount'),
                func.count(TransactionSplit.id).label('unsettled_count')
            ).filter(
                TransactionSplit.is_settled == False
            )
            
            if person_name:
                query = query.filter(TransactionSplit.person_name == person_name.lower().strip())
            
            results = query.group_by(TransactionSplit.person_name).all()
            return [(person, float(amount), count) for person, amount, count in results]
            
        finally:
            session.close()
    
    def get_person_unsettled_transactions(self, person_name: str):
        """Get all unsettled transactions for a specific person"""
        session = self.db_manager.get_session()
        try:
            Transaction = self.models['Transaction']
            TransactionSplit = self.models['TransactionSplit']
            
            query = session.query(Transaction, TransactionSplit).join(
                TransactionSplit, Transaction.id == TransactionSplit.transaction_id
            ).filter(
                TransactionSplit.person_name == person_name.lower().strip(),
                TransactionSplit.is_settled == False
            ).order_by(Transaction.transaction_date.desc())
            
            results = query.all()
            return [(txn, split) for txn, split in results]
            
        finally:
            session.close()
    
    def get_person_transactions(self, person_name: str, start_date=None, end_date=None, test_mode=False):
        """Get all transactions involving a specific person"""
        session = self.db_manager.get_session()
        try:
            Transaction = self.models['Transaction']
            TransactionSplit = self.models['TransactionSplit']
            
            query = session.query(Transaction, TransactionSplit).join(
                TransactionSplit, Transaction.id == TransactionSplit.transaction_id
            ).filter(
                TransactionSplit.person_name == person_name.lower().strip()
            )
            
            if start_date:
                query = query.filter(Transaction.transaction_date >= start_date)
            if end_date:
                query = query.filter(Transaction.transaction_date <= end_date)
            
            results = query.all()
            return [(txn, split) for txn, split in results]
            
        finally:
            session.close()
    
    def get_person_total_amount(self, person_name: str, start_date=None, end_date=None):
        """Get total amount paid for a specific person"""
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import func
            Transaction = self.models['Transaction']
            TransactionSplit = self.models['TransactionSplit']
            
            query = session.query(func.sum(TransactionSplit.amount)).join(
                Transaction, Transaction.id == TransactionSplit.transaction_id
            ).filter(
                TransactionSplit.person_name == person_name.lower().strip()
            )
            
            if start_date:
                query = query.filter(Transaction.transaction_date >= start_date)
            if end_date:
                query = query.filter(Transaction.transaction_date <= end_date)
            
            result = query.scalar()
            return result or 0.0
            
        finally:
            session.close()
    
    def create_skipped_transaction(self, transaction_data: Dict[str, Any]):
        """Create skipped transaction record with raw data"""
        session = self.db_manager.get_session()
        try:
            SkippedTransaction = self.models['SkippedTransaction']
            
            skipped = SkippedTransaction(
                transaction_hash=transaction_data['transaction_hash'],
                institution_id=transaction_data['institution_id'],
                processed_file_id=transaction_data['processed_file_id'],
                raw_data=transaction_data['raw_data'],  # Store raw data as-is
                row_number=transaction_data.get('row_number'),
                skip_reason=transaction_data['skip_reason']
            )
            
            session.add(skipped)
            session.commit()
            session.refresh(skipped)
            
            # Return detached instance  
            session.expunge(skipped)
            return skipped
            
        finally:
            session.close()
    
    def create_processing_log(self, processed_file_id: int, total_transactions: int,
                            processed_transactions: int, skipped_transactions: int,
                            duplicate_transactions: int, duplicate_skipped: int,
                            processing_time: float):
        """Create processing log"""
        session = self.db_manager.get_session()
        try:
            ProcessingLog = self.models['ProcessingLog']
            
            log = ProcessingLog(
                processed_file_id=processed_file_id,
                total_transactions=total_transactions,
                processed_transactions=processed_transactions,
                skipped_transactions=skipped_transactions,
                duplicate_transactions=duplicate_transactions,
                duplicate_skipped=duplicate_skipped,
                processing_time=processing_time
            )
            
            session.add(log)
            session.commit()
            session.refresh(log)
            
            # Return detached instance
            session.expunge(log)
            return log
            
        finally:
            session.close()
    
    def check_transaction_exists(self, transaction_hash: str) -> bool:
        """Check if transaction already exists"""
        session = self.db_manager.get_session()
        try:
            Transaction = self.models['Transaction']
            
            existing = session.query(Transaction).filter_by(
                transaction_hash=transaction_hash
            ).first()
            
            return existing is not None
            
        finally:
            session.close()
    
    def check_skipped_transaction_exists(self, transaction_hash: str) -> bool:
        """Check if transaction was already skipped"""
        session = self.db_manager.get_session()
        try:
            SkippedTransaction = self.models['SkippedTransaction']
            
            existing = session.query(SkippedTransaction).filter_by(
                transaction_hash=transaction_hash
            ).first()
            
            return existing is not None
            
        finally:
            session.close() 