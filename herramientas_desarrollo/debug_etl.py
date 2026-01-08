import sqlite3
import re

def remove_accents(input_str):
    s = input_str
    replacements = (
        ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"),
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ñ", "N"),
        ("Ü", "U"), ("ü", "u")
    )
    for a, b in replacements:
        s = s.replace(a, b)
    return s

def db_norm(s): return re.sub(r'[^A-Z0-9]', '', remove_accents(str(s)).upper())

conn = sqlite3.connect("cava_stats_v2.db")
c = conn.cursor()

print("--- DIAGNOSTIC START ---")

# 1. Check Rival 'SAN MARTIN (B)'
target = "SAN MARTIN (B)"
print(f"Target Rival: {target}")
print(f"Normalized Target: {db_norm(target)}")

c.execute("SELECT id, nombre FROM rivales")
all_rivals = c.fetchall()
found_id = None
for rid, rname in all_rivals:
    norm_r = db_norm(rname)
    if db_norm(target) in norm_r or norm_r in db_norm(target):
         print(f"MATCH FOUND in DB! ID={rid}, Name='{rname}', Norm='{norm_r}'")
         found_id = rid

if not found_id:
    print("CRITICAL: Rival not found in DB via normalization!")
else:
    # 2. Check Matches for this Rival
    print(f"\nChecking Matches for Rival ID {found_id}...")
    c.execute("""
        SELECT p.id, p.fecha, t.temporada, t.nombre
        FROM partidos p
        JOIN torneos t ON p.id_torneo = t.id
        WHERE p.id_rival = ?
    """, (found_id,))
    matches = c.fetchall()
    
    for m in matches:
        print(f"Match: ID={m[0]}, Fecha={m[1]}, Temp={m[2]}, Torneo={m[3]}")
        
    # 3. Check Linking Logic
    year_val = "2019"
    print(f"\nAttempting Link with Year '{year_val}'...")
    linked = False
    for m in matches:
        if str(year_val) in str(m[2]): # m[2] is temporada
            print(f"SUCCESS: Would link to Match {m[0]}")
            linked = True
    
    if not linked:
        print(f"FAILURE: No match found for year '{year_val}' (Check Temporada values!)")

print("--- DIAGNOSTIC END ---")
conn.close()
