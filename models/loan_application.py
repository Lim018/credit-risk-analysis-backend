from app import db
from datetime import datetime

class LoanApplication(db.Model):
    __tablename__ = 'loan_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)
    dependents = db.Column(db.Integer, nullable=False)
    credit_history = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    eligibility_score = db.Column(db.Float, nullable=False)
    eligibility_status = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'monthly_income': self.monthly_income,
            'dependents': self.dependents,
            'credit_history': self.credit_history,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'eligibility_score': self.eligibility_score,
            'eligibility_status': self.eligibility_status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }