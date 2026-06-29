# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.8] - 2026-06-29

### Added
- Introduced a canonical transaction type taxonomy (`收入`, `支出`, `转账`, `余额变更`, `负债变更`, `债权变更`, `调整`) with alias mapping and statistics helpers.
- Automatic tag extraction during import for values wrapped in `#...#` in notes or unmapped columns.
- New tests for the transaction type system and updated import/export behavior.

### Changed
- CSV import now preserves transfer and adjustment records instead of forcing them into `收入`/`支出`.
- Imported negative or zero amounts are retained as-is, enabling refund and reconciliation records to be stored without manual rework.
- Backend summary, statistics, and export aggregations use the new type helpers to avoid double-counting transfers/adjustments as income or expense.
- Frontend transaction form and transaction list type filters now include all seven canonical transaction types.

### Fixed
- Import no longer skips refund/balance-change rows solely because the amount is negative or zero.
- Summary and export totals now exclude non-income/expense types consistently.
