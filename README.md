# best-adcs
Will generate the best ADCs using live data from u.gg if the enemy ADC and ally support has already been chosen.

The code uses the winrates for counter-pick and ADC-support duos to run a binomial distribution calculation, and will then
total the scores for each ADC. The final results will be on a scale of 0-100, with 100 being the statistically strongest
ADC for the specific matchup.

# Prerequisites
1. Selenium
2. Pprint (Optional, will require editing line 86)

# Running the Code:
Make sure that the path to your chromedriver executable is correct.

