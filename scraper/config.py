DEBUG = False # Use fixed list of urls

# ----- Category Names -----

INDEX = "https://wiki.warthunder.com/index.php?curid="
API_URL = "https://wiki.warthunder.com/api.php?action=query&format=json&generator=categorymembers&gcmlimit=max&gcmtitle="

LIGHT_TANKS = "Category:Light_tanks"
MEDIUM_TANKS = "Category:Medium_tanks"
HEAVY_TANKS = "Category:Heavy_tanks"
TANKS_DESTROYERS = "Category:Tank_destroyers"
SPAA = "Category:Anti-aircraft_vehicles"

CATEGORIES = [LIGHT_TANKS, MEDIUM_TANKS, HEAVY_TANKS, TANKS_DESTROYERS, SPAA]




# ----- Specs Settings -----

AB = True # Specs for AB [True] or RB/SB [False]

# For determine specs categories check categories.png
SPECS_RESEARCH = True
SPECS_SURVIVABILITY = True
SPECS_MOBILITY = True
SPECS_ECONOMY= True
SPECS_ARMAMENT = True
SPECS_PROS_AND_CONS = True