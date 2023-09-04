from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from scipy.stats import binom
import pprint as pp

adcs = {"seraphine", "nilah", "kalista", "twitch", "ashe", "aphelios", "vayne", 
        "kog'maw", "draven", "yasuo", "jhin", "zeri", "sivir", "lucian", "xayah",
        "samira", "miss fortune", "ezreal", "jinx", "kai'sa", "tristana", "caitlyn", 
        "varus", "swain", "ziggs"}

def process_matches(matches: str):
    """Will get rid of commas and return an int"""
    return int(matches.replace(",", ""))

def scrape_link(url, ally):
    """ally is a bool"""
    options = Options()
    # options.add_argument("--headless") # Run Chrome in headless mode
    options.add_argument('log-level=3') # Hides non-essential warnings
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--ignore-certificate-errors')
    service = Service("chromedriver.exe") # Path to Chromedriver executable
    driver = webdriver.Chrome(service=service, options=options)
    # driver.implicitly_wait(1)
    driver.get(url)

    rows = driver.find_elements(By.CSS_SELECTOR, "div.rt-tr-group")
    if ally: # This is just for setting values used in getting the data
        x, y, z = 3, 4, 10
    else:
        x, y, z = 2, 3, 9
    
    output = {}
    for row in rows:
        champion = row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type({x})").text
        wr = float(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type({y})").text[:-1]) / 100
        matches = process_matches(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type({z})").text)
        if ally:
            output[champion] = round(binom.cdf(round(wr * matches), matches, 0.5), 5)
        else:
            output[champion] = round(1 - binom.cdf(round(wr * matches), matches, 0.5), 5)
    return output

def get_counterpicks(opp_adc):
    res = scrape_link(f"https://u.gg/lol/champions/{opp_adc}/matchups", False)
    return res

def get_duos(ally_supp):
    res = scrape_link(f"https://u.gg/lol/champions/{ally_supp}/duos", True)
    return res

def _pprint_dict(self, object, stream, indent, allowance, context, level):
    """
    Overwrites the default pprint for dictionaries to remove the automatic
    sorting on pprint
    """
    write = stream.write
    write('{')
    if self._indent_per_level > 1:
        write((self._indent_per_level - 1) * ' ')
    length = len(object)
    if length:
        self._format_dict_items(object.items(), stream, indent, allowance + 1,
                                context, level)
    write('}')

pp.PrettyPrinter._dispatch[dict.__repr__] = _pprint_dict

enemy_adc = input("Enemy ADC: ")
ally_supp = input("Ally Support: ")
counters = get_counterpicks(enemy_adc)
duos = get_duos(ally_supp)

final_ratings = {x: round(50 * (counters.get(x, 0) + duos.get(x, 0)), 5)
                for x in set(counters).intersection(duos)}
sorted_ratings = dict(sorted(final_ratings.items(), key = lambda x: x[1], reverse=True)) # Sorts by highest rating

not_matched = set(counters).difference(duos)
for champ in set(duos).difference(counters):
    not_matched.add(champ)
not_matched.remove(enemy_adc.title())

print()
pp.pprint(sorted_ratings)
print(f"\nUnable to match: {not_matched}")
