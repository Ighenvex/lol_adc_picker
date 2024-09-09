from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scipy.stats import binom
import pprint as pp
import multiprocessing as mp

def process_matches(matches: str):
    "Removes commas, returns an int"
    return int(matches.replace(",", ""))

def create_driver(port):
    "Returns a selenium chromedriver on port = port"
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Run Chrome in headless mode
    chrome_options.add_argument('log-level=3') # Hides non-essential warnings
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument(f'--port={port}')
    
    driver = Chrome(options=chrome_options) #Selenium 4.6+ auto-manages the driver
    driver.implicitly_wait(3)
    return driver

def scrape_adc(adc, driver_port, mp_queue):
    driver = create_driver(driver_port)
    driver.get(f"https://u.gg/lol/champions/{adc}/matchups")
    
    rows = driver.find_elements(By.CSS_SELECTOR, "div.rt-tr-group")
    
    adc_ratings = {}
    for row in rows:
        champion = row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(2)").text
        wr = float(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(3)").text[:-1]) / 100
        matches = process_matches(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(9)").text)
        adc_ratings[champion] = (round(1 - binom.cdf(round(wr * matches), matches, 0.5), 5), matches)

    driver.quit()
    mp_queue.put(["adc", adc_ratings])

def scrape_support(supp, driver_port, mp_queue):
    driver = create_driver(driver_port)
    driver.get(f"https://u.gg/lol/champions/{supp}/duos")
    rows = driver.find_elements(By.CSS_SELECTOR, "div.rt-tr-group")
    
    supp_ratings = {}
    for row in rows:
        champion = row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(3)").text
        wr = float(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(4)").text[:-1]) / 100
        matches = process_matches(row.find_element(By.CSS_SELECTOR, f"div.rt-td:nth-of-type(10)").text)
        supp_ratings[champion] = (round(binom.cdf(round(wr * matches), matches, 0.5), 5), matches)

    driver.quit()
    mp_queue.put(["supp", supp_ratings])

def combine_ratings(counters, duos):
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
    not_matched.remove(enemy_adc.title())

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

    queue = mp.Queue()

    enemy_adc = input("Enemy ADC: ")
    ally_supp = input("Ally Support: ")

    p1 = mp.Process(target=scrape_adc, args=(enemy_adc, 9515, queue))
    p2 = mp.Process(target=scrape_support, args=(ally_supp, 9516, queue))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    x, y = queue.get(), queue.get()
    # not guaranteed which dict was added to the queue first
    if x[0] == "adc":
        counters, duos = x[1], y[1]
    else:
        counters, duos = y[1], x[1]

    final_ratings, not_matched = combine_ratings(counters, duos)

    print()
    pp.pprint(final_ratings)
    print(f"\nUnable to match: {not_matched}") if not_matched else None
    input(f"\nPress Enter to exit.")
