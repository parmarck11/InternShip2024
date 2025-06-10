from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library_001'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')     
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/users', methods=['GET'])
def get_users():    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    cur.close()

    return jsonify([{'id': user[0], 'username': user[1], 'role': user[2]} for user in users]), 20


@app.route('/login', methods=['POST'])
def login_user():
    cookie = request.cookies.get('session_id')
    if cookie:
        return jsonify({'message': 'Already logged in'}), 200
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, role FROM users WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()
    cur.close() 
    if user:
        response = jsonify({'message': 'Login successful', 'user_id': user[0], 'role': user[1]})
        response.set_cookie('session_id', str(user[0]), httponly=True)
        return response, 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
def logout_user():
    response = jsonify({'message': 'Logged out successfully'})
    response.delete_cookie('session_id')
    return response, 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    publishing_year = data.get('publishing_year')

    if not title or not author or not publishing_year:
        return jsonify({'error': 'Title, author, and publishing year are required'}), 400

    if not request.cookies.get('session_id'):
        return jsonify({'error': 'User not logged in'}), 401

    cur = mysql.connection.cursor()
    # Check if the user is an admin  
    cur.execute("SELECT role FROM users WHERE id = %s", (request.cookies.get('session_id'),))
    user = cur.fetchone()   
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    book = cur.execute("SELECT * FROM books WHERE title = %s AND author = %s", (title, author))
    if book:
        return jsonify({'error': 'Book already exists'}), 400

    cur.execute(
        "INSERT INTO books (title, author, publishing_year) VALUES (%s, %s, %s)",
        (title, author, publishing_year)
    )

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book added successfully'}), 201

@app.route('/books', methods=['GET'])
def get_books():    
    cur = mysql.connection.cursor()
    cur.execute("SELECT book_id, title, author, publishing_year FROM books")
    books = cur.fetchall()
    cur.close()

    return jsonify([{'book_id': book[0], 'title': book[1], 'author': book[2], 'publishing_year': book[3]} for book in books]), 200   

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):   
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Book deleted successfully'}), 200

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    publishing_year = data.get('publishing_year')

    if not title or not author or not publishing_year:
        return jsonify({'error': 'Title, author, and publishing year are required'}), 400

    if not request.cookies.get('session_id'):
        return jsonify({'error': 'User not logged in'}), 401

    cur = mysql.connection.cursor()
    # Check if the user is an admin  
    cur.execute("SELECT role FROM users WHERE id = %s", (request.cookies.get('session_id'),))
    user = cur.fetchone()   
    if not user or user[0] != 'admin':
        return jsonify({'error': 'Permission denied'}), 403

    cur.execute(
        "UPDATE books SET title = %s, author = %s, publishing_year = %s WHERE book_id = %s",
        (title, author, publishing_year, book_id)
    )

    mysql.connection.commit()
    cur.close()  

    return jsonify({'message': 'Book updated successfully'}), 200

@app.route('/borrow_book/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if not request.cookies.get('session_id'):
        return jsonify({'error': 'User not logged in'}), 401

     cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE id = %s", (request.cookies.get('session_id'),))
    user = cur.fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    cur.execute("SELECT * FROM borrowed_book WHERE book_id = %s AND user_id = %s", (book_id, user[0]))
    borrow_book = cur.fetchone()

    if borrow_book:
        return jsonify({'error': 'Book already borrowed by this user'}), 400

    cur.execute("INSERT INTO borrowed_book (book_id, user_id) VALUES (%s, %s)", (book_id, user[0]))

    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Book borrowed successfully'}), 201

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True) 