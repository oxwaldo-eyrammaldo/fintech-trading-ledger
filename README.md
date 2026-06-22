# Fintech Trading Ledger & Asset Simulator

A secure, full-stack financial portfolio simulator that enables users to manage mock asset allocations, track transactional ledger balances, and evaluate real-time market valuations by integrating live financial web endpoints.

---

## 🚀 Key Engineering Highlights

* **Transactional Integrity & Ledgers:** Engineered robust SQL schemas to handle real-time asset updates. Transactions utilize atomic balance-checking logic to completely eliminate negative-balance operations or currency duplication edge cases.
* **API Version Integration:** Integrated token-authenticated market endpoints via the **CoinCap v3 API**, parsing nested multi-layered JSON response bodies into clean, internal relational database states.
* **Defensive Web Security:** Built security layers protecting against common web vulnerabilities, incorporating rigorous parameter sanitization to prevent SQL Injections and parameter boundaries to block Insecure Direct Object References (IDOR).
* **Session & State Tracking:** Implemented server-side session management using Flask-Session, ensuring cryptographically secured client-side route access control.

---

## 🛠️ Architecture & Tech Stack

* **Backend Engine:** Python 3.x, Flask (Micro-framework)
* **Database Management:** SQLite / PostgreSQL (Relational schema modeling)
* **API Integration:** Requests (HTTP Client library)
* **Frontend UI:** HTML5, CSS3, Jinja2 Templating Engine

---

## 📂 Project Structure

```text
fintech-trading-ledger/
├── app.py                 # Core Flask routing, security logic & portfolio tracking
├── helpers.py             # Token authentication middleware & API network handlers
├── finance.db             # Relational SQL transaction and user asset databases
├── requirements.txt       # Production dependencies and web framework lockfile
├── README.md              # Project documentation
└── templates/
    ├── layout.html        # Main base UI template layout
    ├── index.html         # Portfolio dashboard showing total asset valuation
    ├── buy.html           # Validation-checked order placement engine
    └── login.html         # Secure, session-validated user authentication screen
