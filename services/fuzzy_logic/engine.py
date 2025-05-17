import numpy as np

# Membership function types
class MembershipFunction:
    def __init__(self, name):
        self.name = name
    
    def evaluate(self, x):
        pass

class TriangularMF(MembershipFunction):
    def __init__(self, name, a, b, c):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c
    
    def evaluate(self, x):
        if x <= self.a or x >= self.c:
            return 0
        if x == self.b:
            return 1
        if x < self.b:
            return (x - self.a) / (self.b - self.a)
        return (self.c - x) / (self.c - self.b)
    
    def inverse(self, y):
        # Inverse function for defuzzification
        if y == 0:
            return self.b  # Default to center if membership is 0
        if y <= 1:
            # Left side of triangle
            x_left = self.a + y * (self.b - self.a)
            # Right side of triangle
            x_right = self.c - y * (self.c - self.b)
            # Return the average (simplified approach)
            return (x_left + x_right) / 2
        return self.b  # Default to center if membership > 1

class TrapezoidalMF(MembershipFunction):
    def __init__(self, name, a, b, c, d):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
    def evaluate(self, x):
        if x <= self.a or x >= self.d:
            return 0
        if self.b <= x <= self.c:
            return 1
        if x < self.b:
            return (x - self.a) / (self.b - self.a)
        return (self.d - x) / (self.d - self.c)
    
    def inverse(self, y):
        # Inverse function for defuzzification
        if y == 0:
            return (self.b + self.c) / 2  # Default to center if membership is 0
        if y == 1:
            return (self.b + self.c) / 2  # Return center of flat top
        if y < 1:
            # Left side of trapezoid
            x_left = self.a + y * (self.b - self.a)
            # Right side of trapezoid
            x_right = self.d - y * (self.d - self.c)
            # Return the average (simplified approach)
            return (x_left + x_right) / 2
        return (self.b + self.c) / 2  # Default to center if membership > 1

# Fuzzy variable
class FuzzyVariable:
    def __init__(self, name, range_min, range_max):
        self.name = name
        self.range = (range_min, range_max)
        self.membership_functions = {}
    
    def add_membership_function(self, mf):
        self.membership_functions[mf.name] = mf
    
    def fuzzify(self, x):
        result = {}
        for name, mf in self.membership_functions.items():
            result[name] = mf.evaluate(x)
        return result

# Fuzzy rule
class FuzzyRule:
    def __init__(self, antecedent_func, consequent_var, consequent_term):
        self.antecedent_func = antecedent_func
        self.consequent_var = consequent_var
        self.consequent_term = consequent_term
    
    def evaluate(self, inputs):
        return self.antecedent_func(inputs)

# Tsukamoto fuzzy inference system
class TsukamotoFIS:
    def __init__(self):
        self.variables = {}
        self.rules = []
        self.output_variables = set()
    
    def add_variable(self, variable, is_output=False):
        self.variables[variable.name] = variable
        if is_output:
            self.output_variables.add(variable.name)
    
    def add_rule(self, rule):
        self.rules.append(rule)
    
    def evaluate(self, inputs):
        result = {}
        rule_results = []
        
        # Calculate firing strength for each rule
        for rule in self.rules:
            firing_strength = rule.evaluate(inputs)
            rule_results.append((rule, firing_strength))
        
        # Calculate weighted average for each output variable
        for output_var in self.output_variables:
            weighted_sum = 0
            weight_sum = 0
            
            for rule, firing_strength in rule_results:
                if rule.consequent_var == output_var and firing_strength > 0:
                    # Find the inverse of the membership function to get the crisp value
                    mf = self.variables[output_var].membership_functions[rule.consequent_term]
                    crisp_value = mf.inverse(firing_strength)
                    
                    weighted_sum += crisp_value * firing_strength
                    weight_sum += firing_strength
            
            if weight_sum > 0:
                result[output_var] = weighted_sum / weight_sum
            else:
                # Default to middle of range if no rules fire
                var_range = self.variables[output_var].range
                result[output_var] = (var_range[0] + var_range[1]) / 2
        
        return result

