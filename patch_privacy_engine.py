with open('stroke_risk_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'annotated_frame = frame.copy()' in l:
        lines.insert(i+1, "        if getattr(config, 'PRIVACY_MODE', False):\n            import numpy as np\n            annotated_frame = np.zeros_like(annotated_frame)\n")
        break

with open('stroke_risk_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Successfully inserted privacy mode hook')
