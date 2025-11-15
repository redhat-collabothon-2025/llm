import json
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

NUM_EMPLOYEES = 50
NUM_LOGS = 5000
START_DATE = datetime(2024, 1, 1)

NORMAL_ACTIONS = [
    "login", "logout", "file_read", "file_write", 
    "email_send", "dashboard_view", "report_generate"
]

SUSPICIOUS_ACTIONS = [
    "bulk_download", "permission_change", "vpn_connect",
    "database_query", "late_night_login", "multiple_failed_login"
]

ANOMALY_ACTIONS = [
    "mass_data_export", "credential_theft_attempt",
    "unauthorized_access", "privilege_escalation", "data_exfiltration"
]

NORMAL_IPS = [f"192.168.1.{i}" for i in range(1, 100)]
SUSPICIOUS_IPS = [f"10.0.{random.randint(0,255)}.{random.randint(0,255)}" for _ in range(20)]
ANOMALY_IPS = [fake.ipv4() for _ in range(10)]

def generate_log(employee_id, log_type="normal"):
    timestamp = START_DATE + timedelta(
        days=random.randint(0, 300),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    if log_type == "normal":
        action = random.choice(NORMAL_ACTIONS)
        ip = random.choice(NORMAL_IPS)
        status = "success"
        data_size = random.randint(100, 50000)
        explanation = "Standard employee activity during business hours"
        label = "NORMAL"
        
    elif log_type == "suspicious":
        action = random.choice(SUSPICIOUS_ACTIONS)
        ip = random.choice(SUSPICIOUS_IPS)
        status = random.choice(["success", "failed"])
        data_size = random.randint(50000, 500000)
        explanation = f"Unusual behavior detected: {action} from uncommon location"
        label = "SUSPICIOUS"
        
    else: 
        action = random.choice(ANOMALY_ACTIONS)
        ip = random.choice(ANOMALY_IPS)
        status = "success"
        data_size = random.randint(500000, 5000000)
        explanation = f"Critical security event: {action} indicates potential insider threat"
        label = "ANOMALY"
    
    return {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "employee_id": f"emp_{employee_id:03d}",
        "session_id": f"sess_{fake.uuid4()[:8]}",
        "ip_address": ip,
        "user_agent": fake.user_agent(),
        "action_type": action,
        "resource_accessed": fake.file_path(depth=3, extension="txt"),
        "resource_type": random.choice(["file", "database", "api", "service"]),
        "request_status": status,
        "data_size_bytes": data_size,
        "geolocation": fake.city(),
        "device_info": random.choice(["Windows-Desktop", "MacOS-Laptop", "Linux-Server"]),
        "label": label,
        "explanation": explanation
    }

def generate_dataset():
    logs = []
    
    normal_count = int(NUM_LOGS * 0.7)
    suspicious_count = int(NUM_LOGS * 0.2)
    anomaly_count = NUM_LOGS - normal_count - suspicious_count
    
    print(f"Generating {normal_count} normal logs...")
    for _ in range(normal_count):
        emp_id = random.randint(1, NUM_EMPLOYEES)
        logs.append(generate_log(emp_id, "normal"))
    
    print(f"Generating {suspicious_count} suspicious logs...")
    for _ in range(suspicious_count):
        emp_id = random.randint(1, NUM_EMPLOYEES)
        logs.append(generate_log(emp_id, "suspicious"))
    
    print(f"Generating {anomaly_count} anomaly logs...")
    for _ in range(anomaly_count):
        emp_id = random.randint(1, NUM_EMPLOYEES)
        logs.append(generate_log(emp_id, "anomaly"))
    
    random.shuffle(logs)
    
    return logs

if __name__ == "__main__":
    print("Starting synthetic log generation...")
    logs = generate_dataset()
    
    output_file = "../outputs/synthetic_logs.json"
    with open(output_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"✅ Generated {len(logs)} logs saved to {output_file}")
    
    normal = sum(1 for log in logs if log['label'] == 'NORMAL')
    suspicious = sum(1 for log in logs if log['label'] == 'SUSPICIOUS')
    anomaly = sum(1 for log in logs if log['label'] == 'ANOMALY')
    
    print(f"\nDataset statistics:")
    print(f"  - NORMAL: {normal} ({normal/len(logs)*100:.1f}%)")
    print(f"  - SUSPICIOUS: {suspicious} ({suspicious/len(logs)*100:.1f}%)")
    print(f"  - ANOMALY: {anomaly} ({anomaly/len(logs)*100:.1f}%)")