# Create credit risk FIS
def create_credit_risk_fis():
    fis = TsukamotoFIS()
    
    # Income variable
    income_var = FuzzyVariable("income", 0, 20000000)  # 0 to 20 million IDR
    income_var.add_membership_function(TrapezoidalMF("low", 0, 0, 2500000, 3000000))
    income_var.add_membership_function(TriangularMF("medium", 2500000, 5000000, 7000000))
    income_var.add_membership_function(TrapezoidalMF("high", 6500000, 7000000, 20000000, 20000000))
    fis.add_variable(income_var)
    
    # Dependents variable
    dependents_var = FuzzyVariable("dependents", 0, 10)
    dependents_var.add_membership_function(TrapezoidalMF("few", 0, 0, 1, 2))
    dependents_var.add_membership_function(TriangularMF("average", 1, 2, 3))
    dependents_var.add_membership_function(TrapezoidalMF("many", 3, 4, 10, 10))
    fis.add_variable(dependents_var)
    
    # Credit history variable
    credit_history_var = FuzzyVariable("credit_history", 0, 10)  # 0 (poor) to 10 (excellent)
    credit_history_var.add_membership_function(TrapezoidalMF("poor", 0, 0, 3, 4))
    credit_history_var.add_membership_function(TriangularMF("average", 3, 5, 7))
    credit_history_var.add_membership_function(TrapezoidalMF("good", 6, 7, 10, 10))
    fis.add_variable(credit_history_var)
    
    # Risk level output variable
    risk_var = FuzzyVariable("risk", 0, 100)  # 0 (low risk) to 100 (high risk)
    risk_var.add_membership_function(TrapezoidalMF("low", 0, 0, 30, 40))
    risk_var.add_membership_function(TriangularMF("medium", 30, 50, 70))
    risk_var.add_membership_function(TrapezoidalMF("high", 60, 70, 100, 100))
    fis.add_variable(risk_var, is_output=True)
    
    # Eligibility output variable
    eligibility_var = FuzzyVariable("eligibility", 0, 100)  # 0 (not eligible) to 100 (eligible)
    eligibility_var.add_membership_function(TrapezoidalMF("not_eligible", 0, 0, 30, 40))
    eligibility_var.add_membership_function(TriangularMF("under_consideration", 30, 50, 70))
    eligibility_var.add_membership_function(TrapezoidalMF("eligible", 60, 70, 100, 100))
    fis.add_variable(eligibility_var, is_output=True)
    
    # Rule 1: IF income is high AND dependents are few AND credit history is good THEN eligibility is eligible
    def rule1_antecedent(inputs):
        income_high = income_var.membership_functions["high"].evaluate(inputs["income"])
        dependents_few = dependents_var.membership_functions["few"].evaluate(inputs["dependents"])
        credit_good = credit_history_var.membership_functions["good"].evaluate(inputs["credit_history"])
        return min(income_high, dependents_few, credit_good)
    
    fis.add_rule(FuzzyRule(rule1_antecedent, "eligibility", "eligible"))
    
    # Rule 2: IF income is high AND dependents are few AND credit history is good THEN risk is low
    fis.add_rule(FuzzyRule(rule1_antecedent, "risk", "low"))
    
    # Rule 3: IF income is medium AND dependents are average AND credit history is average THEN eligibility is under_consideration
    def rule3_antecedent(inputs):
        income_medium = income_var.membership_functions["medium"].evaluate(inputs["income"])
        dependents_avg = dependents_var.membership_functions["average"].evaluate(inputs["dependents"])
        credit_avg = credit_history_var.membership_functions["average"].evaluate(inputs["credit_history"])
        return min(income_medium, dependents_avg, credit_avg)
    
    fis.add_rule(FuzzyRule(rule3_antecedent, "eligibility", "under_consideration"))
    
    # Rule 4: IF income is medium AND dependents are average AND credit history is average THEN risk is medium
    fis.add_rule(FuzzyRule(rule3_antecedent, "risk", "medium"))
    
    # Rule 5: IF income is low OR dependents are many OR credit history is poor THEN eligibility is not_eligible
    def rule5_antecedent(inputs):
        income_low = income_var.membership_functions["low"].evaluate(inputs["income"])
        dependents_many = dependents_var.membership_functions["many"].evaluate(inputs["dependents"])
        credit_poor = credit_history_var.membership_functions["poor"].evaluate(inputs["credit_history"])
        return max(income_low, dependents_many, credit_poor)
    
    fis.add_rule(FuzzyRule(rule5_antecedent, "eligibility", "not_eligible"))
    
    # Rule 6: IF income is low OR dependents are many OR credit history is poor THEN risk is high
    fis.add_rule(FuzzyRule(rule5_antecedent, "risk", "high"))
    
    return fis

# Function to evaluate credit risk
def evaluate_credit_risk(income, dependents, credit_history_rating):
    fis = create_credit_risk_fis()
    result = fis.evaluate({
        "income": income,
        "dependents": dependents,
        "credit_history": credit_history_rating
    })
    
    return {
        "risk": result["risk"],
        "eligibility": result["eligibility"]
    }

# Helper functions
def get_risk_level(risk_score):
    if risk_score < 40:
        return "Low"
    if risk_score < 70:
        return "Medium"
    return "High"

def get_eligibility_status(eligibility_score):
    if eligibility_score < 40:
        return "Not Eligible"
    if eligibility_score < 70:
        return "Under Consideration"
    return "Eligible"

# Test the fuzzy logic system
if __name__ == "__main__":
    # Test with different inputs
    test_cases = [
        {"income": 8000000, "dependents": 1, "credit_history": 8},  # High income, few dependents, good credit
        {"income": 5000000, "dependents": 2, "credit_history": 5},  # Medium income, average dependents, average credit
        {"income": 2000000, "dependents": 5, "credit_history": 2}   # Low income, many dependents, poor credit
    ]
    
    for i, test in enumerate(test_cases):
        result = evaluate_credit_risk(**test)
        risk_score = result["risk"]
        eligibility_score = result["eligibility"]
        
        print(f"Test Case {i+1}:")
        print(f"  Inputs: {test}")
        print(f"  Risk Score: {risk_score:.2f} ({get_risk_level(risk_score)})")
        print(f"  Eligibility Score: {eligibility_score:.2f} ({get_eligibility_status(eligibility_score)})")
        print()