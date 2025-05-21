from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/credit_risk')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Import models and routes after initializing db
from models.user import User
from models.customer import Customer
from models.loan_application import LoanApplication
from services.fuzzy_logic.engine import evaluate_credit_risk

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    # Create new user
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role=data.get('role', 'user')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password is correct
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 200

# Customer routes
@app.route('/api/customers', methods=['GET'])
@jwt_required()
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers]), 200

@app.route('/api/customers/<int:id>', methods=['GET'])
@jwt_required()
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return jsonify(customer.to_dict()), 200

@app.route('/api/customers', methods=['POST'])
@jwt_required()
def create_customer():
    data = request.get_json()
    
    new_customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        created_by=get_jwt_identity()
    )
    
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify(new_customer.to_dict()), 201

# Loan application routes
@app.route('/api/applications', methods=['GET'])
@jwt_required()
def get_applications():
    applications = LoanApplication.query.all()
    return jsonify([application.to_dict() for application in applications]), 200

@app.route('/api/applications/<int:id>', methods=['GET'])
@jwt_required()
def get_application(id):
    application = LoanApplication.query.get_or_404(id)
    return jsonify(application.to_dict()), 200

@app.route('/api/applications', methods=['POST'])
@jwt_required()
def create_application():
    data = request.get_json()
    
    # Create customer if not exists
    customer = None
    if 'customer_id' in data:
        customer = Customer.query.get(data['customer_id'])
    
    if not customer:
        customer = Customer(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            created_by=get_jwt_identity()
        )
        db.session.add(customer)
        db.session.commit()
    
    # Convert credit history to numerical value
    credit_history_map = {
        'poor': 2,
        'average': 5,
        'good': 8
    }
    credit_history_value = credit_history_map.get(data['credit_history'].lower(), 5)
    
    # Evaluate credit risk using fuzzy logic
    result = evaluate_credit_risk(
        income=data['monthly_income'],
        dependents=data['dependents'],
        credit_history_rating=credit_history_value
    )
    
    # Determine eligibility status and risk level
    risk_score = int(result['risk'])
    eligibility_score = int(result['eligibility'])
    
    risk_level = 'Low'
    if risk_score >= 70:
        risk_level = 'High'
    elif risk_score >= 40:
        risk_level = 'Medium'
    
    eligibility_status = 'Eligible'
    if eligibility_score < 40:
        eligibility_status = 'Not Eligible'
    elif eligibility_score < 70:
        eligibility_status = 'Under Consideration'
    
    # Create new loan application
    new_application = LoanApplication(
        customer_id=customer.id,
        monthly_income=data['monthly_income'],
        dependents=data['dependents'],
        credit_history=data['credit_history'],
        risk_score=risk_score,
        risk_level=risk_level,
        eligibility_score=eligibility_score,
        eligibility_status=eligibility_status,
        created_by=get_jwt_identity()
    )
    
    db.session.add(new_application)
    db.session.commit()
    
    return jsonify(new_application.to_dict()), 201

# Dashboard statistics
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    # Get total applications
    total_applications = LoanApplication.query.count()
    
    # Get approved applications (Eligible)
    approved_applications = LoanApplication.query.filter_by(eligibility_status='Eligible').count()
    
    # Calculate approval rate
    approval_rate = 0
    if total_applications > 0:
        approval_rate = (approved_applications / total_applications) * 100
    
    # Get average risk score
    avg_risk_score = db.session.query(db.func.avg(LoanApplication.risk_score)).scalar() or 0
    
    # Get active customers
    active_customers = Customer.query.count()
    
    return jsonify({
        'total_applications': total_applications,
        'approval_rate': round(approval_rate, 1),
        'avg_risk_score': round(float(avg_risk_score), 1),
        'active_customers': active_customers
    }), 200

# Monthly applications chart data
@app.route('/api/dashboard/monthly-applications', methods=['GET'])
@jwt_required()
def get_monthly_applications():
    # Get current year
    current_year = datetime.now().year
    
    # Initialize data structure for all months
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = []
    
    for i, month in enumerate(months):
        # Get applications for this month
        month_num = i + 1
        applications = LoanApplication.query.filter(
            db.extract('year', LoanApplication.created_at) == current_year,
            db.extract('month', LoanApplication.created_at) == month_num
        ).count()
        
        # Get approvals for this month
        approvals = LoanApplication.query.filter(
            db.extract('year', LoanApplication.created_at) == current_year,
            db.extract('month', LoanApplication.created_at) == month_num,
            LoanApplication.eligibility_status == 'Eligible'
        ).count()
        
        monthly_data.append({
            'month': month,
            'applications': applications,
            'approvals': approvals
        })
    
    return jsonify(monthly_data), 200

