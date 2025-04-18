from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from scipy.stats import binom
import pprint as pp
from concurrent.futures import ProcessPoolExecutor

def process_matches(matches: str):
    "Removes commas, returns an int"
    return int(matches.replace(",", ""))

def create_driver():
    "Returns a selenium chromedriver on port = port"
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Run Chrome in headless mode
    chrome_options.add_argument('log-level=3') # Hides non-essential warnings
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors')

    prefs = {"profile.managed_default_content_settings.images": 2,
         "profile.managed_default_content_settings.fonts": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = Chrome(options=chrome_options) #Selenium 4.6+ auto-manages the driver
    driver.implicitly_wait(3)
    
    return driver

def scrape_adc(adc):
    driver = create_driver()
    driver.get(f"https://u.gg/lol/champions/{adc}/matchups")
    
    rows = driver.find_elements(By.CSS_SELECTOR, "div.rt-tr-group")
    
    adc_ratings = {}
    for row in rows:
        tds = row.find_elements(By.CSS_SELECTOR, "div.rt-td")
        if len(tds) >= 9:
            champion = tds[1].text
            wr = float(tds[2].text.rstrip('%')) / 100
            matches = process_matches(tds[8].text)
            adc_ratings[champion] = (
                round(1 - binom.cdf(round(wr * matches), matches, 0.5), 5),
                matches
            )

    driver.quit()
    return adc_ratings

def scrape_support(supp):
    driver = create_driver()
    driver.get(f"https://u.gg/lol/champions/{supp}/duos")
    rows = driver.find_elements(By.CSS_SELECTOR, "div.rt-tr-group")
    
    supp_ratings = {}
    for row in rows:
        tds = row.find_elements(By.CSS_SELECTOR, "div.rt-td")
        if len(tds) >= 10:
            champion = tds[2].text
            wr = float(tds[3].text.rstrip('%')) / 100
            matches = process_matches(tds[9].text)
            supp_ratings[champion] = (
                round(binom.cdf(round(wr * matches), matches, 0.5), 5),
                matches
            )

    driver.quit()
    return supp_ratings

def combine_ratings(counters: dict, duos: dict):
    "Returns final sorted dict of ratings, and the set of unmatched champions"

    combined_ratings = {}
    for champ in set(counters).intersection(duos):
        adcScore, adcMatches = counters[champ]
        suppScore, suppMatches = duos[champ]
        total_matches = adcMatches + suppMatches
        combined_ratings[champ] = round(100 * ((adcScore * adcMatches / total_matches) + (suppScore * suppMatches / total_matches)), 2)
 
    sorted_ratings = dict(sorted(combined_ratings.items(), key = lambda x: x[1], reverse=True)) # Sorts by highest rating

    not_matched = set(counters).difference(duos)
    for champ in set(duos).difference(counters):
        not_matched.add(champ)
    not_matched.remove(enemy_adc.title()) if enemy_adc.title() in not_matched else None

    return sorted_ratings, not_matched

def _pprint_dict(self, object, stream, indent, allowance, context, level):
    """
    Overwrites the default pprint for dictionaries to remove the automatic
    sorting with pprint
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

if __name__ == "__main__":
    pp.PrettyPrinter._dispatch[dict.__repr__] = _pprint_dict

    enemy_adc = input("Enemy ADC: ")
    ally_supp = input("Ally Support: ")

    with ProcessPoolExecutor() as executor:
        future_adc = executor.submit(scrape_adc, enemy_adc)
        future_supp = executor.submit(scrape_support, ally_supp)

        adcs = future_adc.result()
        supports = future_supp.result()

    final_ratings, not_matched = combine_ratings(counters=adcs, duos=supports)

    print()
    pp.pprint(final_ratings)
    print(f"\nUnable to match: {not_matched}") if not_matched else None
    input(f"\nPress Enter to exit.")
