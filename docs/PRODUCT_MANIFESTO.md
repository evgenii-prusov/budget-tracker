# Budget Tracker: Technical Product Manifesto

## 1. Core Vision
A "Headless" Personal Finance Tracker designed for a **Shared AI-First Experience**. The primary interface is a hosted **MCP (Model Context Protocol) Server**, allowing both the user and their spouse to use Claude/ChatGPT mobile apps as their personal financial assistants. UI (Web/Mobile) is secondary and follows the API established for the AI.

## 2. Key Features

### 2.1 Multi-Currency Account Management
*   **Account-Specific Currencies:** Every account (Bank, Cash, Credit Card) has a fixed ISO currency (EUR, USD, RUB, JPY, etc.).
*   **Savings Tracking:** Accounts can be flagged as `is_savings` to differentiate liquid cash from long-term wealth in reports.
*   **Manual Entry:** No automated bank syncing; the users or AI log everything.

### 2.2 Dual-Amount Transfers
*   **Cross-Currency Support:** Transfers between accounts of different currencies.
*   **Manual Rate Override:** User provides both `debit_amount` and `credit_amount`. The effective exchange rate is derivable from the two amounts but is not stored separately.

### 2.3 2-Level Category Hierarchy
*   **Strict 2-Level Limit:** Parent categories (e.g., Food, Health) and Child subcategories (e.g., Groceries, Medical).
*   **Reporting vs. Entry:** 
    *   Transactions are logged against **Subcategories**.
    *   Reports aggregate data at the **Parent Category** level (aiming for 10-15 high-level buckets).
*   **Type Enforcement:** Categories are explicitly typed as `Income` or `Expense`.

### 2.4 Transaction Details
*   **Mandatory-ish Payee:** Every transaction should track *who* was paid (Amazon, EDEKA, Uber Eats).
*   **Optional Description:** Used only for additional context when the payee/category isn't self-explanatory.

### 2.5 AI-First Interface (MCP)
*   **Primary UI:** An MCP Server exposing 10 tools:
    *   **Setup:** `create_account`, `create_category`
    *   **Recording:** `add_expense`, `add_income`, `transfer_funds`
    *   **Review:** `list_accounts`, `list_categories`, `list_postings`, `list_transfers`, `get_spending`
*   **Mobile Integration:** The MCP server is hosted on a permanent URL using **Streamable HTTP** transport, mounted at `/mcp`. This allows Claude and ChatGPT mobile apps to connect to the tools.

### 2.6 Auditability
*   **Source Tracking:** Every posting and transfer records which assistant or user created it (e.g., "Claude", "ChatGPT", "manual").
*   **Purpose:** Enables the household to see who logged what, useful for resolving discrepancies and building trust in shared data.

## 3. Technical Implementation Details

### 3.1 Domain Model
*   **Account:** `id, name, currency, is_savings, initial_balance, balance`.
*   **Category:** `id, name, parent_id (null for parents), type (income/expense)`.
*   **Posting (Transaction):** `id, account_id, category_id, amount, posting_date, posting_type, payee, description`.
*   **Transfer:** `id, source_account_id, dest_account_id, debit_amount, credit_amount, transfer_date, description`.

### 3.2 Shared Experience & Auth
*   **Couple-Centric (Single-Tenant):** Designed for a single household sharing a global state.
*   **Permanent Access:** A shared API Key or Bearer Token is used to authenticate the MCP server requests from mobile apps.
*   **Auditability:** While sharing a `user_id` for now, the system should log which "Assistant Instance" (or descriptive tag) made the entry if possible.

### 3.3 Deployment Strategy
*   **Backend:** FastAPI hosted on a public-facing VPS (or tunnel via Cloudflare) to be reachable by LLM providers.
*   **MCP Server:** Streamable HTTP endpoint at `/mcp` that exposes tools directly backed by the service layer. Must be robust enough to handle simultaneous requests from both spouses.

## 4. Engineering Standards for AI Agents
*   **Contextual Precedence:** This document is the foundational mandate for all architectural decisions.
*   **API First:** Every new feature must have a corresponding FastAPI endpoint AND an MCP Tool definition.
*   **MCP Transport:** Streamable HTTP is the production transport, mounted on the FastAPI app at `/mcp`.
*   **No Bullshit:** Prioritize functional domain logic and AI-tool reliability over secondary UI polish.

---
**Version:** 2.0.0
**Status:** Active Working Document
