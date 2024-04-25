# Pick the best ADC in League of Legends
Web scraper for u.gg that will determine the best ADC for your botlane matchup.

The code uses the winrates for counter-pick and ADC-support duos to run a binomial distribution calculation, and will then
total the scores for each ADC. The final results will be on a scale of 0-100, with 100 being the statistically strongest
ADC for the specific matchup.

# Prerequisites
1. Selenium
2. Scipy
3. Pprint (Optional, will require editing line 73)

