# Projektübersicht

## 📋 Gesamtstruktur

```
Kassensoftware/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                      # REST API Router
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── user.py              # User management
│   │   │   ├── member.py            # Member management
│   │   │   ├── product.py           # Product management
│   │   │   └── transaction.py       # Transaction/Sales endpoints
│   │   ├── services/                 # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── member_service.py
│   │   │   ├── product_service.py
│   │   │   └── transaction_service.py
│   │   ├── repositories/             # Database Access
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── member_repository.py
│   │   │   ├── product_repository.py
│   │   │   └── transaction_repository.py
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base model with ID
│   │   │   ├── user.py              # User model
│   │   │   ├── member.py            # Member model
│   │   │   ├── product.py           # Product model
│   │   │   ├── transaction.py       # Transaction & Items models
│   │   │   └── balance_log.py       # Balance history
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── member.py
│   │   │   ├── product.py
│   │   │   └── transaction.py
│   │   └── core/                     # Configuration & Security
│   │       ├── __init__.py
│   │       ├── config.py            # Settings from environment
│   │       ├── database.py          # Database session & connection pool
│   │       ├── security.py          # Password hashing (bcrypt)
│   │       └── auth.py              # Session auth helpers
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables (local)
│   └── .env.example                  # Environment template
│
├── frontend/                         # Vue 3 + Vite Frontend
│   ├── src/
│   │   ├── components/               # Reusable Vue components
│   │   │   └── (reserved for future)
│   │   ├── views/
│   │   │   ├── Login.vue            # Login page
│   │   │   ├── kasse/
│   │   │   │   └── Kasse.vue        # Main POS system view
│   │   │   └── admin/
│   │   │       ├── Admin.vue        # Admin dashboard
│   │   │       ├── Members.vue      # Member management
│   │   │       ├── Products.vue     # Product management
│   │   │       └── Users.vue        # User management
│   │   ├── stores/                   # Pinia state management
│   │   │   ├── auth.js             # Authentication store
│   │   │   ├── product.js          # Products store
│   │   │   ├── member.js           # Members store
│   │   │   ├── cart.js             # Shopping cart
│   │   │   └── notification.js     # Notifications
│   │   ├── services/
│   │   │   ├── api.js              # Axios API client
│   │   │   └── utils.js            # Utility functions (formatPrice, etc)
│   │   ├── router/
│   │   │   └── index.js            # Vue Router configuration
│   │   ├── styles/
│   │   │   └── main.scss           # Global styles
│   │   ├── App.vue                  # Root component
│   │   └── main.js                  # Vue app entry point
│   ├── public/
│   │   ├── manifest.json           # PWA manifest
│   │   ├── sw.js                   # Service Worker
│   │   └── (icon-192.png, icon-512.png - placeholder)
│   ├── index.html                   # HTML template
│   ├── vite.config.js              # Vite configuration
│   ├── package.json                # NPM dependencies
│   └── .gitignore                  # Git ignore rules
│
├── Documentation Files
│   ├── README.md                    # Main documentation
│   ├── SETUP.md                     # Setup guide
│   ├── ARCHITECTURE.md              # Technical architecture
│   ├── .env.example                 # Environment template
│   └── this file
│
├── Automation Scripts
│   ├── setup-dev.sh                # Local dev setup
│   ├── deploy-production.sh         # Production deployment
│   ├── docker-compose.yml           # Docker reference (NOT REQUIRED)
│   └── test-api.py                  # API test script
│
└── .gitignore                       # Git ignore rules
```

## 🗄️ Datenbank-Schema

### Users
```sql
id (PK) | username (UNIQUE) | email (UNIQUE) | password_hash | role (ENUM: ADMIN/CASHIER) | is_active | created_at | updated_at
```

### Members
```sql
id (PK) | name | email (UNIQUE, nullable) | phone | balance_cents | photo (BLOB) | notes | created_at | updated_at
```

### Products
```sql
id (PK) | name | description | price_cents | member_price_cents | is_discountable | stock_quantity | image | is_active | created_at | updated_at
```