# Risk distribution chart data
@app.route('/api/dashboard/risk-distribution', methods=['GET'])
@jwt_required()
def get_risk_distribution():
    # Count applications by risk level
    low_risk = LoanApplication.query.filter_by(risk_level='Low').count()
    medium_risk = LoanApplication.query.filter_by(risk_level='Medium').count()
    high_risk = LoanApplication.query.filter_by(risk_level='High').count()
    
    return jsonify([
        {'name': 'Low Risk', 'value': low_risk, 'color': '#10B981'},
        {'name': 'Medium Risk', 'value': medium_risk, 'color': '#F59E0B'},
        {'name': 'High Risk', 'value': high_risk, 'color': '#EF4444'}
    ]), 200

# Income range distribution
@app.route('/api/dashboard/income-distribution', methods=['GET'])
@jwt_required()
def get_income_distribution():
    # Count applications by income range
    less_than_3m = LoanApplication.query.filter(LoanApplication.monthly_income < 3000000).count()
    between_3m_5m = LoanApplication.query.filter(
        LoanApplication.monthly_income >= 3000000,
        LoanApplication.monthly_income < 5000000
    ).count()
    between_5m_7m = LoanApplication.query.filter(
        LoanApplication.monthly_income >= 5000000,
        LoanApplication.monthly_income < 7000000
    ).count()
    between_7m_10m = LoanApplication.query.filter(
        LoanApplication.monthly_income >= 7000000,
        LoanApplication.monthly_income < 10000000
    ).count()
    more_than_10m = LoanApplication.query.filter(LoanApplication.monthly_income >= 10000000).count()
    
    return jsonify([
        {'range': '<3M', 'count': less_than_3m},
        {'range': '3-5M', 'count': between_3m_5m},
        {'range': '5-7M', 'count': between_5m_7m},
        {'range': '7-10M', 'count': between_7m_10m},
        {'range': '>10M', 'count': more_than_10m}
    ]), 200

# Dependents distribution
@app.route('/api/dashboard/dependents-distribution', methods=['GET'])
@jwt_required()
def get_dependents_distribution():
    # Count applications by number of dependents
    zero_dependents = LoanApplication.query.filter_by(dependents=0).count()
    one_dependent = LoanApplication.query.filter_by(dependents=1).count()
    two_dependents = LoanApplication.query.filter_by(dependents=2).count()
    three_dependents = LoanApplication.query.filter_by(dependents=3).count()
    four_plus_dependents = LoanApplication.query.filter(LoanApplication.dependents >= 4).count()
    
    return jsonify([
        {'dependents': '0', 'count': zero_dependents},
        {'dependents': '1', 'count': one_dependent},
        {'dependents': '2', 'count': two_dependents},
        {'dependents': '3', 'count': three_dependents},
        {'dependents': '4+', 'count': four_plus_dependents}
    ]), 200

# Recent applications
@app.route('/api/dashboard/recent-applications', methods=['GET'])
@jwt_required()
def get_recent_applications():
    # Get 5 most recent applications
    applications = LoanApplication.query.order_by(LoanApplication.created_at.desc()).limit(5).all()
    
    result = []
    for app in applications:
        customer = Customer.query.get(app.customer_id)
        result.append({
            'id': f'APP-{app.id}',
            'name': customer.name,
            'date': app.created_at.strftime('%Y-%m-%d'),
            'income': app.monthly_income,
            'dependents': app.dependents,
            'risk': app.risk_level,
            'status': app.eligibility_status
        })
    
    return jsonify(result), 200

# Fuzzy logic visualization data
@app.route('/api/fuzzy/membership-functions/<variable_name>', methods=['GET'])
@jwt_required()
def get_membership_function_data(variable_name):
    from services.fuzzy_logic.visualization import generate_membership_function_data
    
    try:
        data = generate_membership_function_data(variable_name)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/fuzzy/rule-evaluation', methods=['POST'])
@jwt_required()
def get_rule_evaluation_data():
    from services.fuzzy_logic.visualization import generate_rule_evaluation_data
    
    data = request.get_json()
    
    # Convert credit history to numerical value
    credit_history_map = {
        'poor': 2,
        'average': 5,
        'good': 8
    }
    credit_history_value = credit_history_map.get(data['credit_history'].lower(), 5)
    
    inputs = {
        'income': data['monthly_income'],
        'dependents': data['dependents'],
        'credit_history': credit_history_value
    }
    
    rule_data = generate_rule_evaluation_data(inputs)
    return jsonify(rule_data), 200

@app.route('/api/fuzzy/comparison', methods=['POST'])
@jwt_required()
def get_comparison_data():
    from services.fuzzy_logic.visualization import generate_comparison_data
    
    data = request.get_json()
    
    comparison_data = generate_comparison_data(
        income=data['monthly_income'],
        dependents=data['dependents'],
        risk_score=data['risk_score']
    )
    
    return jsonify(comparison_data), 200

if __name__ == '__main__':
    app.run(debug=True)