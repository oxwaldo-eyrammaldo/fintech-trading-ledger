import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    # Gather rows summarizing shares owned per stock symbol
    rows = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0",
        user_id
    )

    holdings = []
    total_stock_value = 0

    for row in rows:
        stock = lookup(row["symbol"])
        if stock:
            current_price = stock["price"]
            total_value = row["total_shares"] * current_price
            total_stock_value += total_value
            holdings.append({
                "symbol": row["symbol"],
                "name": stock["name"],
                "shares": row["total_shares"],
                "price": current_price,
                "total": total_value
            })

    # Query remaining liquid cash
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    grand_total = total_stock_value + user_cash

    return render_template("index.html", holdings=holdings, cash=user_cash, total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide symbol", 400)

        # Validate positive integer shares
        if not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("shares must be a positive integer", 400)

        shares = int(shares)
        stock = lookup(symbol)
        if not stock:
            return apology("invalid stock symbol", 400)

        user_id = session["user_id"]
        total_cost = stock["price"] * shares

        # Verify wallet balance
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
        if user_cash < total_cost:
            return apology("insufficient liquid funds", 400)

        # Process Transaction updates
        db.execute(
            "UPDATE users SET cash = cash - ? WHERE id = ?",
            total_cost, user_id
        )
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            user_id, stock["symbol"], shares, stock["price"]
        )

        flash(f"Successfully bought {shares} shares of {stock['symbol']}!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions = db.execute(
        "SELECT symbol, shares, price, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
        user_id
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)

        stock = lookup(symbol)
        if not stock:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", stock=stock)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        if not password or not confirmation:
            return apology("must provide password & confirmation", 400)
        if password != confirmation:
            return apology("passwords must match", 400)

        # Insert user, handling duplicate usernames using structural error catch block
        try:
            password_hash = generate_password_hash(password)
            user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, password_hash
            )
        except ValueError:
            return apology("username already exists", 400)

        # Log new user in automatically
        session["user_id"] = user_id
        flash("Registration complete!")
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must select a stock symbol", 400)

        if not shares or not shares.isdigit() or int(shares) <= 0:
            return apology("shares must be a positive integer", 400)

        shares = int(shares)

        # Track user ownership
        user_shares = db.execute(
            "SELECT SUM(shares) AS total_shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol",
            user_id, symbol
        )

        if not user_shares or user_shares[0]["total_shares"] < shares:
            return apology("you do not own that many shares", 400)

        stock = lookup(symbol)
        total_revenue = stock["price"] * shares

        # Complete sell processing
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_revenue, user_id)
        db.execute(
            "INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
            user_id, symbol, -shares, stock["price"]
        )

        flash(f"Successfully sold {shares} shares of {symbol}!")
        return redirect("/")
    else:
        # Populate selector option layout fields dynamically
        stocks = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0",
            user_id
        )
        return render_template("sell.html", stocks=stocks)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Personal Touch: Allow users to add additional cash funds to their account."""
    if request.method == "POST":
        amount = request.form.get("amount")
        if not amount or not amount.replace('.', '', 1).isdigit() or float(amount) <= 0:
            return apology("must provide valid positive cash amount", 400)

        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", float(amount), session["user_id"])
        flash(f"Added {usd(float(amount))} to your active cash reserves!")
        return redirect("/")
    else:
        return render_template("cash.html")
