from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# In-memory data storage (acts as database replacement)
users = {
    'admin@example.com': {'password': 'admin123', 'name': 'Admin User', 'role': 'admin'},
    'user@example.com': {'password': 'user123', 'name': 'John Doe', 'role': 'user'}
}

buses = {
    1: {
        'id': 1,
        'name': 'City Express',
        'from_city': 'New York',
        'to_city': 'Boston',
        'departure_time': '2024-12-20 08:00:00',
        'arrival_time': '2024-12-20 12:00:00',
        'price': 45.00,
        'total_seats': 40,
        'booked_seats': [5, 12, 18, 25, 33]
    },
    2: {
        'id': 2,
        'name': 'Coast Line Travels',
        'from_city': 'Los Angeles',
        'to_city': 'San Francisco',
        'departure_time': '2024-12-20 09:30:00',
        'arrival_time': '2024-12-20 14:30:00',
        'price': 65.00,
        'total_seats': 50,
        'booked_seats': [8, 15, 22, 30, 38, 42]
    },
    3: {
        'id': 3,
        'name': 'Mountain Rider',
        'from_city': 'Denver',
        'to_city': 'Salt Lake City',
        'departure_time': '2024-12-21 07:00:00',
        'arrival_time': '2024-12-21 13:00:00',
        'price': 55.00,
        'total_seats': 35,
        'booked_seats': [3, 7, 14, 28]
    },
    4: {
        'id': 4,
        'name': 'Southern Comfort',
        'from_city': 'Miami',
        'to_city': 'Orlando',
        'departure_time': '2024-12-21 10:00:00',
        'arrival_time': '2024-12-21 12:30:00',
        'price': 35.00,
        'total_seats': 45,
        'booked_seats': [10, 20, 30]
    },
    5: {
        'id': 5,
        'name': 'Windy City Transit',
        'from_city': 'Chicago',
        'to_city': 'Detroit',
        'departure_time': '2024-12-22 08:30:00',
        'arrival_time': '2024-12-22 11:30:00',
        'price': 40.00,
        'total_seats': 40,
        'booked_seats': [1, 2, 3, 4]
    }
}

bookings = {}
booking_counter = 1

