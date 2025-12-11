from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import random

# --- 1. CONFIGURATION AND INITIALIZATION ---

# Create a path to the database file in the current directory
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# Allow access from the React development server on port 3000
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'food_connect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database object
db = SQLAlchemy(app)

# --- 2. DATABASE MODEL (The Table Structure) ---

class Donation(db.Model):
    # Defines the table name in the database
    __tablename__ = 'donations' 
    
    # Defines the columns (fields) for the donation table
    id = db.Column(db.Integer, primary_key=True)
    
    # Core Donation Info
    name = db.Column(db.String(100), nullable=False) # e.g., Chicken Sandwiches
    servings = db.Column(db.String(50)) # e.g., 20 Servings
    readyTime = db.Column(db.String(50)) # e.g., 3:00 PM Today
    foodType = db.Column(db.String(50)) # e.g., prepared or fresh
    status = db.Column(db.String(50), default='pending') # pending, claimed, delivered
    icon = db.Column(db.String(10), default='🎁')
    
    # Donor/Receiver Details (from Form)
    donor = db.Column(db.String(100), nullable=True) # Jane's Bakery (The name)
    donorAddress = db.Column(db.String(255))
    donor_phone = db.Column(db.String(50))
    receiverAddress = db.Column(db.String(255))
    receiverPhone = db.Column(db.String(50))

    # Dynamic/Calculated Fields
    distance = db.Column(db.String(50)) # e.g., 5.0 mi

    # Method to convert the Python object into a dictionary for JSON response
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'donor': self.donor,
            'donor_phone': self.donor_phone,
            'donorAddress': self.donorAddress,
            'receiverAddress': self.receiverAddress,
            'receiverPhone': self.receiverPhone,
            'servings': self.servings,
            'distance': self.distance,
            'readyTime': self.readyTime,
            'status': self.status,
            'icon': self.icon,
            'foodType': self.foodType
        }

# --- 3. HELPER FUNCTION FOR DISTANCE (Placeholder) ---
def calculate_distance_to_receiver(donor_address):
    """Simulated distance calculation."""
    return f"{random.uniform(0.5, 10.0):.1f} mi"


# --- 4. API ENDPOINTS ---

# 1. GET Endpoint (Retrieve all donations)
@app.route('/api/donations', methods=['GET'])
def get_donations():
    donations = Donation.query.all()
    # Ensure the list of dictionaries is returned
    return jsonify([d.to_dict() for d in donations])

# 2. POST Endpoint (Add a new donation)
@app.route('/api/donations', methods=['POST'])
def add_donation():
    new_donation_data = request.json
    
    if not new_donation_data or 'quantity' not in new_donation_data:
        return jsonify({"error": "Missing required data"}), 400

    calculated_distance = calculate_distance_to_receiver(new_donation_data.get('donorAddress', ''))
    
    # 🚨 FIX APPLIED: Using 'donorname' and 'itemname' from the form.
    new_donation = Donation(
        donor=new_donation_data.get('donorname', 'Web Form User'), 
        name=new_donation_data.get('itemname', 'New Food Donation'), 
        
        donor_phone=new_donation_data.get('donorPhone'),
        donorAddress=new_donation_data.get('donorAddress'),
        receiverAddress=new_donation_data.get('receiverAddress'),
        receiverPhone=new_donation_data.get('receiverPhone'),
        
        foodType=new_donation_data.get('foodType'),
        servings=f"{new_donation_data.get('quantity', 0)} Servings",
        distance=calculated_distance,
        readyTime=new_donation_data.get('pickupTime', 'ASAP')
    )
    
    try:
        db.session.add(new_donation)
        db.session.commit()
        
        print(f"--- API Success: Added donation ID {new_donation.id} to SQLite DB ---")
        # Ensure we return the dictionary of the newly created item
        return jsonify({"message": "Donation successfully recorded", "data": new_donation.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to save donation to database"}), 500

# 3. PATCH Endpoint (Claim a donation)
@app.route('/api/donations/<int:donation_id>/claim', methods=['PATCH'])
def claim_donation(donation_id):
    donation = Donation.query.get(donation_id)
    
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if donation.status == 'pending':
        donation.status = 'claimed'
        
        try:
            db.session.commit()
            print(f"--- API Success: Donation ID {donation_id} status updated to claimed ---")
            return jsonify({"message": f"Donation {donation_id} claimed successfully"}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Database Error during claim: {e}")
            return jsonify({"error": "Failed to update donation status"}), 500
    else:
        return jsonify({"message": f"Donation {donation_id} is already {donation.status}"}), 400


# --- 5. RUN SERVER AND CREATE DATABASE ---

if __name__ == '__main__':
    # This block creates the database file and all the tables defined by the models
    with app.app_context():
        db.create_all()
        print("Database 'food_connect.db' and tables ensured.")
        
    print("🚀 Python Flask API running on http://127.0.0.1:5000")
    # Setting use_reloader=False prevents database creation from running twice
    app.run(port=5000, debug=True, use_reloader=False)