import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  Pagination,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { transactionApi } from '../services/api';
import type { Transaction, TransactionListResponse } from '../types';

interface TransactionTableProps {
  onEditTransaction?: (transaction: Transaction) => void;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  onEditTransaction,
}) => {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>('');
  const [search, setSearch] = useState('');
  const pageSize = 25;

  const {
    data: transactionData,
    isLoading,
    error,
    refetch,
  } = useQuery<TransactionListResponse>({
    queryKey: ['transactions', page, status, search],
    queryFn: () => transactionApi.list({
      page,
      size: pageSize,
      status: status || undefined,
      search: search || undefined,
    }),
    staleTime: 30000, // 30 seconds
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'processed':
        return 'success';
      case 'skipped':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatAmount = (amount: number | undefined, currency = 'INR') => {
    if (amount === undefined) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const totalPages = Math.ceil((transactionData?.total || 0) / pageSize);

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load transactions. Please try again.
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Transaction Management
      </Typography>

      {/* Filters */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search descriptions..."
          size="small"
          sx={{ minWidth: 200 }}
        />
        <TextField
          select
          label="Status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          size="small"
          sx={{ minWidth: 120 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="pending">Pending</MenuItem>
          <MenuItem value="processed">Processed</MenuItem>
          <MenuItem value="skipped">Skipped</MenuItem>
        </TextField>
        <Tooltip title="Refresh">
          <IconButton onClick={() => refetch()} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Statistics */}
      {transactionData && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="textSecondary">
            Showing {transactionData.items.length} of {transactionData.total} transactions
          </Typography>
        </Box>
      )}

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="right">Debit</TableCell>
              <TableCell align="right">Credit</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Category</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : transactionData?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  No transactions found
                </TableCell>
              </TableRow>
            ) : (
              transactionData?.items.map((transaction) => (
                <TableRow
                  key={transaction.id}
                  hover
                  sx={{
                    backgroundColor:
                      transaction.status === 'pending' ? '#fff3e0' : 'inherit',
                  }}
                >
                  <TableCell>
                    {formatDate(transaction.transaction_date)}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                      {transaction.description}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {formatAmount(transaction.debit_amount, transaction.currency)}
                  </TableCell>
                  <TableCell align="right">
                    {formatAmount(transaction.credit_amount, transaction.currency)}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={transaction.status}
                      color={getStatusColor(transaction.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {transaction.category || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Edit Transaction">
                      <IconButton
                        size="small"
                        onClick={() => onEditTransaction?.(transaction)}
                        disabled={transaction.status === 'processed'}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, newPage) => setPage(newPage)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
};