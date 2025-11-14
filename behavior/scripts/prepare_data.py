import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
import os

def parse_ip_features(ip):
    parts = str(ip).split('.')
    if len(parts) == 4:
        try:
            return [int(p) for p in parts]
        except:
            return [0, 0, 0, 0]
    return [0, 0, 0, 0]

def calculate_time_features(timestamp):
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    hour = dt.hour
    is_night = 1 if (hour < 6 or hour > 22) else 0
    is_weekend = 1 if dt.weekday() >= 5 else 0
    is_business_hours = 1 if (9 <= hour <= 18) else 0
    return hour, is_night, is_weekend, is_business_hours

def detect_anomalies(logs_df):
    anomalies = []
    employee_ips = {}
    employee_devices = {}
    
    for idx, row in logs_df.iterrows():
        score = 0
        emp_id = row.get('employee_id', 'unknown')
        
        if row['is_night'] == 1:
            score += 3
            
        if row['action_code'] == 5:
            score += 4
            
        if row['ip_first_octet'] >= 80 and row['ip_first_octet'] < 192:
            score += 2
            
        if pd.notna(row.get('resource_accessed')):
            res = str(row['resource_accessed']).lower()
            if any(word in res for word in ['confidential', 'salary', 'layoff', 'database', 'backup', 'dump']):
                score += 3
                
        if emp_id not in employee_ips:
            employee_ips[emp_id] = set()
        employee_ips[emp_id].add(row['ip_address'])
        if len(employee_ips[emp_id]) > 2:
            score += 2
            
        if emp_id not in employee_devices:
            employee_devices[emp_id] = set()
        if pd.notna(row.get('device_fingerprint')):
            employee_devices[emp_id].add(row['device_fingerprint'])
            if len(employee_devices[emp_id]) > 2:
                score += 1
                
        if row['action_code'] == 3 and row['has_resource'] == 1:
            score += 1
            
        if row.get('geo_location') == 'Unknown':
            score += 2
            
        if 'curl' in str(row.get('user_agent', '')).lower() or 'python' in str(row.get('user_agent', '')).lower():
            score += 2
            
        anomalies.append(1 if score >= 4 else 0)
    
    return anomalies

def prepare_training_data(input_json_path, output_dir='behavior/data'):
    with open(input_json_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    df = pd.DataFrame(logs)
    
    df['ip_address'] = df['ip_address'].astype(str)
    ip_features = df['ip_address'].apply(parse_ip_features)
    df['ip_first_octet'] = ip_features.apply(lambda x: x[0])
    df['ip_second_octet'] = ip_features.apply(lambda x: x[1])
    df['ip_third_octet'] = ip_features.apply(lambda x: x[2])
    df['ip_fourth_octet'] = ip_features.apply(lambda x: x[3])
    
    time_features = df['timestamp'].apply(calculate_time_features)
    df['hour'] = time_features.apply(lambda x: x[0])
    df['is_night'] = time_features.apply(lambda x: x[1])
    df['is_weekend'] = time_features.apply(lambda x: x[2])
    df['is_business_hours'] = time_features.apply(lambda x: x[3])
    
    action_map = {
        'login': 0,
        'logout': 1,
        'read': 2,
        'download': 3,
        'upload': 4,
        'failed_login': 5,
        'password_change': 6,
        'delete': 7
    }
    df['action_code'] = df['action_type'].map(action_map).fillna(0)
    
    df['has_resource'] = df['resource_accessed'].notna().astype(int)
    
    df['response_code'] = df['response_code'].fillna(200).astype(int)
    df['is_failed_request'] = (df['response_code'] >= 400).astype(int)
    
    df['anomaly'] = detect_anomalies(df)
    
    feature_columns = [
        'ip_first_octet',
        'ip_second_octet', 
        'ip_third_octet',
        'ip_fourth_octet',
        'hour',
        'is_night',
        'is_weekend',
        'is_business_hours',
        'action_code',
        'has_resource',
        'is_failed_request',
        'anomaly'
    ]
    
    os.makedirs(output_dir, exist_ok=True)
    
    final_df = df[feature_columns].copy()
    
    print(f"\nOriginal data anomaly count: {final_df['anomaly'].sum()} out of {len(final_df)}")
    
    augmented_data = []
    for _ in range(25):
        for _, row in final_df.iterrows():
            new_row = row.copy()
            
            if np.random.random() < 0.20:
                new_row['anomaly'] = 1
                new_row['is_night'] = 1
                new_row['is_business_hours'] = 0
                new_row['ip_first_octet'] = np.random.choice([85, 176, 203, 198])
                new_row['action_code'] = np.random.choice([3, 5])
                new_row['has_resource'] = 1
            
            for col in feature_columns[:-1]:
                if col not in ['action_code', 'has_resource', 'is_night', 'is_weekend', 'is_business_hours', 'is_failed_request', 'anomaly']:
                    noise = np.random.randint(-5, 6)
                    new_row[col] = max(0, min(255, new_row[col] + noise))
            
            augmented_data.append(new_row)
    
    augmented_df = pd.DataFrame(augmented_data)
    
    anomaly_count = augmented_df['anomaly'].sum()
    total_count = len(augmented_df)
    
    if anomaly_count < total_count * 0.15:
        indices_to_flip = augmented_df[augmented_df['anomaly'] == 0].sample(
            n=int(total_count * 0.20 - anomaly_count), 
            random_state=42
        ).index
        augmented_df.loc[indices_to_flip, 'anomaly'] = 1
    
    train_df, temp_df = train_test_split(
        augmented_df, 
        test_size=0.3, 
        random_state=42, 
        stratify=augmented_df['anomaly']
    )
    val_df, test_df = train_test_split(
        temp_df, 
        test_size=0.5, 
        random_state=42, 
        stratify=temp_df['anomaly']
    )
    
    train_df.to_csv(f'{output_dir}/train.csv', index=False)
    val_df.to_csv(f'{output_dir}/validate.csv', index=False)
    test_df.to_csv(f'{output_dir}/test.csv', index=False)
    
    print(f"\nData preparation complete!")
    print(f"Train samples: {len(train_df)} (anomalies: {train_df['anomaly'].sum()}, {train_df['anomaly'].mean():.2%})")
    print(f"Validation samples: {len(val_df)} (anomalies: {val_df['anomaly'].sum()}, {val_df['anomaly'].mean():.2%})")
    print(f"Test samples: {len(test_df)} (anomalies: {test_df['anomaly'].sum()}, {test_df['anomaly'].mean():.2%})")
    
    return train_df, val_df, test_df

if __name__ == "__main__":
    prepare_training_data('../datasets/employee_activity_logs.json', '../data')
