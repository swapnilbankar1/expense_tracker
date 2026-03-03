# Expense Tracker - Project Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [API Endpoints](#api-endpoints)
7. [Flow Charts](#flow-charts)

---

## System Overview

The Expense Tracker is a full-stack web application that allows users to:
- Upload PDF bank/credit card statements
- Automatically extract and categorize transactions
- View monthly expense summaries with charts
- Filter and analyze spending patterns
- Track merchant-wise payments

**Architecture Pattern:** 3-Tier Architecture (Presentation → Business Logic → Data Layer)

---

## Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13 | Core programming language |
| **FastAPI** | 0.128.0 | Web framework for building APIs |
| **Uvicorn** | 0.40.0 | ASGI server for running FastAPI |
| **SQLAlchemy** | 2.0.39 | ORM for database operations |
| **PostgreSQL** | 15 | Relational database |
| **psycopg2-binary** | 2.9.11 | PostgreSQL adapter for Python |
| **pdfplumber** | 0.11.9 | PDF text extraction library |
| **Pydantic** | 2.10.3 | Data validation and serialization |
| **python-multipart** | - | File upload handling |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Angular** | 20.x | Frontend framework (standalone components) |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Chart.js** | 4.4.1 | Data visualization library |
| **ng2-charts** | 6.0.1 | Angular wrapper for Chart.js |
| **RxJS** | 7.x | Reactive programming for HTTP calls |
| **SCSS** | - | CSS preprocessor for styling |

### DevOps & Tools

| Technology | Purpose |
|------------|---------|
| **Docker Compose** | PostgreSQL containerization |
| **Git** | Version control |

---

## Backend Architecture

### Directory Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API utilities
│   │   └── upload.py           # File upload handlers
│   ├── core/                   # Core configuration
│   │   ├── config.py           # App configuration
│   │   ├── database.py         # Database connection & session
│   │   └── llm.py              # LLM integration (future use)
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── transaction.py      # Transaction table model
│   │   └── monthly_expense.py  # Monthly expense table model
│   ├── routes/                 # API route handlers
│   │   ├── statements.py       # Statement upload endpoints
│   │   ├── transactions.py     # Transaction CRUD endpoints
│   │   ├── monthly_expenses.py # Monthly expense endpoints
│   │   └── categorize.py       # Categorization endpoints
│   ├── schemas/                # Pydantic schemas (validation)
│   │   ├── transaction.py      # Transaction request/response schemas
│   │   └── monthly_expense.py  # Monthly expense schemas
│   ├── services/               # Business logic layer
│   │   ├── pdf_reader.py       # PDF parsing logic
│   │   ├── normalizer.py       # Merchant name normalization
│   │   ├── categorizer.py      # Transaction categorization
│   │   └── monthly_expense_service.py # Monthly aggregation
│   ├── scripts/                # Database scripts
│   │   └── init_db.py          # Database initialization
│   └── utils/                  # Utility functions
│       └── rules.py            # Business rules
├── data/
│   └── statements/             # Uploaded PDF storage
├── docker-compose.yml          # PostgreSQL container config
└── requirements.txt            # Python dependencies
```

### Key Backend Components

#### 1. **Database Layer** (`app/core/database.py`)
```python
# PostgreSQL connection using SQLAlchemy
DATABASE_URL = "postgresql://expense_user:expense_pass@localhost:6543/expense_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

#### 2. **Models** (ORM Tables)

**Transaction Model** (`app/models/transaction.py`):
```python
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    merchant_raw = Column(String)        # Original merchant name from PDF
    merchant_clean = Column(String)      # Normalized merchant name
    amount = Column(Float)
    category = Column(String)            # Auto-categorized
    transaction_type = Column(String)    # DEBIT or CREDIT
    source = Column(String)              # phonepe / credit_card
```

**MonthlyExpense Model** (`app/models/monthly_expense.py`):
```python
class MonthlyExpense(Base):
    __tablename__ = "monthly_expenses"
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    month = Column(Integer)
    category = Column(String)
    total_amount = Column(Float)
    transaction_count = Column(Integer)
    source = Column(String)
```

#### 3. **Services** (Business Logic)

**PDF Reader** (`app/services/pdf_reader.py`):
- Extracts text from PDF using `pdfplumber`
- Supports multiple formats:
  - PhonePe: `Oct 28, 2025  Merchant  DEBIT  ₹1,234.56`
  - Credit Card: `DD/MM/YYYY  Merchant  1,234.56`
- Uses regex patterns to parse transactions
- Returns list of dictionaries with transaction data

**Normalizer** (`app/services/normalizer.py`):
- Cleans merchant names (removes numbers, special chars)
- Standardizes formatting
- Example: "Swiggy #12345" → "Swiggy"

**Categorizer** (`app/services/categorizer.py`):
- Rule-based categorization using merchant keywords
- Categories: Food, Transport, Shopping, Entertainment, Utilities
- Uses merchant name and amount to determine category

**Monthly Expense Service** (`app/services/monthly_expense_service.py`):
- Aggregates transactions by year/month/category
- Calculates totals and counts
- Syncs data to monthly_expenses table

#### 4. **Routes** (API Endpoints)

**Statements Route** (`app/routes/statements.py`):
- `POST /statements/upload` - Upload PDF statement
  - Saves PDF to disk
  - Extracts transactions
  - Checks for duplicates
  - Inserts into database
  - Syncs monthly expenses

**Transactions Route** (`app/routes/transactions.py`):
- `GET /transactions` - List all transactions with filters
- `GET /transactions/by-merchant` - Merchant-wise aggregation

**Monthly Expenses Route** (`app/routes/monthly_expenses.py`):
- `POST /monthly-expenses/upload-pdf` - Upload and get summary
- `GET /monthly-expenses/summary` - Get monthly summary
- `GET /monthly-expenses/categories` - Get category breakdown

#### 5. **CORS Configuration** (`app/main.py`)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Frontend Architecture

### Directory Structure
```
frontend/src/app/
├── app.ts                      # Main app component
├── app.routes.ts               # Route configuration
├── components/
│   ├── dashboard/              # Dashboard with charts
│   │   ├── dashboard.component.ts
│   │   ├── dashboard.component.html
│   │   └── dashboard.component.scss
│   ├── upload/                 # PDF upload interface
│   │   ├── upload.component.ts
│   │   ├── upload.component.html
│   │   └── upload.component.scss
│   ├── transactions/           # Transaction list with filters
│   │   ├── transactions.component.ts
│   │   ├── transactions.component.html
│   │   └── transactions.component.scss
│   └── monthly-expenses/       # Monthly expense cards
│       ├── monthly-expenses.component.ts
│       ├── monthly-expenses.component.html
│       └── monthly-expenses.component.scss
├── services/
│   └── expense.service.ts      # HTTP service for API calls
└── models/
    ├── transaction.model.ts    # TypeScript interfaces
    └── monthly-expense.model.ts
```

### Key Frontend Components

#### 1. **Routing** (`app.routes.ts`)
```typescript
routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'upload', component: UploadComponent },
  { path: 'transactions', component: TransactionsComponent },
  { path: 'monthly-expenses', component: MonthlyExpensesComponent }
]
```

#### 2. **Expense Service** (`services/expense.service.ts`)
- Centralized HTTP client for all API calls
- Methods:
  - `getTransactions()` - Fetch transactions
  - `getMonthlyExpenseSummary()` - Get monthly data
  - `uploadPDFAndGetSummary()` - Upload PDF file
  - `getTransactionsByMerchant()` - Get merchant stats

#### 3. **Components**

**Dashboard Component**:
- Shows 4 stat cards (total expenses, this month, transactions, top category)
- 3 quick action cards for navigation
- Line chart for monthly trends
- Pie chart for category breakdown
- Bar chart for top merchants

**Upload Component**:
- Drag-and-drop file upload
- File selection via button
- Displays upload progress
- Shows success/error messages
- Displays duplicate count

**Transactions Component**:
- Filterable transaction table
- Filters: Month, Category, Merchant, Date range
- Shows transaction type badges (DEBIT/CREDIT)
- Color-coded amounts
- Merchant pie chart
- Month statistics
- Pagination (50 items per page)

**Monthly Expenses Component**:
- Month-wise expense cards
- Expandable to show individual transactions
- Filter by year/category
- Upload button for quick access

#### 4. **State Management**
- Uses Angular Signals for reactive state
- No external state management library needed
- Example:
```typescript
transactions = signal<Transaction[]>([]);
loading = signal(true);
filteredTransactions = computed(() => /* filter logic */);
```

---

## Data Flow

### Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER ACTION                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Component (upload.component.ts)                           │ │
│  │  - User selects/drops PDF file                             │ │
│  │  - Calls expenseService.uploadPDFAndGetSummary()           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  HTTP Service (expense.service.ts)                         │ │
│  │  - Creates FormData with file                              │ │
│  │  - POST to http://127.0.0.1:8000/monthly-expenses/upload  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP Request
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Route Handler (monthly_expenses.py)                       │ │
│  │  @router.post("/upload-pdf")                               │ │
│  │  - Validates PDF file                                      │ │
│  │  - Saves to disk (data/statements/)                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PDF Reader Service (pdf_reader.py)                        │ │
│  │  - Opens PDF with pdfplumber                               │ │
│  │  - Extracts text from each page                            │ │
│  │  - Parses with regex patterns:                             │ │
│  │    • PhonePe: Oct 28, 2025 Merchant DEBIT ₹1,234.56       │ │
│  │    • Credit Card: DD/MM/YYYY Merchant 1,234.56             │ │
│  │  - Returns list of transaction dicts                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Processing Loop (for each transaction)                    │ │
│  │  1. Normalize merchant name (normalizer.py)                │ │
│  │     "Swiggy #12345" → "Swiggy"                             │ │
│  │  2. Categorize transaction (categorizer.py)                │ │
│  │     "Swiggy" → "Food"                                       │ │
│  │  3. Check for duplicates (compare date+merchant+amount)    │ │
│  │  4. Create Transaction object                               │ │
│  │  5. Add to database session                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Database Operations                                        │ │
│  │  - db.commit() - Save all transactions                     │ │
│  │  - sync_monthly_expenses() - Aggregate by month/category   │ │
│  │  - get_monthly_summary() - Fetch summary data              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Response (PDFUploadResponse)                              │ │
│  │  {                                                          │ │
│  │    "message": "Statement processed",                       │ │
│  │    "transactions_inserted": 45,                            │ │
│  │    "duplicates_skipped": 3,                                │ │
│  │    "monthly_summary": [...]                                │ │
│  │  }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ JSON Response
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Component (upload.component.ts)                           │ │
│  │  - Receives response                                        │ │
│  │  - Updates UI with results                                  │ │
│  │  - Shows success message                                    │ │
│  │  - Displays transaction count and duplicates                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER SEES                                │
│  ✓ Statement uploaded successfully                              │
│  📊 45 transactions inserted                                     │
│  🔄 3 duplicates skipped                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Statement Upload
```http
POST /statements/upload
Content-Type: multipart/form-data

Request Body: PDF file
Response: {
  "message": "Statement processed",
  "transactions_inserted": 45,
  "duplicates_skipped": 3
}
```

### Monthly Expenses Upload
```http
POST /monthly-expenses/upload-pdf
Content-Type: multipart/form-data

Request Body: PDF file
Response: {
  "message": "PDF uploaded successfully",
  "transactions_inserted": 45,
  "duplicates_skipped": 3,
  "monthly_summary": [
    {
      "year": 2025,
      "month": 10,
      "month_name": "October",
      "total_amount": 12500.50,
      "transaction_count": 23,
      "categories": [...]
    }
  ]
}
```

### Get Transactions
```http
GET /transactions?category=Food&limit=500&offset=0

Response: [
  {
    "id": 1,
    "date": "2025-10-28",
    "merchant_raw": "Swiggy #12345",
    "merchant_clean": "Swiggy",
    "amount": 450.00,
    "category": "Food",
    "transaction_type": "DEBIT",
    "source": "phonepe"
  }
]
```

### Get Merchant Aggregation
```http
GET /transactions/by-merchant

Response: [
  {
    "merchant": "Swiggy",
    "total_amount": 4500.00,
    "transaction_count": 12,
    "average_amount": 375.00
  }
]
```

### Get Monthly Summary
```http
GET /monthly-expenses/summary?year=2025&month=10

Response: [
  {
    "year": 2025,
    "month": 10,
    "month_name": "October",
    "total_amount": 25000.00,
    "transaction_count": 45,
    "categories": [
      {
        "category": "Food",
        "total_amount": 8000.00,
        "transaction_count": 20
      }
    ]
  }
]
```

---

## Flow Charts

### 1. PDF Upload and Processing Flow

```
┌─────────────┐
│   START     │
│ User Clicks │
│  Upload     │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Select PDF File  │
│ (Drag or Browse) │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│ Frontend Validation      │
│ - Check file type (.pdf) │
│ - Check file size        │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ HTTP POST Request        │
│ FormData with PDF file   │
│ → Backend API            │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Backend: Receive File    │
│ - Validate PDF           │
│ - Save to disk           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Extract Text from PDF    │
│ using pdfplumber         │
│ - Loop through pages     │
│ - Extract text           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Parse Each Line          │
│ - Try PhonePe format     │
│ - Try Credit Card format │
│ - Extract: date, merchant│
│   amount, type           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ For Each Transaction:    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 1. Normalize Merchant    │
│    "Swiggy #123" → "Swiggy"│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 2. Categorize            │
│    "Swiggy" → "Food"     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 3. Check Duplicate       │
│ Query DB for:            │
│ - Same date              │
│ - Same merchant          │
│ - Same amount            │
└──────┬───────────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼ YES             ▼ NO
┌─────────────┐   ┌──────────────┐
│   Skip      │   │ Insert to DB │
│ Duplicate   │   │ transactions │
│ Count++     │   │ table        │
└─────────────┘   └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Inserted    │
                  │  Count++     │
                  └──────────────┘
                         │
       ┌─────────────────┘
       │
       ▼
┌──────────────────────────┐
│ All Transactions Done?   │
└──────┬───────────────────┘
       │ YES
       ▼
┌──────────────────────────┐
│ Commit to Database       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Sync Monthly Expenses    │
│ - Group by year/month    │
│ - Calculate totals       │
│ - Update monthly_expenses│
│   table                  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Get Monthly Summary      │
│ - Fetch aggregated data  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Return JSON Response     │
│ - transactions_inserted  │
│ - duplicates_skipped     │
│ - monthly_summary        │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Frontend: Update UI      │
│ - Show success message   │
│ - Display counts         │
│ - Refresh data           │
└──────┬───────────────────┘
       │
       ▼
┌─────────────┐
│     END     │
└─────────────┘
```

### 2. Transaction Filtering Flow (Frontend)

```
┌─────────────┐
│   START     │
│ User Opens  │
│Transactions │
│    Page     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ Component ngOnInit()     │
│ - Call loadTransactions()│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ HTTP GET /transactions   │
│ ?limit=500               │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Receive Data from API    │
│ - Store in signal        │
│ - Extract categories     │
│ - Extract months         │
│ - Build merchant chart   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Display Initial View     │
│ - All transactions       │
│ - Filter dropdowns       │
│ - Summary stats          │
│ - Charts                 │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ User Selects Filter      │
│ (Month/Category/Merchant)│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ applyFilters() triggered │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Filter Logic:            │
│ 1. Month Filter          │
│    - Extract year/month  │
│    - Filter by date      │
│ 2. Category Filter       │
│    - Match category      │
│ 3. Merchant Filter       │
│    - Search in name      │
│ 4. Date Range            │
│    - Filter start/end    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Update Signals           │
│ - filteredTransactions   │
│ - merchantChartData      │
│ - Reset pagination       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Re-render View           │
│ - Updated table          │
│ - Updated chart          │
│ - Updated summary        │
└──────┬───────────────────┘
       │
       ▼
┌─────────────┐
│  User Sees  │
│  Filtered   │
│   Results   │
└─────────────┘
```

### 3. Database Schema Relationship

```
┌─────────────────────────────────────────┐
│          transactions                   │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ date                                    │
│ merchant_raw                            │
│ merchant_clean                          │
│ amount                                  │
│ category                                │
│ transaction_type (DEBIT/CREDIT)         │
│ source (phonepe/credit_card)            │
└────────────┬────────────────────────────┘
             │
             │ Aggregated by
             │ sync_monthly_expenses()
             │
             ▼
┌─────────────────────────────────────────┐
│         monthly_expenses                │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ year                                    │
│ month                                   │
│ category                                │
│ total_amount (SUM)                      │
│ transaction_count (COUNT)               │
│ source                                  │
└─────────────────────────────────────────┘
```

---

## Key Features Implementation

### 1. Duplicate Detection
```python
# Check if transaction already exists
existing = db.query(Transaction).filter(
    Transaction.date == transaction_date,
    Transaction.merchant_raw == t["description"],
    Transaction.amount == transaction_amount
).first()

if existing:
    duplicates += 1
    continue
```

### 2. Merchant Normalization
```python
def normalize_merchant(merchant: str) -> str:
    # Remove numbers and special characters
    merchant = re.sub(r'[0-9#@*]', '', merchant)
    # Remove extra spaces
    merchant = ' '.join(merchant.split())
    return merchant.strip()
```

### 3. Auto-Categorization
```python
def categorize(transaction: dict) -> str:
    merchant = transaction["merchant_clean"].lower()
    
    food_keywords = ["swiggy", "zomato", "restaurant", "cafe"]
    if any(kw in merchant for kw in food_keywords):
        return "Food"
    # ... more categories
```

### 4. Monthly Aggregation
```python
# SQLAlchemy group by query
results = db.query(
    Transaction.year,
    Transaction.month,
    Transaction.category,
    func.sum(Transaction.amount).label('total_amount'),
    func.count(Transaction.id).label('transaction_count')
).group_by(
    Transaction.year, 
    Transaction.month, 
    Transaction.category
).all()
```

---

## Performance Considerations

1. **Pagination**: Frontend limits to 50 transactions per page
2. **Backend Limit**: API enforces max 1000 transactions per request
3. **Duplicate Detection**: Indexed on (date, merchant_raw, amount)
4. **Chart Optimization**: Shows top 10 merchants only
5. **Lazy Loading**: Month transactions loaded on-demand

---

## Future Enhancements

- [ ] Machine learning-based categorization
- [ ] Multi-currency support
- [ ] Budget planning and alerts
- [ ] Export to Excel/CSV
- [ ] Receipt image attachment
- [ ] Mobile app (React Native)
- [ ] Real-time sync with bank APIs

---

## Development Setup

### Backend
```bash
cd backend
docker-compose up -d  # Start PostgreSQL
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
ng serve --port 4200
```

### Database Migration
```bash
python -m app.scripts.init_db
```

---

## Conclusion

This architecture provides a scalable, maintainable foundation for expense tracking with:
- ✅ Clean separation of concerns (3-tier architecture)
- ✅ Type safety (TypeScript + Pydantic)
- ✅ Reactive UI (Angular Signals)
- ✅ Efficient data processing (SQLAlchemy ORM)
- ✅ Flexible PDF parsing (Multiple format support)
- ✅ Real-time visualization (Chart.js)

The modular design allows easy extension for new features and statement formats.
