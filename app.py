# app.py - Complete POS System Backend (OOP Version)
# Object-Oriented Programming with Classes, Inheritance, Polymorphism, Encapsulation, Abstraction

from flask import Flask, render_template, request, jsonify, session, send_file
from datetime import datetime, timedelta
import json
import os
from functools import wraps
from abc import ABC, abstractmethod

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# ========== ABSTRACT BASE CLASS (ABSTRACTION) ==========
class DataStorageInterface(ABC):
    """Abstract base class for data storage operations - Demonstrates ABSTRACTION"""
    
    @abstractmethod
    def load_data(self):
        """Abstract method - must be implemented by child classes"""
        pass
    
    @abstractmethod
    def save_data(self, data):
        """Abstract method - must be implemented by child classes"""
        pass
    
    @abstractmethod
    def get_products(self):
        """Abstract method - must be implemented by child classes"""
        pass
    
    @abstractmethod
    def get_transactions(self):
        """Abstract method - must be implemented by child classes"""
        pass

# ========== DATA STORAGE CLASS (INHERITANCE & ENCAPSULATION) ==========
class JSONDataStorage(DataStorageInterface):
    """Handles JSON file operations - Demonstrates INHERITANCE from DataStorageInterface"""
    
    def __init__(self, data_file='pos_data.json'):
        """Constructor - Demonstrates ENCAPSULATION by hiding internal attributes"""
        self.__data_file = data_file  # Private attribute (ENCAPSULATION)
        self.__data = self.__load_initial_data()
    
    def __load_initial_data(self):
        """Private method - Demonstrates ENCAPSULATION"""
        if os.path.exists(self.__data_file):
            return self.load_data()
        return {
            'products': [],
            'transactions': []
        }
    
    def load_data(self):
        """Implementation of abstract method - Demonstrates POLYMORPHISM"""
        try:
            with open(self.__data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.__get_default_data()
    
    def __get_default_data(self):
        """Private helper method - Demonstrates ENCAPSULATION"""
        return {
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
    
    def save_data(self, data):
        """Implementation of abstract method - Demonstrates POLYMORPHISM"""
        with open(self.__data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_products(self):
        """Implementation of abstract method"""
        return self.load_data().get('products', [])
    
    def get_transactions(self):
        """Implementation of abstract method"""
        return self.load_data().get('transactions', [])
    
    def update_product_stock(self, product_id, quantity_sold):
        """Update product stock after sale"""
        data = self.load_data()
        for product in data['products']:
            if product['id'] == product_id:
                product['stock'] -= quantity_sold
                product['sales'] = product.get('sales', 0) + quantity_sold
                break
        self.save_data(data)
    
    def add_transaction(self, transaction):
        """Add new transaction to storage"""
        data = self.load_data()
        data['transactions'].insert(0, transaction)
        self.save_data(data)
    
    def add_product(self, product):
        """Add new product to storage"""
        data = self.load_data()
        data['products'].append(product)
        self.save_data(data)
    
    def update_product(self, product_id, updated_data):
        """Update existing product"""
        data = self.load_data()
        for product in data['products']:
            if product['id'] == product_id:
                product.update(updated_data)
                break
        self.save_data(data)
    
    def delete_product(self, product_id):
        """Delete product from storage"""
        data = self.load_data()
        data['products'] = [p for p in data['products'] if p['id'] != product_id]
        self.save_data(data)

# ========== PRODUCT CLASS ==========
class Product:
    """Product class demonstrating ENCAPSULATION"""
    
    def __init__(self, product_id, name, price, stock, sales=0):
        """Constructor with private attributes"""
        self.__id = product_id
        self.__name = name
        self.__price = price
        self.__stock = stock
        self.__sales = sales
    
    # Getter methods (ENCAPSULATION)
    def get_id(self):
        return self.__id
    
    def get_name(self):
        return self.__name
    
    def get_price(self):
        return self.__price
    
    def get_stock(self):
        return self.__stock
    
    def get_sales(self):
        return self.__sales
    
    # Setter methods (ENCAPSULATION)
    def set_name(self, name):
        self.__name = name
    
    def set_price(self, price):
        self.__price = price
    
    def set_stock(self, stock):
        self.__stock = stock
    
    def set_sales(self, sales):
        self.__sales = sales
    
    def reduce_stock(self, quantity):
        """Reduce stock when sold"""
        if quantity <= self.__stock:
            self.__stock -= quantity
            self.__sales += quantity
            return True
        return False
    
    def to_dict(self):
        """Convert to dictionary for JSON storage"""
        return {
            'id': self.__id,
            'name': self.__name,
            'price': self.__price,
            'stock': self.__stock,
            'sales': self.__sales
        }
    
    @classmethod
    def from_dict(cls, data):
        """Factory method to create Product from dictionary"""
        return cls(data['id'], data['name'], data['price'], data['stock'], data.get('sales', 0))

# ========== CART ITEM CLASS ==========
class CartItem:
    """Cart item class"""
    
    def __init__(self, product_id, name, price, quantity):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity
    
    def get_total(self):
        """Calculate item total"""
        return self.price * self.quantity
    
    def to_dict(self):
        return {
            'id': self.product_id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity
        }

# ========== DISCOUNT CLASS (POLYMORPHISM) ==========
class Discount(ABC):
    """Abstract base class for discounts - Demonstrates ABSTRACTION & POLYMORPHISM"""
    
    def __init__(self, value):
        self.value = value
        self.amount = 0
    
    @abstractmethod
    def calculate(self, subtotal):
        """Abstract method - different discount types implement differently"""
        pass
    
    def to_dict(self):
        return {'type': self.get_type(), 'value': self.value, 'amount': self.amount}
    
    @abstractmethod
    def get_type(self):
        pass

class PercentageDiscount(Discount):
    """Percentage discount - Demonstrates INHERITANCE & POLYMORPHISM"""
    
    def calculate(self, subtotal):
        self.amount = (subtotal * self.value) / 100
        return self.amount
    
    def get_type(self):
        return 'percentage'

class FixedDiscount(Discount):
    """Fixed amount discount - Demonstrates INHERITANCE & POLYMORPHISM"""
    
    def calculate(self, subtotal):
        self.amount = min(self.value, subtotal)
        return self.amount
    
    def get_type(self):
        return 'fixed'

# ========== TRANSACTION CLASS ==========
class Transaction:
    """Transaction class for sales records"""
    
    def __init__(self, cart_items, subtotal, discount_amount, total, payment, change, cashier):
        self.id = int(datetime.now().timestamp() * 1000)
        self.date = datetime.now().isoformat()
        self.items = cart_items
        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.total = total
        self.payment = payment
        self.change = change
        self.cashier = cashier
        self.discount = None
    
    def set_discount(self, discount):
        self.discount = discount
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'items': [item.to_dict() for item in self.items],
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'total': self.total,
            'payment': self.payment,
            'change': self.change,
            'cashier': self.cashier
        }

# ========== RECEIPT GENERATOR CLASS ==========
class ReceiptGenerator:
    """Handles receipt generation - Demonstrates SINGLE RESPONSIBILITY"""
    
    @staticmethod
    def generate_receipt_text(transaction_dict):
        """Generate formatted receipt text"""
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

# ========== REPORT GENERATOR CLASS ==========
class ReportGenerator:
    """Generates various sales reports - Demonstrates SINGLE RESPONSIBILITY"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def get_daily_report(self, target_date):
        """Generate daily sales report"""
        data = self.storage.load_data()
        daily_transactions = [
            t for t in data['transactions'] 
            if datetime.fromisoformat(t['date']).date() == target_date
        ]
        
        total_revenue = sum(t['total'] for t in daily_transactions)
        total_transactions = len(daily_transactions)
        total_items = sum(sum(item['quantity'] for item in t['items']) for t in daily_transactions)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate best sellers
        product_sales = {}
        for transaction in daily_transactions:
            for item in transaction['items']:
                product_sales[item['name']] = product_sales.get(item['name'], 0) + item['quantity']
        
        best_sellers = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'date': target_date.isoformat(),
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'total_items': total_items,
            'avg_transaction': avg_transaction,
            'best_sellers': [{'name': name, 'quantity': qty} for name, qty in best_sellers]
        }
    
    def get_monthly_report(self, year, month):
        """Generate monthly sales report"""
        data = self.storage.load_data()
        monthly_transactions = [
            t for t in data['transactions']
            if datetime.fromisoformat(t['date']).year == year and 
               datetime.fromisoformat(t['date']).month == month
        ]
        
        total_revenue = sum(t['total'] for t in monthly_transactions)
        total_transactions = len(monthly_transactions)
        total_items = sum(sum(item['quantity'] for item in t['items']) for t in monthly_transactions)
        
        # Daily breakdown
        daily_breakdown = {}
        for transaction in monthly_transactions:
            day = datetime.fromisoformat(transaction['date']).day
            daily_breakdown[day] = daily_breakdown.get(day, 0) + transaction['total']
        
        # Best sellers
        product_sales = {}
        for transaction in monthly_transactions:
            for item in transaction['items']:
                product_sales[item['name']] = product_sales.get(item['name'], 0) + item['quantity']
        
        best_sellers = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'year': year,
            'month': month,
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'total_items': total_items,
            'daily_breakdown': [{'day': day, 'revenue': revenue} for day, revenue in sorted(daily_breakdown.items())],
            'best_sellers': [{'name': name, 'quantity': qty} for name, qty in best_sellers]
        }
    
    def get_analytics(self):
        """Generate overall analytics"""
        data = self.storage.load_data()
        transactions = data['transactions']
        
        total_revenue = sum(t['total'] for t in transactions)
        total_transactions = len(transactions)
        total_items = sum(sum(item['quantity'] for item in t['items']) for t in transactions)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # All-time best sellers
        product_sales = {}
        for transaction in transactions:
            for item in transaction['items']:
                product_sales[item['name']] = product_sales.get(item['name'], 0) + item['quantity']
        
        best_sellers = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Last 7 days trend
        last_7_days = []
        today = datetime.now().date()
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_revenue = sum(
                t['total'] for t in transactions 
                if datetime.fromisoformat(t['date']).date() == date
            )
            day_transactions = len([
                t for t in transactions 
                if datetime.fromisoformat(t['date']).date() == date
            ])
            last_7_days.append({
                'date': date.isoformat(),
                'revenue': day_revenue,
                'transactions': day_transactions
            })
        
        return {
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'total_items': total_items,
            'avg_transaction': avg_transaction,
            'best_sellers': [{'name': name, 'quantity': qty} for name, qty in best_sellers[:5]],
            'last_7_days': last_7_days
        }

# ========== CART MANAGER CLASS ==========
class CartManager:
    """Manages shopping cart operations"""
    
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
            cart.append({
                'id': product_id,
                'name': name,
                'price': price,
                'quantity': quantity
            })
            self.set_cart(cart)
            return True, f'Added {name} to cart'
    
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
    
    def get_cart_items_copy(self):
        cart = self.get_cart()
        return [CartItem(item['id'], item['name'], item['price'], item['quantity']) for item in cart]

# ========== AUTHENTICATION MANAGER CLASS ==========
class AuthManager:
    """Manages user authentication - Demonstrates SINGLE RESPONSIBILITY"""
    
    def __init__(self):
        self.__users = {
            'admin': {'password': 'secret', 'role': 'admin'},
            'user': {'password': '123456', 'role': 'user'}
        }
    
    def authenticate(self, username, password):
        """Authenticate user credentials"""
        if username in self.__users and self.__users[username]['password'] == password:
            return True, self.__users[username]['role']
        return False, None
    
    def get_user_role(self, username):
        return self.__users.get(username, {}).get('role', None)

# ========== POS CONTROLLER CLASS (MAIN CONTROLLER) ==========
class POSController:
    """Main controller that orchestrates all operations - Demonstrates COMPOSITION"""
    
    def __init__(self):
        self.storage = JSONDataStorage()
        self.auth_manager = AuthManager()
        self.report_generator = ReportGenerator(self.storage)
        self.receipt_generator = ReceiptGenerator()
    
    def get_products(self):
        return self.storage.get_products()
    
    def add_product(self, name, price, stock):
        data = self.storage.load_data()
        new_id = max([p['id'] for p in data['products']], default=0) + 1
        new_product = {
            'id': new_id,
            'name': name,
            'price': float(price),
            'stock': int(stock),
            'sales': 0
        }
        self.storage.add_product(new_product)
        return new_product
    
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
        cart_items = cart_manager.get_cart_items_copy()
        
        if not cart_items:
            return False, "Cart is empty!", None
        
        subtotal = sum(item.get_total() for item in cart_items)
        
        # Calculate discount
        discount_amount = 0
        discount_obj = None
        if discount_data:
            if discount_data['type'] == 'percentage':
                discount_obj = PercentageDiscount(discount_data['value'])
            else:
                discount_obj = FixedDiscount(discount_data['value'])
            discount_amount = discount_obj.calculate(subtotal)
        
        total = subtotal - discount_amount
        
        if payment_amount < total:
            return False, f"Insufficient payment! Need ₱{total - payment_amount:,.2f}", None
        
        # Update stock
        for cart_item in cart_items:
            self.storage.update_product_stock(cart_item.product_id, cart_item.quantity)
        
        # Create transaction
        transaction = Transaction(
            cart_items, subtotal, discount_amount, total, 
            payment_amount, payment_amount - total, username
        )
        
        # Save transaction to storage
        self.storage.add_transaction(transaction.to_dict())
        
        # Clear cart
        cart_manager.clear_cart()
        
        # Generate receipt
        receipt = self.receipt_generator.generate_receipt_text(transaction.to_dict())
        
        return True, f"Transaction successful! Change: ₱{transaction.change:,.2f}", receipt
    
    def get_daily_report(self, date):
        return self.report_generator.get_daily_report(date)
    
    def get_monthly_report(self, year, month):
        return self.report_generator.get_monthly_report(year, month)
    
    def get_analytics(self):
        return self.report_generator.get_analytics()
    
    def get_all_transactions(self):
        return self.storage.get_transactions()
    
    def get_transaction_by_id(self, transaction_id):
        transactions = self.storage.get_transactions()
        return next((t for t in transactions if t['id'] == transaction_id), None)

# ========== FLASK ROUTES (Using the OOP Controller) ==========
# Initialize the controller
pos_controller = POSController()

# ========== AUTHENTICATION ==========
def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to check if user has admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== FEATURE 1: SALES TRANSACTION FUNCTIONS ==========
@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Get all products"""
    products = pos_controller.get_products()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    """Get single product by ID"""
    products = pos_controller.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add item to cart (session-based)"""
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

@app.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    """Get current cart"""
    cart_manager = CartManager(session)
    return jsonify(cart_manager.get_cart())

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart_manager = CartManager(session)
    cart_manager.remove_item(product_id)
    return jsonify({'success': True, 'cart': cart_manager.get_cart()})

@app.route('/api/cart/update', methods=['PUT'])
@login_required
def update_cart_quantity():
    """Update cart item quantity"""
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    products = pos_controller.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    cart_manager = CartManager(session)
    success, message = cart_manager.update_quantity(product_id, quantity, product['stock'])
    
    return jsonify({'success': success, 'message': message, 'cart': cart_manager.get_cart()})
# ========== FEATURE 2: RECEIPT GENERATION ==========
@app.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment and create transaction"""
    data = request.json
    payment = data.get('payment', 0)
    discount = data.get('discount')
    
    cart_manager = CartManager(session)
    username = session.get('username', 'POS User')
    
    success, message, receipt = pos_controller.process_payment(
        cart_manager, discount, payment, username
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            'receipt': receipt
        })
    else:
        return jsonify({'success': False, 'message': message})

# ========== FEATURE 3: SALES REPORTS ==========
@app.route('/api/reports/daily', methods=['GET'])
@admin_required
def get_daily_report():
    """Generate daily sales report"""
    date_str = request.args.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()
    
    report = pos_controller.get_daily_report(target_date)
    return jsonify(report)

@app.route('/api/reports/monthly', methods=['GET'])
@admin_required
def get_monthly_report():
    """Generate monthly sales report"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        now = datetime.now()
        year = now.year
        month = now.month
    
    report = pos_controller.get_monthly_report(year, month)
    return jsonify(report)

@app.route('/api/reports/analytics', methods=['GET'])
@admin_required
def get_analytics():
    """Generate overall analytics"""
    analytics = pos_controller.get_analytics()
    return jsonify(analytics)

@app.route('/api/transactions', methods=['GET'])
@admin_required
def get_transactions():
    """Get all transactions"""
    transactions = pos_controller.get_all_transactions()
    return jsonify(transactions)

@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@admin_required
def get_transaction(transaction_id):
    """Get single transaction by ID"""
    transaction = pos_controller.get_transaction_by_id(transaction_id)
    if transaction:
        return jsonify(transaction)
    return jsonify({'error': 'Transaction not found'}), 404

# ========== PRODUCT MANAGEMENT (Admin Only) ==========
@app.route('/api/products', methods=['POST'])
@admin_required
def add_product():
    """Add new product"""
    data = request.json
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    
    new_product = pos_controller.add_product(name, price, stock)
    return jsonify({'success': True, 'product': new_product})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    """Update existing product"""
    data = request.json
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    
    pos_controller.update_product(product_id, name, price, stock)
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    """Delete product"""
    pos_controller.delete_product(product_id)
    return jsonify({'success': True})

# ========== AUTHENTICATION ROUTES ==========
@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    success, role = pos_controller.auth_manager.authenticate(username, password)
    
    if success:
        session['username'] = username
        session['role'] = role
        return jsonify({
            'success': True,
            'username': username,
            'role': role
        })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username'],
            'role': session['role']
        })
    return jsonify({'authenticated': False})

# ========== SERVE HTML FILES ==========
@app.route('/')
def index():
    """Serve main dashboard"""
    return send_file('templates/dashboard.html')

@app.route('/feature1')
def feature1():
    """FEATURE 1: Sales Transaction System"""
    return send_file('templates/salestransaction.html')

@app.route('/feature2')
def feature2():
    """FEATURE 2: Receipt Generation"""
    return send_file('templates/receiptgenerationsforcustomers.html')

@app.route('/feature3')
def feature3():
    """FEATURE 3: Sales Reports"""
    return send_file('templates/salessummaryandreporting.html')

@app.route('/products')
def products_page():
    """Product Management (Admin Only)"""
    return send_file('templates/products.html')

@app.route('/history')
def history_page():
    """Transaction History (Admin Only)"""
    return send_file('templates/history.html')

application = app

if __name__ == '_main_':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)