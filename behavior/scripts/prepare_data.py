import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
import os

def parse_ip_features(ip):
    parts = ip.split('.')
    if len(parts) == 4:
        return [int(p) for p in parts]
    return [0, 0, 0, 0]

def calculate_time_features(timestamp):
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    hour = dt.hour
    is_night = 1 if (hour < 6 or hour > 22) else 0
    is_weekend = 1 if dt.weekday() >= 5 else 0
    return hour, is_night, is_weekend

def detect_anomalies(logs_df):
    anomalies = []
    
    for idx, row in logs_df.iterrows():
        score = 0
        
        if row['is_night'] == 1:
            score += 3
            
        if row['action'] == 'failed_login':
            score += 4
            
        if row['ip_first_octet'] > 192 or row['ip_first_octet'] < 10:
            score += 2
            
        if 'confidential' in str(row.get('resource', '')).lower():
            score += 3
            
        anomalies.append(1 if score > 5 else 0)
    
    return anomalies

def prepare_training_data(input_json_path, output_dir='behavior/data'):
    with open(input_json_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    df = pd.DataFrame(logs)
    
    ip_features = df['ip'].apply(parse_ip_features)
    df['ip_first_octet'] = ip_features.apply(lambda x: x[0])
    df['ip_second_octet'] = ip_features.apply(lambda x: x[1])
    df['ip_third_octet'] = ip_features.apply(lambda x: x[2])
    df['ip_fourth_octet'] = ip_features.apply(lambda x: x[3])
    
    time_features = df['timestamp'].apply(calculate_time_features)
    df['hour'] = time_features.apply(lambda x: x[0])
    df['is_night'] = time_features.apply(lambda x: x[1])
    df['is_weekend'] = time_features.apply(lambda x: x[2])
    
    action_map = {
        'login': 0,
        'logout': 1,
        'read': 2,
        'download': 3,
        'failed_login': 4,
        'password_change': 5
    }
    df['action_code'] = df['action'].map(action_map).fillna(0)
    
    df['has_resource'] = df['resource'].notna().astype(int)
    
    df['anomaly'] = detect_anomalies(df)
    
    feature_columns = [
        'ip_first_octet',
        'ip_second_octet', 
        'ip_third_octet',
        'ip_fourth_octet',
        'hour',
        'is_night',
        'is_weekend',
        'action_code',
        'has_resource',
        'anomaly'
    ]
    
    os.makedirs(output_dir, exist_ok=True)
    
    final_df = df[feature_columns].copy()
    
    augmented_data = []
    for _ in range(30):
        for _, row in final_df.iterrows():
            new_row = row.copy()
            for col in feature_columns[:-1]:
                if col not in ['action_code', 'has_resource', 'is_night', 'is_weekend']:
                    noise = np.random.randint(-5, 6)
                    new_row[col] = max(0, min(255, new_row[col] + noise))
            augmented_data.append(new_row)
    
    augmented_df = pd.DataFrame(augmented_data)
    
    train_df, temp_df = train_test_split(augmented_df, test_size=0.3, random_state=42, stratify=augmented_df['anomaly'])
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42, stratify=temp_df['anomaly'])
    
    train_df.to_csv(f'{output_dir}/train.csv', index=False)
    val_df.to_csv(f'{output_dir}/validate.csv', index=False)
    test_df.to_csv(f'{output_dir}/test.csv', index=False)
    
    print(f"Data preparation complete!")
    print(f"Train samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    print(f"Anomaly ratio in training: {train_df['anomaly'].mean():.2%}")
    
    return train_df, val_df, test_df

if __name__ == "__main__":
    prepare_training_data('behavior/datasets/fake_bank_logs.json', 'behavior/data')
