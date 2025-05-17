import numpy as np
import matplotlib.pyplot as plt
from services.fuzzy_logic.engine import create_credit_risk_fis

def generate_membership_function_data(variable_name, num_points=100):
    """Generate data for plotting membership functions"""
    fis = create_credit_risk_fis()
    
    if variable_name not in fis.variables:
        raise ValueError(f"Variable {variable_name} not found in FIS")
    
    variable = fis.variables[variable_name]
    range_min, range_max = variable.range
    
    x = np.linspace(range_min, range_max, num_points)
    data = []
    
    for i, x_val in enumerate(x):
        point = {"x": float(x_val)}
        
        for mf_name, mf in variable.membership_functions.items():
            point[mf_name] = float(mf.evaluate(x_val))
        
        data.append(point)
    
    return data

def plot_membership_functions(variable_name, save_path=None):
    """Plot membership functions for a variable"""
    fis = create_credit_risk_fis()
    
    if variable_name not in fis.variables:
        raise ValueError(f"Variable {variable_name} not found in FIS")
    
    variable = fis.variables[variable_name]
    range_min, range_max = variable.range
    
    x = np.linspace(range_min, range_max, 1000)
    
    plt.figure(figsize=(10, 6))
    
    for mf_name, mf in variable.membership_functions.items():
        y = [mf.evaluate(x_val) for x_val in x]
        plt.plot(x, y, label=mf_name)
    
    plt.title(f"Membership Functions for {variable_name}")
    plt.xlabel(variable_name)
    plt.ylabel("Membership Degree")
    plt.legend()
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def evaluate_rule(rule_index, inputs):
    """Evaluate a specific rule and return its firing strength"""
    fis = create_credit_risk_fis()
    
    if rule_index < 0 or rule_index >= len(fis.rules):
        raise ValueError(f"Rule index {rule_index} out of range")
    
    rule = fis.rules[rule_index]
    firing_strength = rule.evaluate(inputs)
    
    return {
        "rule_index": rule_index,
        "firing_strength": firing_strength,
        "consequent_var": rule.consequent_var,
        "consequent_term": rule.consequent_term
    }

def generate_rule_evaluation_data(inputs):
    """Generate data for rule evaluation visualization"""
    fis = create_credit_risk_fis()
    
    data = []
    for i, rule in enumerate(fis.rules):
        firing_strength = rule.evaluate(inputs)
        
        # Get the crisp output value using the inverse membership function
        mf = fis.variables[rule.consequent_var].membership_functions[rule.consequent_term]
        crisp_value = mf.inverse(firing_strength) if firing_strength > 0 else 0
        
        data.append({
            "rule": f"Rule {i+1}",
            "antecedent": firing_strength,
            "consequent": firing_strength,  # Same as antecedent in Tsukamoto
            "description": get_rule_description(i),
            "output_var": rule.consequent_var,
            "output_term": rule.consequent_term,
            "crisp_value": crisp_value
        })
    
    return data

def get_rule_description(rule_index):
    """Get a human-readable description of a rule"""
    descriptions = [
        "IF income is high AND dependents are few AND credit history is good THEN eligibility is eligible",
        "IF income is high AND dependents are few AND credit history is good THEN risk is low",
        "IF income is medium AND dependents are average AND credit history is average THEN eligibility is under consideration",
        "IF income is medium AND dependents are average AND credit history is average THEN risk is medium",
        "IF income is low OR dependents are many OR credit history is poor THEN eligibility is not eligible",
        "IF income is low OR dependents are many OR credit history is poor THEN risk is high"
    ]
    
    if rule_index < 0 or rule_index >= len(descriptions):
        return "Unknown rule"
    
    return descriptions[rule_index]

def generate_comparison_data(income, dependents, risk_score):
    """Generate data for comparison with average metrics"""
    # These would typically come from database averages
    avg_income = 6200000
    avg_dependents = 2.5
    avg_risk_score = 45
    
    return [
        {"name": "Monthly Income", "applicant": income, "average": avg_income},
        {"name": "Dependents", "applicant": dependents, "average": avg_dependents},
        {"name": "Risk Score", "applicant": risk_score, "average": avg_risk_score}
    ]