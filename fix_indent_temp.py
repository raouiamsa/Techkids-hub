# Read the file
with open('apps/ai-brain/benchmarking/comp2_agents_llm_comparaison.py', 'r') as f:
    lines = f.readlines()

# Fix indentation: lines 425-621 (0-indexed: 424-620) need +4 spaces
# These are the lines that should be inside the repeat loop
for i in range(424, 621):  # 425-621 in 1-indexed = 424-620 in 0-indexed
    line = lines[i]
    # Skip empty lines or lines with only whitespace
    if line.strip():
        # Add 4 spaces to the indentation
        lines[i] = '    ' + line

# Write back
with open('apps/ai-brain/benchmarking/comp2_agents_llm_comparaison.py', 'w') as f:
    f.writelines(lines)

print("✓ Fixed indentation for repeat loop")
