from email.mime import image

from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key ="campus_store_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'rootanjali123'
app.config['MYSQL_DB'] = 'campus_store'

mysql = MySQL(app)
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    print("LOGIN PAGE OPENED")

    if request.method == 'POST':

        print("FORM SUBMITTED")

        email = request.form['email']
        password = request.form['password']

        print("EMAIL =", email)

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        print("USER =", user)

        cur.close()

        if user and check_password_hash(user[3], password):

            print("LOGIN SUCCESS")

            session['user_id'] = user[0]
            session['user_name'] = user[1]

            print("SESSION =", session)

            return redirect('/products')

        print("LOGIN FAILED")

        return "Invalid Email or Password"

    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['fullname']
        email = request.form['email']

        # Hash password here
        password = generate_password_hash(
            request.form['password']
        )

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(%s,%s,%s)
            """,
            (name,email,password)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template('register.html')
@app.route('/products')
def products():

    search = request.args.get('search')

    cur = mysql.connection.cursor()

    if search:

        cur.execute(
            """
            SELECT * FROM products
            WHERE name LIKE %s
            """,
            ('%' + search + '%',)
        )

    else:

        cur.execute(
            "SELECT * FROM products"
        )

    products = cur.fetchall()

    cur.close()

    return render_template(
        'products.html',
        products=products
    )
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    if request.method == 'POST':

        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']
        stock = request.form['stock']
        image = request.files['image']

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )
        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO products
            (name, category, price, description, stock, image)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (name, category, price, description, stock, filename)
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/products')

    return render_template('add_product.html')
@app.route('/delete_product/<int:id>')
def delete_product(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM products WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/products')
@app.route('/product/<int:id>')
def product_details(id):

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT *
        FROM products
        WHERE id=%s
        """,
        (id,)
    )

    product = cur.fetchone()

    cur.close()

    return render_template(
        'product_details.html',
        product=product
    )
@app.route('/cart')
def cart():

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
            products.name,
            products.price,
            cart.quantity

        FROM cart

        JOIN products
        ON cart.product_id = products.id

        WHERE cart.user_id=%s
        """,
        (user_id,)
    )

    items = cur.fetchall()

    cur.close()

    return render_template(
        'cart.html',
        items=items
    )
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    user_id = session.get('user_id')

    if not user_id:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO cart
        (user_id, product_id, quantity)
        VALUES (%s, %s, %s)
        """,
        (user_id, id, 1)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/cart')
@app.route('/checkout', methods=['GET','POST'])
def checkout():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if request.method == 'POST':

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT SUM(products.price * cart.quantity)
            FROM cart
            JOIN products
            ON cart.product_id = products.id
            WHERE cart.user_id=%s
            """,
            (user_id,)
        )

        total = cur.fetchone()[0]

        if total is None:
            total = 0

        cur.execute(
            """
            INSERT INTO orders
            (user_id,total)
            VALUES(%s,%s)
            """,
            (user_id,total)
        )

        cur.execute(
            """
            DELETE FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/orders')

    return render_template('checkout.html')
@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    orders = cur.fetchall()

    cur.close()

    return render_template(
        'orders.html',
        orders=orders
    )
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')
@app.route('/admin')
def admin():

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products")
    products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    cur.close()

    return render_template(
        'admin_dashboard.html',
        users=users,
        products=products,
        orders=orders
    )

@app.route('/edit_product/<int:id>', methods=['GET','POST'])
def edit_product(id):

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        name = request.form['name']
        price = request.form['price']

        cur.execute(
            """
            UPDATE products
            SET name=%s,
                price=%s
            WHERE id=%s
            """,
            (name,price,id)
        )

        mysql.connection.commit()

        return redirect('/products')

    cur.execute(
        """
        SELECT *
        FROM products
        WHERE id=%s
        """,
        (id,)
    )

    product = cur.fetchone()

    return render_template(
        'edit_product.html',
        product=product
    )
@app.route('/wishlist/<int:id>')
def wishlist(id):

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO wishlist
        (user_id,product_id)
        VALUES(%s,%s)
        """,
        (user_id,id)
    )

    mysql.connection.commit()

    return redirect('/products')
if __name__ == '__main__':
    app.run(debug=True)