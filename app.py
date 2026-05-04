# app.py - Vercel-compatible POS System Backend
from flask import Flask, redirect, request, jsonify, session, render_template
from datetime import datetime, timedelta
import json
import os
from functools import wraps
from abc import ABC, abstractmethod

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'

# ========== USE IN-MEMORY STORAGE FOR VERCEL ==========
class InMemoryDataStorage:
    """In-memory storage for Vercel serverless environment"""
    
    def __init__(self):
        # Initialize with default data
        self._data = {
            'products': [
                {"id": 1, "name": "Gaming Laptop", "price": 45000, "stock": 10, "sales": 0},
                {"id": 2, "name": "Wireless Mouse", "price": 500, "stock": 50, "sales": 0},
                {"id": 3, "name": "Mechanical Keyboard", "price": 1200, "stock": 30, "sales": 0},
                {"id": 4, "name": "27-inch Monitor", "price": 8500, "stock": 15, "sales": 0},
                {"id": 5, "name": "USB-C Cable", "price": 150, "stock": 100, "sales": 0},
                {"id": 6, "name": "Gaming Headset", "price": 2500, "stock": 25, "sales": 0}
            ],
            'transactions': []
        }
        self._next_product_id = 7
    
    def load_data(self):
        return self._data
    
    def save_data(self, data):
        self._data = data
    
    def get_products(self):
        return self._data.get('products', [])
    
    def get_transactions(self):
        return self._data.get('transactions', [])
    
    def update_product_stock(self, product_id, quantity_sold):
        for product in self._data['products']:
            if product['id'] == product_id:
                product['stock'] -= quantity_sold
                product['sales'] = product.get('sales', 0) + quantity_sold
                break
    
    def add_transaction(self, transaction):
        self._data['transactions'].insert(0, transaction)
    
    def add_product(self, product):
        product['id'] = self._next_product_id
        self._next_product_id += 1
        self._data['products'].append(product)
        return product
    
    def update_product(self, product_id, updated_data):
        for product in self._data['products']:
            if product['id'] == product_id:
                product.update(updated_data)
                break
    
    def delete_product(self, product_id):
        self._data['products'] = [p for p in self._data['products'] if p['id'] != product_id]

# ========== AUTHENTICATION MANAGER ==========
class AuthManager:
    def __init__(self):
        self.__users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'user': {'password': 'user123', 'role': 'user'}
        }
    
    def authenticate(self, username, password):
        if username in self.__users and self.__users[username]['password'] == password:
            return True, self.__users[username]['role']
        return False, None

# ========== CART MANAGER ==========
class CartManager:
    def __init__(self, session):
        self.session = session
    
    def get_cart(self):
        return self.session.get('cart', [])
    
    def set_cart(self, cart):
        self.session['cart'] = cart
    
    def add_item(self, product_id, name, price, quantity, available_stock):
        cart = self.get_cart()
        existing = next((item for item in cart if item['id'] == product_id), None)
        
        if existing:
            if existing['quantity'] + quantity <= available_stock:
                existing['quantity'] += quantity
                self.set_cart(cart)
                return True, f'Added {quantity} more {name}'
            else:
                return False, f'Only {available_stock - existing["quantity"]} more available!'
        else:
            if quantity <= available_stock:
                cart.append({
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'quantity': quantity
                })
                self.set_cart(cart)
                return True, f'Added {name} to cart'
            else:
                return False, f'Only {available_stock} units available!'
    
    def remove_item(self, product_id):
        cart = self.get_cart()
        cart = [item for item in cart if item['id'] != product_id]
        self.set_cart(cart)
        return True
    
    def update_quantity(self, product_id, quantity, available_stock):
        cart = self.get_cart()
        item = next((i for i in cart if i['id'] == product_id), None)
        
        if item:
            if quantity > 0 and quantity <= available_stock:
                item['quantity'] = quantity
                self.set_cart(cart)
                return True, 'Quantity updated'
            elif quantity == 0:
                return self.remove_item(product_id), 'Item removed'
        return False, 'Invalid operation'
    
    def clear_cart(self):
        self.session['cart'] = []
    
    def calculate_subtotal(self):
        cart = self.get_cart()
        return sum(item['price'] * item['quantity'] for item in cart)

