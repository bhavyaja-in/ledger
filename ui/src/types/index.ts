// Types for the application
export interface User {
  id: number;
  username: string;
  roles: string;
  is_active: boolean;
}

export interface Transaction {
  id: number;
  transaction_hash: string;
  institution_id: number;
  processed_file_id: number;
  transaction_date: string;
  description: string;
  debit_amount?: number;
  credit_amount?: number;
  balance?: number;
  reference_number?: string;
  transaction_type: string;
  currency: string;
  enum_id?: number;
  category?: string;
  transaction_category?: string;
  reason?: string;
  splits?: Split[];
  has_splits: boolean;
  is_settled: boolean;
  status: 'pending' | 'processed' | 'skipped';
  created_at: string;
  updated_at: string;
}

export interface Split {
  person: string;
  percentage: number;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
  has_more: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ClassifyRequest {
  regex: string[];
  enum_name: string;
  enum_category: string;
  txn_category: string;
  reason: string;
  splits?: Split[];
}

export interface SkipRequest {
  reason: string;
}

export interface Suggestion {
  enum_id?: number;
  enum_name?: string;
  category?: string;
  txn_category?: string;
  pattern_suggestions: string[];
}

export interface TransactionEnum {
  id: number;
  enum_name: string;
  patterns: string[];
  category: string;
  processor_type: string;
  is_active: boolean;
}

export interface Category {
  name: string;
  description: string;
}