### Transactions
```sql
id (PK) | type (ENUM: SALE/STORNO/RECHARGE) | payment_method (ENUM: CASH/BALANCE) | total_amount_cents | user_id (FK) | member_id (FK, nullable) | reference_transaction_id (FK, nullable) | created_at | updated_at
```

### TransactionItems
```sql
id (PK) | transaction_id (FK) | product_id (FK) | quantity | unit_price_cents | total_price_cents | created_at
```

### BalanceLogs
```sql
id (PK) | member_id (FK) | transaction_id (FK, nullable) | old_balance_cents | new_balance_cents | change_cents | reason | created_at
```

## 🔌 API Endpoints Summary

### Auth
- `POST   /api/auth/login`           - Login
- `POST   /api/auth/logout`          - Logout
- `GET    /api/auth/me`              - Current user

### Users (Admin Only)
- `GET    /api/users`                - List all
- `POST   /api/users`                - Create
- `GET    /api/users/{id}`           - Get one
- `PUT    /api/users/{id}`           - Update
- `DELETE /api/users/{id}`           - Delete

### Members
- `GET    /api/members`              - List all
- `POST   /api/members`              - Create
- `GET    /api/members/{id}`         - Get one
- `PUT    /api/members/{id}`         - Update
- `POST   /api/members/{id}/recharge` - Recharge balance
- `DELETE /api/members/{id}`         - Delete

### Products
- `GET    /api/products`             - List all
- `POST   /api/products`             - Create
- `GET    /api/products/{id}`        - Get one
- `PUT    /api/products/{id}`        - Update
- `POST   /api/products/{id}/adjust-stock` - Adjust stock
- `DELETE /api/products/{id}`        - Delete (soft)

### Transactions
- `POST   /api/transactions/sale`           - Create sale
- `POST   /api/transactions/storno`         - Create storno
- `GET    /api/transactions/{id}`           - Get one
- `GET    /api/transactions`                - List (with pagination)
- `GET    /api/transactions/daily-summary`  - Z-Bon

## 🚀 Quick Start Commands

### Local Development

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Production

```bash
# On Linux server
sudo bash deploy-production.sh
```

## 📊 Key Features Implemented

✓ User Management (Admin/Cashier)
✓ Member Management with Balance
✓ Product Management with Stock
✓ Transaction Recording (Sales)
✓ Storno System (Reversals)
✓ Balance Management (Audit Trail)
✓ Z-Bon (Daily Summary)
✓ Session-based Authentication
✓ Password Hashing (bcrypt)
✓ PWA Support
✓ Touch-optimized UI
✓ Responsive Design
✓ API Documentation (Swagger)

## 🔐 Security Features

- bcrypt password hashing (12 rounds)
- Session-based authentication
- CORS configured
- Role-based access control (ADMIN/CASHIER)
- No sensitive data in logs
- SQL prepared statements (SQLAlchemy)
- Session cookie security

## 📱 PWA Features

- Offline caching (HTML/CSS/JS)
- Installable on tablets
- Service Worker support
- Manifest.json configuration
- Touch-optimized interface

## 🐛 Development

### Run Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### API Documentation
Open: http://localhost:8000/docs (when running locally)

### Test API Endpoints
```bash
python3 test-api.py
```

## ⚙️ Configuration

### Environment Variables (Backend)
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=long-random-string-for-sessions
```

### Environment Variables (Frontend)
```
VITE_API_URL=http://localhost:8000/api
```

## 🎯 Next Steps

1. ✓ Database Setup (PostgreSQL)
2. ✓ Backend API Implementation
3. ✓ Frontend UI Implementation
4. ✓ Authentication System
5. ✓ Payment Processing
6. Test & Debug (ongoing)
7. Production Deployment

## 📞 Support

For issues or questions, check:
- README.md for general info
- SETUP.md for setup help
- ARCHITECTURE.md for technical details
- API docs at /docs endpoint

---

**Status: ✓ READY FOR LOCAL DEPLOYMENT**

Das System ist vollständig funktionsfähig und kann lokal auf Linux ohne Docker gestartet werden!