# ========== RECEIPT GENERATOR ==========
class ReceiptGenerator:
    @staticmethod
    def generate_receipt_text(transaction_dict):
        date = datetime.fromisoformat(transaction_dict['date'])
        receipt = []
        receipt.append("╔════════════════════════════════════════╗")
        receipt.append("║           MODERN POS SYSTEM            ║")
        receipt.append("║        123 Business Street, City       ║")
        receipt.append("╚════════════════════════════════════════╝")
        receipt.append("")
        receipt.append(f"Transaction #: {transaction_dict['id']}")
        receipt.append(f"Date: {date.strftime('%Y-%m-%d')}")
        receipt.append(f"Time: {date.strftime('%H:%M:%S')}")
        receipt.append(f"Cashier: {transaction_dict.get('cashier', 'POS User')}")
        receipt.append("─────────────────────────────────────────")
        receipt.append("")
        receipt.append("ITEMS:")
        
        for item in transaction_dict['items']:
            receipt.append(f"{item['name']}")
            receipt.append(f"  {item['quantity']} x ₱{item['price']:,.2f} = ₱{(item['price'] * item['quantity']):,.2f}")
        
        receipt.append("")
        receipt.append("─────────────────────────────────────────")
        receipt.append(f"Subtotal:                    ₱{transaction_dict['subtotal']:,.2f}")
        
        if transaction_dict.get('discount_amount', 0) > 0:
            receipt.append(f"Discount:                     -₱{transaction_dict['discount_amount']:,.2f}")
        
        receipt.append(f"TOTAL:                       ₱{transaction_dict['total']:,.2f}")
        receipt.append(f"Cash Payment:                ₱{transaction_dict['payment']:,.2f}")
        receipt.append(f"Change:                      ₱{transaction_dict['change']:,.2f}")
        receipt.append("═════════════════════════════════════════")
        receipt.append("          THANK YOU FOR SHOPPING!")
        receipt.append("            Please come again!")
        receipt.append("═════════════════════════════════════════")
        
        return "\n".join(receipt)

# ========== POS CONTROLLER ==========
class POSController:
    def __init__(self):
        self.storage = InMemoryDataStorage()
        self.auth_manager = AuthManager()
        self.receipt_generator = ReceiptGenerator()
    
    def get_products(self):
        return self.storage.get_products()
    
    def add_product(self, name, price, stock):
        new_product = {
            'name': name,
            'price': float(price),
            'stock': int(stock),
            'sales': 0
        }
        return self.storage.add_product(new_product)
    
    def update_product(self, product_id, name, price, stock):
        self.storage.update_product(product_id, {
            'name': name,
            'price': float(price),
            'stock': int(stock)
        })
        return True
    
    def delete_product(self, product_id):
        self.storage.delete_product(product_id)
        return True
    
    def process_payment(self, cart_manager, discount_data, payment_amount, username):
        cart_items = cart_manager.get_cart()
        
        if not cart_items:
            return False, "Cart is empty!", None
        
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        
        discount_amount = 0
        if discount_data and discount_data.get('type') == 'percentage':
            discount_amount = (subtotal * discount_data['value']) / 100
        
        total = subtotal - discount_amount
        
        if payment_amount < total:
            return False, f"Insufficient payment! Need ₱{total - payment_amount:,.2f}", None
        
        # Update stock
        for cart_item in cart_items:
            self.storage.update_product_stock(cart_item['id'], cart_item['quantity'])
        
        # Create transaction
        transaction = {
            'id': int(datetime.now().timestamp() * 1000),
            'date': datetime.now().isoformat(),
            'items': cart_items,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total': total,
            'payment': payment_amount,
            'change': payment_amount - total,
            'cashier': username
        }
        
        self.storage.add_transaction(transaction)
        cart_manager.clear_cart()
        receipt = self.receipt_generator.generate_receipt_text(transaction)
        
        return True, f"Transaction successful! Change: ₱{transaction['change']:,.2f}", receipt
    
    def get_all_transactions(self):
        return self.storage.get_transactions()
    
    def get_transaction_by_id(self, transaction_id):
        transactions = self.storage.get_transactions()
        for transaction in transactions:
            if transaction['id'] == transaction_id:
                return transaction
        return None
    
    def get_analytics(self):
        transactions = self.storage.get_transactions()
        products = self.storage.get_products()
        
        total_revenue = sum(t['total'] for t in transactions)
        total_transactions = len(transactions)
        
        return {
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'total_products': len(products),
            'low_stock_products': [p for p in products if p['stock'] < 10]
        }
    
    def get_daily_revenue(self, date_str):
        """Get revenue for a specific date (YYYY-MM-DD)"""
        transactions = self.storage.get_transactions()
        total = 0
        for t in transactions:
            trans_date = datetime.fromisoformat(t['date']).strftime('%Y-%m-%d')
            if trans_date == date_str:
                total += t['total']
        return total

