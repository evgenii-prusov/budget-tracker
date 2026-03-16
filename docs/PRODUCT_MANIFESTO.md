# Budget Tracker: Technical Product Manifesto

## 1. Core Vision
A personal finance tracker for a **shared household experience**. Both spouses use the same instance to track income, expenses, and transfers across multiple currencies. The system provides a web UI for daily use and a REST API for programmatic access.

## 2. Key Features

### 2.1 Multi-Currency Account Management
*   **Account-Specific Currencies:** Every account (Bank, Cash, Credit Card) has a fixed ISO currency (EUR, USD, RUB, CHF, JPY, CNY, GBP, etc.).
*   **Savings Tracking:** Accounts can be flagged as `is_savings` to differentiate liquid cash from long-term wealth in reports.
*   **Computed Balance:** Account balance is derived from `initial_balance` plus all postings and transfers — never stored separately to avoid inconsistency.
*   **Manual Entry:** No automated bank syncing; users log everything manually via the web UI or API.

### 2.2 Dual-Amount Transfers
*   **Cross-Currency Support:** Transfers between accounts of different currencies record both `debit_amount` and `credit_amount` independently.
*   **Manual Rate Override:** The effective exchange rate is derivable from the two amounts but is not stored separately.

### 2.3 2-Level Category Hierarchy
*   **Strict 2-Level Limit:** Parent categories (e.g., Food, Health) and child subcategories (e.g., Groceries, Medical).
*   **Reporting vs. Entry:**
    *   Transactions are logged against **subcategories**.
    *   Reports aggregate data at the **parent category** level (aiming for 10–15 high-level buckets).
*   **Type Enforcement:** Categories are explicitly typed as `Income` or `Expense`.

### 2.4 Transaction Details
*   **Mandatory-ish Payee:** Every transaction should track *who* was paid (Amazon, EDEKA, Uber Eats).
*   **Optional Description:** Used only for additional context when the payee/category isn't self-explanatory.

### 2.5 Spending Reports
*   **Period-Based Aggregation:** Reports cover `week`, `month`, or `year` periods relative to a reference date.
*   **Parent-Level Rollup:** Spending is aggregated by parent category and currency.
*   **Savings Filter:** Optionally exclude savings accounts from expense calculations.

### 2.6 Web UI
*   **Accounts page:** Create, view, and update accounts with balances.
*   **Categories page:** Manage expense/income category hierarchies.
*   **Postings page:** Record and browse income and expense transactions.
*   **Transfers page:** Transfer funds between accounts.
*   **Reports page:** Spending breakdown by period and category.

## 3. Technical Implementation Details

### 3.1 Domain Model
*   **Account:** `id, name, currency, is_savings, initial_balance, description`. Balance is computed.
*   **Category:** `id, name, parent_id (null for root), type (income/expense), description`.
*   **Posting (Transaction):** `id, account_id, category_id, amount, posting_date, posting_type, payee, description`.
*   **Transfer:** `id, source_account_id, dest_account_id, debit_amount, credit_amount, transfer_date, description`.

### 3.2 Architecture
*   **Pattern:** Domain-Driven Design (DDD) with hexagonal architecture.
*   **Layers:** REST API → Service Layer → Abstract Repositories → SQLAlchemy (imperative mapping) → PostgreSQL.
*   **Aggregates:** `Account` (owns `Posting`), `Transfer`, `Category` — each with its own repository.
*   **Invariants:** All monetary values use `Decimal`. Account balance is computed, not stored. Postings can only be made against leaf categories.

### 3.3 Tech Stack
*   **Backend:** Python 3.12, FastAPI, SQLAlchemy (imperative mapping), Alembic, PostgreSQL 17.
*   **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query v5, Recharts.
*   **Package management:** `uv` (Python), npm (frontend).
*   **Testing:** pytest, testcontainers (real PostgreSQL for integration tests).
*   **Quality:** Ruff (lint + format), mypy (type checking).

### 3.4 Authentication
*   **Couple-Centric (Single-Tenant):** Designed for a single household sharing global state.
*   **Bearer Token:** A shared API key authenticates all requests to the REST API.

### 3.5 Deployment
*   **Local dev:** Docker Compose (Postgres + backend + frontend).
*   **Production:** Azure Container Apps (backend + frontend), PostgreSQL as managed service.
*   **CI/CD:** GitHub Actions.

## 4. Engineering Standards
*   **Contextual Precedence:** This document is the foundational mandate for all architectural decisions.
*   **API First:** Every new feature must have a corresponding FastAPI endpoint.
*   **TDD:** Tests are written first, then implementation. Unit tests use fakes; integration tests use real PostgreSQL via testcontainers.
*   **No Bullshit:** Prioritize functional domain logic and data correctness over UI polish.

---
**Version:** 3.0.0
**Status:** Active Working Document
