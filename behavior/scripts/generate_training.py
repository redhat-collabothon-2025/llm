import json
from collections import defaultdict

def generate_training_dataset(input_log_file, output_training_file):
    with open(input_log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    user_events = defaultdict(list)
    for event in logs:
        user = event['user_id']
        line = f"{event['timestamp']}: {event['action']} from IP {event['ip']}"
        if 'resource' in event:
            line += f", resource {event['resource']}"
        user_events[user].append(line)

    training_data = []
    for user, events in user_events.items():
        input_text = "\n".join(events)
        instr = {
            "instruction": f"Analyze security risk for user {user} based on events.",
            "input": input_text,
            "output": "Risk level (0-10), anomalies detected, security recommendations."
        }
        training_data.append(instr)

    with open(output_training_file, 'w', encoding='utf-8') as f_out:
        json.dump(training_data, f_out, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    generate_training_dataset('datasets/fake_bank_logs.json', 'datasets/training_dataset.json')
    print("Training dataset generated at datasets/training_dataset.json")