# ========== FLASK ROUTES ==========
pos_controller = POSController()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== PAGE ROUTES ==========
@app.route('/')
def index():
    if 'username' in session:
        return render_template('dashboard.html')
    return render_template('login.html')

@app.route('/login')
def login_page():
    if 'username' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/feature1')
@login_required
def feature1():
    return render_template('salestransaction.html')

@app.route('/feature2')
@login_required
def feature2():
    return render_template('receiptgenerationsforcustomers.html')

@app.route('/feature3')
@login_required
def feature3():
    return render_template('salessummaryandreporting.html')

@app.route('/products')
@admin_required
def products_page():
    return render_template('products.html')

@app.route('/history')
@admin_required
def history_page():
    return render_template('history.html')

# ========== API ROUTES ==========
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    success, role = pos_controller.auth_manager.authenticate(username, password)
    
    if success:
        session['username'] = username
        session['role'] = role
        return jsonify({'success': True, 'username': username, 'role': role})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth', methods=['GET'])
def api_check_auth():
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username'],
            'role': session['role']
        })
    return jsonify({'authenticated': False})

@app.route('/api/products', methods=['GET'])
@login_required
def api_get_products():
    return jsonify(pos_controller.get_products())

@app.route('/api/products', methods=['POST'])
@admin_required
def api_add_product():
    data = request.json
    product = pos_controller.add_product(
        data.get('name'),
        data.get('price'),
        data.get('stock')
    )
    return jsonify({'success': True, 'product': product})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@admin_required
def api_update_product(product_id):
    data = request.json
    pos_controller.update_product(
        product_id,
        data.get('name'),
        data.get('price'),
        data.get('stock')
    )
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@admin_required
def api_delete_product(product_id):
    pos_controller.delete_product(product_id)
    return jsonify({'success': True})

@app.route('/api/cart', methods=['GET'])
@login_required
def api_get_cart():
    cart_manager = CartManager(session)
    return jsonify(cart_manager.get_cart())

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    products = pos_controller.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    if product['stock'] < quantity:
        return jsonify({'success': False, 'message': f'Only {product["stock"]} units available!'})
    
    cart_manager = CartManager(session)
    success, message = cart_manager.add_item(
        product_id, product['name'], product['price'], 
        quantity, product['stock']
    )
    
    return jsonify({'success': success, 'message': message, 'cart': cart_manager.get_cart()})

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(product_id):
    cart_manager = CartManager(session)
    cart_manager.remove_item(product_id)
    return jsonify({'success': True, 'cart': cart_manager.get_cart()})

@app.route('/api/cart/update/<int:product_id>', methods=['PUT'])
@login_required
def api_update_cart_quantity(product_id):
    data = request.json
    quantity = data.get('quantity', 1)
    
    products = pos_controller.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    cart_manager = CartManager(session)
    success, message = cart_manager.update_quantity(product_id, quantity, product['stock'])
    
    return jsonify({'success': success, 'message': message, 'cart': cart_manager.get_cart()})

@app.route('/api/process-payment', methods=['POST'])
@login_required
def api_process_payment():
    data = request.json
    payment = data.get('payment', 0)
    discount = data.get('discount')
    
    cart_manager = CartManager(session)
    username = session.get('username', 'POS User')
    
    success, message, receipt = pos_controller.process_payment(
        cart_manager, discount, payment, username
    )
    
    return jsonify({'success': success, 'message': message, 'receipt': receipt})

@app.route('/api/transactions', methods=['GET'])
@admin_required
def api_get_transactions():
    return jsonify(pos_controller.get_all_transactions())

@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def api_get_transaction(transaction_id):
    transaction = pos_controller.get_transaction_by_id(transaction_id)
    if transaction:
        return jsonify(transaction)
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/receipt/generate', methods=['POST'])
@login_required
def api_generate_receipt():
    data = request.json
    transaction_id = data.get('transaction_id')
    
    if not transaction_id:
        # Get latest transaction
        transactions = pos_controller.get_all_transactions()
        if transactions:
            transaction = transactions[0]
        else:
            return jsonify({'error': 'No transactions found'}), 404
    else:
        transaction = pos_controller.get_transaction_by_id(transaction_id)
    
    if transaction:
        receipt = pos_controller.receipt_generator.generate_receipt_text(transaction)
        return jsonify({'receipt': receipt})
    
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/analytics', methods=['GET'])
@admin_required
def api_get_analytics():
    return jsonify(pos_controller.get_analytics())

@app.route('/api/reports/daily', methods=['GET'])
@login_required
def api_get_daily_revenue():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    total = pos_controller.get_daily_revenue(date_str)
    return jsonify({'date': date_str, 'total_revenue': total})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# For Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)