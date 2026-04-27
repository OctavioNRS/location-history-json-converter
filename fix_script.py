with open("analyze_semantic_locations.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("analyze_semantic_locations.py", "w", encoding="utf-8") as f:
    for line in lines:
        if "'Hours_In_Home': round(avg_at_home, 2)," in line:
            f.write("              'Hours_In_Home': round(avg_at_home, 2),\n")
            f.write("              'Hours_Outside': round(1.0 - round(avg_at_home, 2), 2)\n")
        elif "'Hours_Outside': round(avg_away, 2)" in line:
            continue
        else:
            f.write(line)