# Helper function to get available seats
def get_available_seats(bus_id):
    bus = buses.get(bus_id)
    if not bus:
        return []
    booked = set(bus['booked_seats'])
    available = [seat for seat in range(1, bus['total_seats'] + 1) if seat not in booked]
    return available

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html', buses=buses.values())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users.get(email)
        if user and user['password'] == password:
            session['user_email'] = email
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if email in users:
            flash('Email already registered', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
        else:
            users[email] = {
                'password': password,
                'name': name,
                'role': 'user'
            }
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/buses')
def list_buses():
    from_city = request.args.get('from_city', '')
    to_city = request.args.get('to_city', '')
    date = request.args.get('date', '')
    
    filtered_buses = buses.values()
    
    if from_city:
        filtered_buses = [b for b in filtered_buses if from_city.lower() in b['from_city'].lower()]
    if to_city:
        filtered_buses = [b for b in filtered_buses if to_city.lower() in b['to_city'].lower()]
    if date:
        filtered_buses = [b for b in filtered_buses if date in b['departure_time']]
    
    return render_template('buses.html', buses=filtered_buses)

@app.route('/bus/<int:bus_id>')
def bus_details(bus_id):
    bus = buses.get(bus_id)
    if not bus:
        flash('Bus not found', 'danger')
        return redirect(url_for('list_buses'))
    
    available_seats = get_available_seats(bus_id)
    return render_template('bus_details.html', bus=bus, available_seats=available_seats)

@app.route('/book/<int:bus_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(bus_id):
    bus = buses.get(bus_id)
    if not bus:
        flash('Bus not found', 'danger')
        return redirect(url_for('list_buses'))
    
    if request.method == 'POST':
        seat_numbers = request.form.getlist('seats')
        passenger_name = request.form.get('passenger_name')
        passenger_phone = request.form.get('passenger_phone')
        
        if not seat_numbers:
            flash('Please select at least one seat', 'danger')
            return redirect(url_for('book_ticket', bus_id=bus_id))
        
        seat_numbers_int = [int(seat) for seat in seat_numbers]
        
        # Check if seats are still available
        available_seats = set(get_available_seats(bus_id))
        if all(seat in available_seats for seat in seat_numbers_int):
            global booking_counter
            booking_id = booking_counter
            booking_counter += 1
            
            # Create booking
            booking = {
                'id': booking_id,
                'bus_id': bus_id,
                'bus_name': bus['name'],
                'user_email': session['user_email'],
                'user_name': session['user_name'],
                'seats': seat_numbers_int,
                'passenger_name': passenger_name,
                'passenger_phone': passenger_phone,
                'total_amount': len(seat_numbers_int) * bus['price'],
                'booking_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'confirmed'
            }
            
            bookings[booking_id] = booking
            
            # Update bus booked seats
            bus['booked_seats'].extend(seat_numbers_int)
            
            flash(f'Successfully booked {len(seat_numbers_int)} seat(s)! Booking ID: {booking_id}', 'success')
            return redirect(url_for('my_bookings'))
        else:
            flash('Some seats are no longer available', 'danger')
    
    available_seats = get_available_seats(bus_id)
    return render_template('book_ticket.html', bus=bus, available_seats=available_seats)

@app.route('/my-bookings')
@login_required
def my_bookings():
    user_bookings = [b for b in bookings.values() if b['user_email'] == session['user_email']]
    return render_template('my_bookings.html', bookings=user_bookings)

@app.route('/cancel-booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = bookings.get(booking_id)
    if not booking:
        flash('Booking not found', 'danger')
        return redirect(url_for('my_bookings'))
    
    if booking['user_email'] != session['user_email'] and session['user_role'] != 'admin':
        flash('You can only cancel your own bookings', 'danger')
        return redirect(url_for('my_bookings'))
    
    # Free up seats
    bus = buses.get(booking['bus_id'])
    if bus:
        for seat in booking['seats']:
            if seat in bus['booked_seats']:
                bus['booked_seats'].remove(seat)
    
    booking['status'] = 'cancelled'
    flash(f'Booking #{booking_id} has been cancelled', 'info')
    return redirect(url_for('my_bookings'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_bookings = len(bookings)
    total_users = len(users)
    total_revenue = sum(b['total_amount'] for b in bookings.values() if b['status'] == 'confirmed')
    
    return render_template('admin_dashboard.html', 
                         total_bookings=total_bookings,
                         total_users=total_users,
                         total_revenue=total_revenue,
                         bookings=bookings.values(),
                         users=users)

@app.route('/admin/add-bus', methods=['GET', 'POST'])
@admin_required
def add_bus():
    if request.method == 'POST':
        new_id = max(buses.keys()) + 1 if buses else 1
        
        new_bus = {
            'id': new_id,
            'name': request.form.get('name'),
            'from_city': request.form.get('from_city'),
            'to_city': request.form.get('to_city'),
            'departure_time': request.form.get('departure_time'),
            'arrival_time': request.form.get('arrival_time'),
            'price': float(request.form.get('price')),
            'total_seats': int(request.form.get('total_seats')),
            'booked_seats': []
        }
        
        buses[new_id] = new_bus
        flash('Bus added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_bus.html')

@app.route('/api/bus/<int:bus_id>/seats')
def get_bus_seats(bus_id):
    bus = buses.get(bus_id)
    if not bus:
        return json.dumps({'error': 'Bus not found'}), 404
    
    available_seats = get_available_seats(bus_id)
    return json.dumps({
        'bus_id': bus_id,
        'total_seats': bus['total_seats'],
        'booked_seats': bus['booked_seats'],
        'available_seats': available_seats
    })

if __name__ == '__main__':
    app.run(debug=True)
