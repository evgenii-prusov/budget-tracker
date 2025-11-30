# Budget Tracker — Product Specification

**Version:** 0.1.0
**Last Updated:** 2025-11-30
**Author:** Evgenii Prusov

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Personas](#3-user-personas)
4. [Domain Model](#4-domain-model)
5. [Feature Specifications](#5-feature-specifications)
6. [Business Rules](#6-business-rules)
7. [Multi-Currency](#7-multi-currency)
8. [Reports & Analytics](#8-reports--analytics)
9. [API Contracts](#9-api-contracts)
10. [UI/UX Specifications](#10-uiux-specifications)
11. [Non-Functional Requirements](#11-non-functional-requirements)
12. [Future Considerations](#12-future-considerations)
13. [Glossary](#13-glossary)

---

## 1. Overview

### 1.1 Vision Statement

Budget Tracker is a personal finance application that helps individuals track their income, expenses, and transfers across multiple accounts and currencies, providing insights into spending patterns and progress toward financial goals.

### 1.2 Problem Statement

It is challenging for individuals to maintain a clear overview of their personal finances, especially when managing multiple accounts and currencies. Existing solutions may lack flexibility and modern features like OCR for receipts and AI assistance. Another reason is that I want to have a personal project to experiment with new technologies and improve my software engineering skills. This project also should be a tracked record of my modern coding abilities for potential employers or collaborators.

### 1.3 Target Users

Primary target is myself as an individual user who wants to track personal finances effectively. Secondary target includes other individuals seeking a simple yet powerful tool for personal finance management without relying on third-party services.

### 1.4 Key Differentiators

The integration of OCR for invoice scanning and AI assistance for financial insights sets it apart from traditional budgeting apps.

---

## 2. Goals & Non-Goals

### 2.1 Goals (MVP)

| ID | Goal | Priority |
|----|------|----------|
| G01 | Track income and expenses across multiple accounts | Must Have |
| G02 | Support transfers between accounts | Must Have |
| G03 | Categorize transactions | Must Have |
| G04 | Multi-currency support with conversion | Must Have |
| G05 | Upload and OCR invoices/receipts | Nice to Have |
| G06 | Monthly budget tracking per category | Must Have |
| G07 | Basic spending reports | Must Have |
| G08 | Integration with AI assistant for financial insights | Nice to Have |
| G09 | Categories management | Must Have |
| G10 | User authentication and multi-tenancy | Must Have |
| G11 | Project-based expense tracking | Must Have |
| G12 | Telegram bot for quick transaction entry | Nice to Have |
| G13 | Mobile app | Future |
| G14 | Bank API integration (Plaid) | Future |
| G15 | Forecasting and financial goal setting | Future |

### 2.2 Non-Goals (MVP)

> (Explicitly state what you're NOT building in MVP)

| ID | Non-Goal | Reason |
|----|----------|--------|
| NG1 | Bank API integration (Plaid) | Complexity, post-MVP |
| NG2 | Shared/family accounts | Post-MVP |
| NG3 | Investment tracking | Different domain |
| NG4 | Mobile app | Post-MVP |

### 2.3 Success Metrics

> (How will you measure if the app is successful?)

| Metric | Target |
|--------|--------|
| Daily active usage | Personal use |
| Transaction entry time | < 10 seconds |
| Report generation time | < 2 seconds |
| MVP adoption | Personal use for 3+ months |
| At least 1 beta tester outside myself use the app | Yes |

---

## 3. User Personas

### 3.1 Primary Persona: "Evgenii – The Tech-Savvy Finance Tracker"

**Name:** Evgenii  
**Age:** 30-40  
**Role:** Software engineer managing personal finances across multiple accounts and currencies  

**Goals:**

- Track all income, expenses, and transfers in one place without manual bank syncing
- Understand spending patterns and stay within monthly budgets
- Manage finances across multiple currencies (EUR, JPY, RUB, etc.)
- Quickly log transactions on-the-go with minimal friction
- Have full control and ownership of financial data (self-hosted)
- Experiment with modern technologies while solving a real personal problem

**Pain Points:**

- Existing budgeting apps are either too simplistic or overly complex
- Limitations in data analysis and reporting features
- Difficult to track expenses per project, for example for particular travel or work-related costs
- Needs a portfolio project that demonstrates modern development skills

**Technical Proficiency:** High  

- Comfortable with command-line tools and APIs
- Can self-host applications (Docker, cloud deployment)
- Appreciates clean API design and good documentation
- Values automation (OCR, recurring transactions)

**Behaviors:**

- Prefers keyboard shortcuts and quick actions
- Likely to use Telegram bot for rapid transaction entry and reports
- Will customize categories and budgets to fit personal needs
- May want to extend the app with custom features

**Success Criteria:**

- Can log a transaction in under 5 seconds
- Clear visibility into monthly spending vs. budget
- Real bank accounts are accurately reflected in the app
- Could generate reports showing spending trends
- Could compare spending across different periods
- Could forecast future expenses based on historical data
- Confidence that all financial data is accurate and private
- Backup and restore functionality works seamlessly

---

### 3.2 Secondary Persona: "Anna, blogger with variable income"

**Name:** Anna
**Age:** 25-35
**Role:** My wife managing household and personal finances

**Goals:**

- Track variable monthly income from multiple clients
- Set realistic budgets for different expense categories
- Save for irregular expenses (taxes, equipment, travel)
- Understand which months/categories overspend
- Attach invoices and receipts for tax purposes

**Pain Points:**

- Income varies significantly month-to-month
- Hard to predict budget needs without historical data
- Forgets to log small cash expenses
- Wants simple reports without complex accounting knowledge

**Technical Proficiency:** Medium  

- Comfortable with web applications and mobile apps
- Not interested in technical setup (prefers hosted solution)
- Appreciates intuitive UI and minimal configuration

**Behaviors:**

- Checks budget status weekly
- Uploads receipts immediately after purchases
- May use mobile app more than desktop
- May use telegram bot for quick entries

**Success Criteria:**

- Can easily see if current month is on track with budget
- Feels in control of irregular income/expenses

---

## 4. Domain Model

### 4.1 Core Entities

```plain text
┌─────────────────────────────────────────────────────────────────┐
│                          USER                                    │
│  (Tenant - all data scoped to user)                             │
└───────────────┬─────────────────────────────────────────────────┘
                │
                │ owns
                ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│         ACCOUNT           │     │        CATEGORY           │
│  - Bank accounts          │     │  - Income categories      │
│  - Cash                   │     │  - Expense categories     │
│  - Credit cards           │     │  - Hierarchical (parent)  │
│  - Savings                │     │                           │
└───────────────┬───────────┘     └─────────────┬─────────────┘
                │                               │
                │ has                           │ assigned to
                ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TRANSACTION                               │
│  - Income: money coming in                                       │
│  - Expense: money going out                                      │
│  - Transfer: money between accounts                              │
└───────────────┬─────────────────────────────────────────────────┘
                │
                │ may have
                ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│         INVOICE           │     │          BUDGET           │
│  - Receipt images         │     │  - Monthly limits         │
│  - OCR extracted data     │     │  - Per category           │
└───────────────────────────┘     └───────────────────────────┘
```

### 4.2 Entity Definitions

#### 4.2.1 User

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| email | String | Yes | Unique, used for login |
| username | String | Yes | Display name |
| default_currency | String(3) | Yes | ISO 4217 code (e.g., EUR) |
| timezone | String | No | User's timezone |
| created_at | DateTime | Yes | Registration date |

#### 4.2.2 Account

> An Account represents a financial container (bank account, wallet, credit card, etc.)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| name | String(100) | Yes | Account name |
| account_type | Enum | Yes | See Account Types below |
| currency | String(3) | Yes | ISO 4217 code |
| initial_balance | Decimal | Yes | Starting balance |
| current_balance | Decimal | Computed | Calculated field |
| icon | String | No | Icon identifier |
| color | String(7) | No | Hex color code |
| is_active | Boolean | Yes | Soft delete flag |
| include_in_total | Boolean | Yes | Include in net worth |
| created_at | DateTime | Yes | |

**Account Types:**

| Type | Code | Description | Balance Type |
|------|------|-------------|--------------|
| Bank Account | `checking` | Regular bank account | Can be negative |
| Savings | `savings` | Savings account | Typically positive |
| Cash | `cash` | Physical cash/wallet | Positive only |
| Credit Card | `credit_card` | Credit card | Typically negative |

**Business Rules:**

- [ ] Account name must be unique per user
- [ ] Deleting account requires handling existing transactions
- [ ] Deleting category with transactions requires reassignment to another category

#### 4.2.3 Category

> Categories organize transactions into meaningful groups

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| name | String(100) | Yes | Category name |
| category_type | Enum | Yes | `income` or `expense` |
| parent_id | FK(Category) | No | Parent category (for hierarchy) |
| icon | String | No | Icon identifier |
| color | String(7) | No | Hex color |
| is_active | Boolean | Yes | Soft delete flag |
| sort_order | Integer | No | Display order |

**Default Categories (Seed Data):**

**Income Categories:**

| Name | Icon | Subcategories |
|------|------|---------------|
| Salary | 💼 | Main job, Side job |
| Freelance | 💻 | |
| Investments | 📈 | Dividends, Interest, Capital gains |
| Gifts | 🎁 | |
| Social Benefits | 🏛️ | |
| Other Income | ➕ | |

**Expense Categories:**

| Name | Icon | Subcategories |
|------|------|---------------|
| Housing | 🏠 | Rent/Mortgage, Utilities, Maintenance |
| Food | 🍔 | Groceries, Restaurants, Coffee |
| Transportation | 🚗 | Fuel, Public transit, Maintenance, Parking |
| Healthcare | 🏥 | Doctor, Pharmacy, Insurance |
| Entertainment | 🎬 | Movies, Games, Subscriptions |
| Shopping | 🛒 | Clothing, Electronics, Home goods |
| Personal | 👤 | Haircut, Gym, Education |
| Financial | 🏦 | Bank fees, Interest payments |
| Travel | ✈️ | Flights, Hotels, Activities |
| Other Expense | ➖ | |

**Business Rules:**

- [ ] Category name must be unique within same parent and user
- [ ] Maximum hierarchy depth: 2 levels (parent → child)

#### 4.2.4 Transaction

> A Transaction represents a single financial event

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| transaction_type | Enum | Yes | `income`, `expense`, `transfer` |
| account_id | FK(Account) | Yes | Source account |
| category_id | FK(Category) | Conditional | Required for income/expense |
| project_id | FK(Project) | No | Optional project association |
| amount | Decimal | Yes | Always positive |
| currency | String(3) | Yes | Transaction currency |
| date | Date | Yes | Transaction date |
| description | Text | No | Notes/memo |
| payee | String(200) | No | Who paid / who received |
| created_at | DateTime | Yes | |
| updated_at | DateTime | Yes | |

**Transfer-specific fields:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| to_account_id | FK(Account) | Yes* | Destination account (*if transfer) |
| to_amount | Decimal | No | Amount in destination currency |
| exchange_rate | Decimal | No | Rate used for conversion |

**Transaction Types:**

| Type | Description | Account Impact | Category Required |
|------|-------------|----------------|-------------------|
| `income` | Money received | +amount to account | Yes (income type) |
| `expense` | Money spent | -amount from account | Yes (expense type) |
| `transfer` | Move between accounts | -from source, +to destination | No |

**Business Rules:**

- [ ] Amount must be positive (type determines direction)
- [ ] Income transaction requires income-type category
- [ ] Expense transaction requires expense-type category
- [ ] Transfer requires both source and destination accounts
- [ ] Transfer between different currencies requires exchange rate
- [ ] There should be an option to split transactions into multiple parts based on categories
      in case if one transaction covers multiple expense types (e.g., groceries and dining out)

#### 4.2.5 Invoice

> An Invoice represents an uploaded receipt/invoice image with OCR data

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| transaction_id | FK(Transaction) | No | Linked transaction |
| file_path | String | Yes | S3/MinIO path |
| file_name | String | Yes | Original filename |
| file_size | Integer | Yes | Size in bytes |
| content_type | String | Yes | MIME type |
| ocr_status | Enum | Yes | `pending`, `processing`, `completed`, `failed` |
| ocr_text | Text | No | Raw extracted text |
| ocr_data | JSON | No | Structured extracted data |
| ocr_confidence | Float | No | OCR confidence score |
| ocr_processed_at | DateTime | No | When OCR completed |
| created_at | DateTime | Yes | |

**OCR Extracted Data Structure:**

```json
{
  "vendor": "Store Name",
  "date": "2025-01-15",
  "total": 42.50,
  "currency": "EUR",
  "items": [
    {"description": "Item 1", "amount": 10.00},
    {"description": "Item 2", "amount": 32.50}
  ],
  "tax": 8.50,
  "payment_method": "card"
}
```

**Business Rules:**

- [ ] Maximum file size: 10MB
- [ ] Allowed formats: JPEG, PNG, PDF
- [ ] OCR processing is asynchronous
- [ ] One invoice can link to one transaction

#### 4.2.6 Budget

> A Budget sets spending limits per category for a time period

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| category_id | FK(Category) | Yes | Expense category |
| amount | Decimal | Yes | Budget limit |
| currency | String(3) | Yes | Budget currency |
| period_type | Enum | Yes | `monthly`, `weekly`, `yearly` |
| year | Integer | Yes | Budget year |
| month | Integer | Conditional | Required if monthly |
| week | Integer | Conditional | Required if weekly |
| rollover | Boolean | No | Carry unused to next period |
| created_at | DateTime | Yes | |

**Business Rules:**

- [ ] One budget per category per period
- [ ] Budget currency should match user's default currency
- [ ] Only expense categories can have budgets

---

#### 4.2.7 Project

> A Project groups related transactions for tracking specific events or initiatives (e.g., business trips, vacations, home renovations)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID/Integer | Yes | Primary key |
| user_id | FK(User) | Yes | Owner |
| name | String(200) | Yes | Project name (e.g., "Tokyo Business Trip", "Spain Vacation 2025") |
| description | Text | No | Project details and notes |
| start_date | Date | No | Project start date |
| end_date | Date | No | Project end date |
| budget | Decimal | No | Total budget for the project |
| currency | String(3) | No | Project budget currency (defaults to user's default) |
| status | Enum | Yes | `active`, `completed`, `archived` |
| color | String(7) | No | Hex color for visual identification |
| icon | String | No | Icon identifier |
| is_active | Boolean | Yes | Soft delete flag |
| created_at | DateTime | Yes | |
| updated_at | DateTime | Yes | |

**Project Status:**

| Status | Description |
|--------|-------------|
| `active` | Currently tracking expenses |
| `completed` | Project finished, no longer accepting transactions |
| `archived` | Historical project, hidden from default views |

**Business Rules:**

- [ ] Project name must be unique per user
- [ ] Transactions can be linked to at most one project
- [ ] Project budget is optional but recommended for tracking
- [ ] Completed/archived projects can still be viewed in reports
- [ ] Deleting a project unlinks transactions (doesn't delete them)
- [ ] Project date range is optional and informational only

**Common Use Cases:**

- Travel: "Tokyo Business Trip 2025", "Spain Vacation August"
- Events: "Wedding Planning", "Birthday Party"
- Home: "Kitchen Renovation", "Garden Project"
- Work: "Conference Travel", "Client Meeting NYC"

---

## 5. Feature Specifications

### 5.1 Account Management

#### F1.1: Create Account

**User Story:**  
As a user, I want to create a new account so that I can track finances for that account.

**Acceptance Criteria:**

- [ ] User can enter account name (required, max 100 chars)
- [ ] User can select account type from predefined list
- [ ] User can select currency from supported currencies
- [ ] User can enter initial balance (default: 0)
- [ ] User can select icon (optional)
- [ ] User can select color (optional)
- [ ] User can choose if account is included in net worth total
- [ ] System validates uniqueness of name per user
- [ ] System creates account with provided details
- [ ] System displays new account in account list

**API Endpoint:** `POST /api/accounts`

---

#### F1.2: Edit Account

**User Story:**  
As a user, I want to edit an existing account to update its details.

**Acceptance Criteria:**

- [ ] User can update name, icon, color, include_in_total
- [ ] User cannot change currency if transactions exist
- [ ] User cannot change account type if transactions exist
- [ ] System validates and saves changes
- [ ] System recalculates balance if initial_balance changed

**API Endpoint:** `PATCH /api/accounts/{id}`

---

#### F1.3: Archive/Delete Account

**User Story:**  
As a user, I want to archive an account I no longer use.

**Acceptance Criteria:**

- [ ] User can archive account (soft delete)
- [ ] Archived accounts hidden from default views
- [ ] User can view archived accounts separately
- [ ] User can restore archived account
- [ ] User can permanently delete only if no transactions

**API Endpoint:** `DELETE /api/accounts/{id}` (archive)

---

#### F1.4: View Account Balance

**User Story:**  
As a user, I want to see the current balance of each account.

**Acceptance Criteria:**

- [ ] Balance = initial_balance + sum(income) - sum(expense) + sum(transfer_in) - sum(transfer_out)
- [ ] Balance displayed in account's currency
- [ ] Balance updated in real-time after transactions
- [ ] Show balance converted to default currency (optional)

---

### 5.2 Transaction Management

#### F2.1: Create Income Transaction

**User Story:**  
As a user, I want to record income so that I can track money received.

**Acceptance Criteria:**

- [ ] User selects transaction type: Income
- [ ] User selects destination account (required)
- [ ] User enters amount (required, positive)
- [ ] User selects income category (required)
- [ ] User enters date (required, default: today)
- [ ] User enters description (optional)
- [ ] User enters payee/source (optional)
- [ ] System adds amount to account balance
- [ ] System creates transaction record
- [ ] List of payees auto-suggested based on previous entries

**API Endpoint:** `POST /api/transactions`

---

#### F2.2: Create Expense Transaction

**User Story:**  
As a user, I want to record an expense to track money spent.

**Acceptance Criteria:**

- [ ] User selects transaction type: Expense
- [ ] User selects source account (required)
- [ ] User enters amount (required, positive)
- [ ] User selects expense category (required)
- [ ] User enters date (required, default: today)
- [ ] User enters description (optional)
- [ ] User enters payee/merchant (optional)
- [ ] User can attach invoice/receipt (optional)
- [ ] System subtracts amount from account balance
- [ ] System creates transaction record

**API Endpoint:** `POST /api/transactions`

---

#### F2.3: Create Transfer Transaction

**User Story:**  
As a user, I want to transfer money between accounts.

**Acceptance Criteria:**

- [ ] User selects transaction type: Transfer
- [ ] User selects source account (required)
- [ ] User selects destination account (required, different from source)
- [ ] User enters amount in source currency (required)
- [ ] If currencies differ, User enters destination amount and System calculates exchange rate
- [ ] User enters date (required, default: today)
- [ ] User enters description (optional)
- [ ] System subtracts from source account
- [ ] System adds to destination account (converted if needed)
- [ ] System stores exchange rate used
- [ ] System validates exchange rate in case user enters incorrect values
- [ ] User only can create transaction he owns

**API Endpoint:** `POST /api/transactions`

**Example - Same Currency:**

```plaintext
Source: Sparkassa Evg (EUR) - €100
Destination: Revolute Iana (EUR) + €100
```

**Example - Different Currencies:**

```plaintext
Source: Sparkassa Evg (EUR) - €100
Destination: Revolute Iana (USD) + $108 (rate: 1.08)
Exchange Rate: 1.08 stored
```

---

#### F2.4: Edit Transaction

**User Story:**
As a user, I want to edit a transaction to fix mistakes.

**Acceptance Criteria:**

- [ ] User can edit all transaction fields
- [ ] Changing amount recalculates account balance
- [ ] Changing account recalculates both old and new account balances
- [ ] System maintains audit trail (optional: store original values)
- [ ] System updates updated_at timestamp
- [ ] User can change only transactions he owns

**API Endpoint:** `PATCH /api/transactions/{id}`

---

#### F2.5: Delete Transaction

**User Story:**  
As a user, I want to delete an incorrect transaction.

**Acceptance Criteria:**

- [ ] User confirms deletion
- [ ] System reverses balance impact
- [ ] System removes transaction record
- [ ] Linked invoices are unlinked (not deleted)
- [ ] User can delete only transactions he owns

**API Endpoint:** `DELETE /api/transactions/{id}`

---

#### F2.6: List/Filter Transactions

**User Story:**  
As a user, I want to view and filter my transactions.

**Acceptance Criteria:**

- [ ] Default view: current month transactions
- [ ] Filter by date range
- [ ] Filter by account(s)
- [ ] Filter by category(s)
- [ ] Filter by transaction type
- [ ] Filter by amount range
- [ ] Search by description/payee
- [ ] Sort by date, amount, category
- [ ] Pagination support

**API Endpoint:** `GET /api/transactions`

---

### 5.3 Category Management

#### F3.1: Create Category

**Acceptance Criteria:**

- [ ] User enters name (required)
- [ ] User selects type: income or expense
- [ ] User selects parent category (optional, for subcategory)
- [ ] User selects icon (optional)
- [ ] User selects color (optional)
- [ ] System validates uniqueness

**API Endpoint:** `POST /api/categories`

---

#### F3.2: Edit/Delete Category

**Acceptance Criteria:**

- [ ] User can edit name, icon, color
- [ ] User cannot change type if transactions exist
- [ ] User can archive category (transactions keep reference)
- [ ] User can merge category into another (migrate transactions)

**API Endpoint:** `PATCH/DELETE /api/categories/{id}`

---

### 5.4 Invoice/Receipt Management

#### F4.1: Upload Invoice

**User Story:**  
As a user, I want to upload a receipt image to attach to a transaction.

**Acceptance Criteria:**

- [ ] User can upload image (JPEG, PNG) or PDF
- [ ] Maximum file size: 10MB
- [ ] System stores file in S3/MinIO
- [ ] System queues OCR processing
- [ ] User sees upload progress
- [ ] User can optionally link to existing transaction

**API Endpoint:** `POST /api/invoices`

---

#### F4.2: OCR Processing

**User Story:**  
As a user, I want receipts automatically scanned to extract data.

**Acceptance Criteria:**

- [ ] System processes image with Tesseract OCR
- [ ] System attempts to extract: vendor, date, total, items
- [ ] System stores raw text and structured data
- [ ] User notified when processing complete
- [ ] User can view extracted data
- [ ] User can create transaction from extracted data

**Background Task:** Celery task

---

#### F4.3: Create Transaction from Invoice

**User Story:**  
As a user, I want to quickly create a transaction from scanned receipt data.

**Acceptance Criteria:**

- [ ] System pre-fills transaction form with OCR data
- [ ] User reviews and adjusts as needed
- [ ] User selects account and category
- [ ] System creates transaction linked to invoice

---

### 5.5 Budget Management

#### F5.1: Create Budget

**User Story:**  
As a user, I want to set spending limits for categories.

**Acceptance Criteria:**

- [ ] User selects expense category
- [ ] User enters budget amount
- [ ] User selects period (monthly/weekly/yearly)
- [ ] User can enable rollover of unused amount
- [ ] System validates one budget per category per period

**API Endpoint:** `POST /api/budgets`

---

#### F5.2: View Budget Progress

**User Story:**
As a user, I want to see how much I've spent vs. budgeted.

**Acceptance Criteria:**

- [ ] Show budgeted amount per category
- [ ] Show spent amount (sum of expenses in period)
- [ ] Show remaining amount
- [ ] Show percentage used
- [ ] Visual indicator (progress bar, color coding)
- [ ] Alert when approaching/exceeding budget

---

### 5.6 Project Management

#### F6.1: Create Project

**User Story:**
As a user, I want to create a project to track related expenses for a specific event or initiative.

**Acceptance Criteria:**

- [ ] User can enter project name (required, max 200 chars)
- [ ] User can enter description (optional)
- [ ] User can set start and end dates (optional)
- [ ] User can set project budget (optional)
- [ ] User can select currency (defaults to user's default)
- [ ] User can select icon and color for visual identification (optional)
- [ ] System validates uniqueness of name per user
- [ ] System creates project with status 'active'
- [ ] System displays new project in project list

**API Endpoint:** `POST /api/projects`

---

#### F6.2: Link Transaction to Project

**User Story:**
As a user, I want to associate a transaction with a project to track project-specific spending.

**Acceptance Criteria:**

- [ ] User can select project when creating/editing transaction (optional dropdown)
- [ ] Only active projects shown in dropdown by default
- [ ] User can optionally view completed projects in dropdown
- [ ] Transaction can only be linked to one project at a time
- [ ] System updates project total spent when transaction linked/unlinked
- [ ] Linking/unlinking updates project statistics in real-time

**API Endpoint:** `POST /api/transactions` (with project_id field)

---

#### F6.3: View Project Summary

**User Story:**
As a user, I want to see an overview of all expenses for a specific project.

**Acceptance Criteria:**

- [ ] Show project name, description, dates
- [ ] Show total spent vs. budget (if set)
- [ ] Show percentage of budget used (if budget set)
- [ ] Show list of all transactions linked to project
- [ ] Show spending breakdown by category within project
- [ ] Show spending over time (timeline chart)
- [ ] Filter transactions by date range
- [ ] Allow export of project report

**API Endpoint:** `GET /api/projects/{id}`

---

#### F6.4: Complete/Archive Project

**User Story:**
As a user, I want to mark a project as completed when it's finished.

**Acceptance Criteria:**

- [ ] User can change project status to 'completed'
- [ ] Completed projects hidden from active project dropdown by default
- [ ] User can still view completed projects in project list
- [ ] User can archive projects (soft delete)
- [ ] Archived projects hidden from default views
- [ ] User can restore archived projects
- [ ] Transactions remain linked to completed/archived projects

**API Endpoint:** `PATCH /api/projects/{id}`

---

#### F6.5: Project Reports

**User Story:**
As a user, I want to compare spending across different projects.

**Acceptance Criteria:**

- [ ] List all projects with total spent for each
- [ ] Compare budget vs. actual for all projects
- [ ] Filter by status (active/completed/all)
- [ ] Sort by name, date, budget, spent
- [ ] Show projects over/under budget
- [ ] Export project comparison report

**API Endpoint:** `GET /api/projects`

---

---

## 6. Business Rules

### 6.1 Account Rules

| ID | Rule | Enforcement |
|----|------|-------------|
| AR1 | Account name unique per user | Database constraint |
| AR2 | Currency immutable after first transaction | Application logic |
| AR3 | Balance must reflect all transactions | Computed/trigger |
| AR4 | Credit card balance typically negative | UI guidance only |

### 6.2 Transaction Rules

| ID | Rule | Enforcement |
|----|------|-------------|
| TR1 | Amount always stored as positive | Validation |
| TR2 | Income requires income-type category | Validation |
| TR3 | Expense requires expense-type category | Validation |
| TR4 | Transfer requires two different accounts | Validation |
| TR5 | Cross-currency transfer requires exchange rate | Validation |
| TR6 | Transaction date could be future (planned) | Validation |

### 6.3 Category Rules

| ID | Rule | Enforcement |
|----|------|-------------|
| CR1 | Category name unique per user per parent | Database constraint |
| CR2 | Max hierarchy depth: 2 levels | Validation |
| CR3 | Cannot delete category with transactions | Validation |

### 6.4 Budget Rules

| ID | Rule | Enforcement |
|----|------|-------------|
| BR1 | One budget per category per period | Database constraint |
| BR2 | Budget only for expense categories | Validation |
| BR3 | Budget currency matches user's default | Validation |

### 6.5 Project Rules

| ID | Rule | Enforcement |
|----|------|-------------|
| PR1 | Project name unique per user | Database constraint |
| PR2 | Transaction can link to at most one project | Foreign key |
| PR3 | Deleting project unlinks transactions (SET NULL) | Database cascade |
| PR4 | Project end_date must be >= start_date | Validation |
| PR5 | Cannot delete project, only archive | Application logic |
| PR6 | There might be a budget associated with a project | Validation |

---

## 7. Multi-Currency

### 7.1 Overview

The application supports multiple currencies with the following approach:

- Each **account** has a fixed currency
- Each **transaction** is recorded in its account's currency
- **Transfers** between different currencies require exchange rate
- **Reports** can be viewed in user's default currency (converted)

### 7.2 Supported Currencies

| Code | Name | Symbol | Decimal Places |
|------|------|--------|----------------|
| EUR | Euro | € | 2 |
| USD | US Dollar | $ | 2 |
| YEN | Japanese Yen | ¥ | 0 |
| RUB | Russian Ruble | ₽ | 2 |

### 7.3 Exchange Rates

**Source:** (Define where rates come from)

- [x] Manual entry only (MVP)
- [ ] European Central Bank (ECB) API
- [ ] Open Exchange Rates API
- [ ] Other: ___________

**Update Frequency:**

- [x] Manual (user defines rate to USD for each currency, the System calculates cross rates based on that)
- [ ] Daily automatic update
- [ ] Real-time

**Storage:**

| Attribute | Type | Description |
|-----------|------|-------------|
| base_currency | String(3) | Base currency (e.g., EUR) |
| target_currency | String(3) | Target currency |
| rate | Decimal(12,6) | Exchange rate |
| date | Date | Rate date |
| source | String | Where rate came from |

### 7.4 Currency Conversion Rules

| Scenario | Rule |
|----------|------|
| Display account balance | Show in account's native currency |
| Display total net worth | Convert all to user's default currency |
| Create expense | Use account's currency |
| Transfer same currency | No conversion needed |
| Transfer different currencies | User provides both source and target amounts, system calculates rate |
| Reports by default | User's default currency |
| Reports with filter | Allow selection of currency |

### 7.5 Conversion Calculation

```plain text
Amount in target currency = Amount in source currency × Exchange rate

Example:
- Source: EUR 100
- Rate EUR/USD: 1.08
- Target: USD 108
```

**For reporting (converting to default currency):**

```plain text
Converted amount = Original amount × (1 / rate to default currency)

Example:
- Transaction: USD 108
- User default: EUR  
- Rate EUR/USD on transaction date: 1.08
- Converted: 108 / 1.08 = EUR 100
```

### 7.6 Multi-Currency behavior in Transactions

```plain text
Currency rates should be stored with start and end date to allow historical accuracy.
Each transaction should link to the rate used at the time.
On different dates, different rates may apply.
```

---

## 8. Reports & Analytics

### 8.1 Dashboard Overview

**Widgets:**

| Widget | Description | Data |
|--------|-------------|------|
| Net Worth | Total across all accounts | Sum of all account balances |
| Monthly Balance | Income vs Expense this month | Sum by type |
| Budget Progress | Category budgets status | Budget vs spent |
| Recent Transactions | Last 10 transactions | Transaction list |
| Spending by Category | Pie/donut chart | Grouped expenses |

### 8.2 Report Types

#### R1: Income vs Expense Report

**Purpose:** Compare income and expenses over time

**Parameters:**

- Date range (required)
- Granularity: daily / weekly / monthly / yearly
- Accounts: all or selected
- Currency: default or specific

**Output:**

| Period | Income | Expenses | Net |
|--------|--------|----------|-----|
| Jan 2026 | €3,000 | €2,500 | €500 |
| Feb 2026 | €3,200 | €2,800 | €400 |

**Visualization:** Bar chart (income vs expense), line chart (net over time)

---

#### R2: Spending by Category Report

**Purpose:** Understand where money goes

**Parameters:**

- Date range (required)
- Category level: top-level or detailed
- Accounts: all or selected

**Output:**

| Category | Amount | % of Total |
|----------|--------|------------|
| Housing | €1,000 | 40% |
| Food | €500 | 20% |
| Transport | €300 | 12% |

**Visualization:** Pie chart, treemap

---

#### R3: Category Trend Report

**Purpose:** See spending trends per category over time

**Parameters:**

- Category (required)
- Date range (required)
- Granularity: monthly

**Output:**

| Month | Amount | vs Previous | vs Average |
|-------|--------|-------------|------------|
| Jan | €500 | - | +10% |
| Feb | €450 | -10% | -€5 |

**Visualization:** Line chart

---

#### R4: Budget Report

**Purpose:** Track budget adherence

**Parameters:**

- Period: current month / specific month
- Categories: all budgeted or specific

**Output:**

| Category | Budget | Spent | Remaining | % Used |
|----------|--------|-------|-----------|--------|
| Food | €600 | €450 | €150 | 75% |
| Entertainment | €200 | €220 | -€20 | 110% |

**Visualization:** Progress bars, gauges

---

#### R5: Account Balance History

**Purpose:** Track account balance over time

**Parameters:**

- Account (required)
- Date range (required)

**Output:**

| Date | Balance | Change |
|------|---------|--------|
| Jan 1 | €5,000 | - |
| Jan 15 | €4,500 | -€500 |
| Jan 31 | €5,200 | +€700 |

**Visualization:** Line chart

---

#### R6: Cash Flow Report

**Purpose:** Understand money movement

**Parameters:**

- Date range (required)
- Accounts: all or selected

**Output:**

``` plain text
Opening Balance: €10,000

+ Income: €5,000
  - Salary: €4,000
  - Freelance: €1,000

- Expenses: €4,000
  - Housing: €1,500
  - Food: €800
  - Other: €1,700

± Transfers: €0

= Closing Balance: €11,000
```

---

#### R7: Net Worth Report

**Purpose:** Track total financial position

**Parameters:**

- Date range
- Include/exclude account types

**Output:**

| Date | Assets | Liabilities | Net Worth |
|------|--------|-------------|-----------|
| Jan 2026 | €15,000 | €2,000 | €13,000 |
| Feb 2026 | €16,500 | €1,800 | €14,700 |

**Visualization:** Stacked area chart

---

### 8.3 Report Requirements Summary

| Report | MVP | Priority |
|--------|-----|----------|
| Dashboard Overview | Yes | P0 |
| Income vs Expense | Yes | P0 |
| Spending by Category | Yes | P0 |
| Budget Progress | Yes | P0 |
| Category Trend | Yes | P1 |
| Account Balance History | Yes | P1 |
| Cash Flow | No | P2 |
| Net Worth Over Time | No | P2 |

---

## 9. API Contracts

### 9.1 API Overview

**Base URL:** `/api/v1`  
**Authentication:** Session-based (django-allauth) or Token  
**Format:** JSON  
**Documentation:** OpenAPI 3.0 at `/api/docs`

### 9.2 Endpoints Summary

| Resource | Endpoints |
|----------|-----------|
| Auth | `POST /auth/login`, `POST /auth/logout`, `POST /auth/register` |
| Users | `GET /users/me`, `PATCH /users/me` |
| Accounts | `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| Categories | `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| Transactions | `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| Invoices | `GET`, `POST`, `GET /{id}`, `DELETE /{id}` |
| Budgets | `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| Projects | `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` |
| Reports | `GET /reports/income-expense`, `GET /reports/by-category`, `GET /reports/projects`, etc. |

### 9.3 Common Response Formats

**Success (single item):**

```json
{
  "id": 1,
  "name": "Checking Account",
  "...": "..."
}
```

**Success (list):**

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

**Error:**

```json
{
  "detail": "Error message",
  "errors": [
    {"field": "amount", "message": "Must be positive"}
  ]
}
```

### 9.4 Detailed Endpoint Specifications

> (Define request/response schemas for each endpoint)
> (Can reference Django Ninja auto-generated docs)

---

## 10. UI/UX Specifications

### 10.1 Pages/Views

| Page | URL | Description |
|------|-----|-------------|
| Landing | `/` | Login/signup prompt or dashboard redirect |
| Dashboard | `/dashboard` | Main overview with widgets |
| Accounts | `/accounts` | List of accounts |
| Account Detail | `/accounts/{id}` | Single account with transactions |
| Transactions | `/transactions` | All transactions list |
| Transaction Form | `/transactions/new` | Create/edit transaction |
| Categories | `/categories` | Manage categories |
| Budgets | `/budgets` | Budget management |
| Projects | `/projects` | Project list and comparison |
| Project Detail | `/projects/{id}` | Single project with transactions and summary |
| Invoices | `/invoices` | Invoice list |
| Reports | `/reports` | Reports hub |
| Settings | `/settings` | User settings |

### 10.2 Key User Flows

#### Flow 1: Quick Expense Entry

``` plain text
Dashboard → "+" button → Select "Expense" →
Enter amount → Select category → Select account →
(Optional: add details) → Save → Return to dashboard
```

#### Flow 2: Invoice Upload

``` plain text
Dashboard/Invoices → "Upload" → Select file →
Wait for OCR → Review extracted data →
"Create Transaction" → Adjust fields → Save
```

#### Flow 3: Budget Check

``` plain text
Dashboard (see widget) → Click "Budgets" →
See all category budgets → Click category →
See transactions in that category
```

## 11. Non-Functional Requirements

### 11.1 Performance

| Requirement | Target |
|-------------|--------|
| Page load time | < 2 seconds |
| API response time | < 500ms (p95) |
| Report generation | < 2 seconds |
| File upload | < 10 seconds for 10MB |
| OCR processing | < 30 seconds |

### 11.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | django-allauth with session |
| Authorization | All data filtered by user_id |
| Password policy | Min 8 chars, complexity rules |
| HTTPS | Required in production |
| CSRF protection | Django default |
| SQL injection | ORM parameterized queries |
| XSS | Django template escaping |

### 11.3 Scalability

| Aspect | MVP Target |
|--------|------------|
| Users | Single user (personal use) |
| Transactions | 10,000+ per user |
| Concurrent requests | 10 |
| Data retention | Unlimited |

### 11.4 Reliability

| Requirement | Target |
|-------------|--------|
| Uptime | 99% (personal project) |
| Backup frequency | Daily |
| Recovery time | < 1 hour |

### 11.5 Compatibility

| Platform | Support |
|----------|---------|
| Chrome | Latest 2 versions |
| Firefox | Latest 2 versions |
| Safari | Latest 2 versions |
| Mobile browsers | Responsive design |

---

## 12. Future Considerations

> (Features explicitly not in MVP but planned for future)

### Phase 2 (Post-MVP)

- [ ] Bank API integration (Plaid, GoCardless)
- [ ] Recurring transactions
- [x] Mobile app (PWA or native)
- [ ] Email reports
- [ ] Data export (CSV, PDF)

### Phase 3 (Long-term)

- [x] AI-powered categorization
- [x] Financial goals tracking
- [x] Bill reminders
- [x] Multi-language support

---

## 13. Glossary

| Term | Definition |
|------|------------|
| Account | A financial container (bank account, wallet, credit card) |
| Transaction | A single financial event (income, expense, or transfer) |
| Transfer | Movement of money between two accounts |
| Category | Classification of transactions (e.g., Food, Salary) |
| Budget | Spending limit set for a category and time period |
| Project | A grouping of related transactions for tracking specific events (e.g., business trip, vacation) |
| Invoice | Uploaded receipt/bill image with OCR data |
| OCR | Optical Character Recognition - extracting text from images |
| Net Worth | Total assets minus total liabilities |
| Tenant | User - all data is scoped to a single user |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | | Evgenii | Initial draft |
