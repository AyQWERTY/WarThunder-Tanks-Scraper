# Introduction
To develop the scraper, I created a Mind Map. With this, you can see what data my scraper collects and what categories are available.

![Scraper Mind Map](https://github.com/AyQWERTY/WarThunder-Tanks-Scraper/raw/main/categories.png)
## Using
You have three options on how to use this:

 1. Download the source code and compile it
 2. Download the compiled .exe file from [Releases](https://github.com/AyQWERTY/WarThunder-Tanks-Scraper/releases)
 3. Download the CSV File (data for Arcade) from [Releases](https://github.com/AyQWERTY/WarThunder-Tanks-Scraper/releases)

# Installation
### Required packages

    pip install scrapy progress beautifulsoup4

### Config
You can edit `config.py` to disable certain categories of information to be collected.

    AB = True  # Specs for AB [True] or RB/SB [False]
        
    SPECS_RESEARCH = True    
    SPECS_SURVIVABILITY = True    
    SPECS_MOBILITY = True    
    SPECS_ECONOMY = True    
    SPECS_ARMAMENT = True    
    SPECS_PROS_AND_CONS = True

Also here you can choose which data will be collected: for arcade battles or for realistic ones.
