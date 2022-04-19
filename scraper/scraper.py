import os
import scrapy
import requests
import config

from decimal import DivisionByZero
from config import INDEX, API_URL, AB, DEBUG, CATEGORIES
from helpers import RmvSpaces, toFloat
from progress.bar import ShadyBar
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
from contextlib import suppress


# ----- Page parsing ----
class Tanks(scrapy.Spider):
    name = 'Tanks'
    start_urls = []
    bar = None

    def parse(self, response):
        if self.bar == None:
            self.bar = ShadyBar('Collecting tanks...', max=len(self.start_urls), suffix = '%(index)d/%(max)d - ETA: %(eta_td)s')

        sp = BeautifulSoup(response.text, 'lxml')
        specs_boxes = sp.find_all(class_='specs_info')
        
        tank = {
            # ----- General Info ----
            'Name': response.css('.general_info_name::text').get(),
            'Nation': response.css('.general_info_nation > a:nth-child(2)::text').get(),
            'Rank': response.css('.general_info_rank > a:nth-child(1)::text').get().replace(' Rank', ''),
            'Rating': response.css('.general_info_br > table:nth-child(2) > tr:nth-child(2) > td:nth-child(1)::text').get().replace('.', ',') if AB else response.css('.general_info_br > table:nth-child(2) > tr:nth-child(2) > td:nth-child(2)::text').get().replace('.', ','),
            'Type': response.css('.general_info_class > div:nth-child(3) > a:nth-child(1)::text').get() if response.css('.general_info_class > div:nth-child(2) > a:nth-child(1)::text').get() == 'PREMIUM' else response.css('.general_info_class > div:nth-child(2) > a:nth-child(1)::text').get(),
            'Premium': '•' if response.css('.general_info_class > div:nth-child(2) > a:nth-child(1)::text').get() == 'PREMIUM' else '',
        }

        # ----- Research ----
        if config.SPECS_RESEARCH:
            if response.css('.small > a:nth-child(1)').get() != None:
                tank['RP'] = 0
                tank['Price'] = 0
                tank['Free'] = 'Bundle or Gift'
            elif response.css('.general_info_price_research > span:nth-child(2)').get() == None:
                tank['RP'] = 0
                tank['Price'] = int(response.css('.general_info_price_buy > span:nth-child(2)::text').get().replace(' ', ''))
                tank['Free'] = ''
            elif response.css('.general_info_price_research > span:nth-child(2)::text').get() == 'Free':
                tank['RP'] = 0
                tank['Price'] = 0
                tank['Free'] = 'Free'
            else:
                tank['RP'] = int(response.css('.general_info_price_research > span:nth-child(2)::text').get().replace(' ', ''))
                tank['Price'] = int(response.css('.general_info_price_buy > span:nth-child(2)::text').get().replace(' ', ''))
                tank['Free'] = ''

        # ----- Survivability ----
        if config.SPECS_SURVIVABILITY:
            # ----- Define Dict Entries ----
            tank['Surv.Mods'] = ''
            tank['Armour.Hull.front'] = ''
            tank['Armour.Hull.side'] = ''
            tank['Armour.Hull.back'] = ''
            tank['Armour.Turret.front'] = ''
            tank['Armour.Turret.side'] = ''
            tank['Armour.Turret.back'] = ''
            tank['Crew'] = ''
            tank['Visibility'] = ''

            # ----- Help *username* find a some armour ----
            if 'Armour' in specs_boxes[0].text:
                surv_box = specs_boxes[0]
                mods = []

                for feature in surv_box.contents[1].contents:
                    mods.append(feature.contents[3].text)

                tank['Surv.Mods'] = ' | '.join(mods)
                
                Hull = surv_box.contents[3].contents[1].contents[3].contents[1].text.split(' / ')
                Turret = surv_box.contents[3].contents[1].contents[5].contents[1].text.split(' / ')

                tank['Armour.Hull.front'] = Hull[0]
                tank['Armour.Hull.side'] = Hull[1]
                tank['Armour.Hull.back'] = Hull[2]
                tank['Armour.Turret.front'] = Turret[0]
                tank['Armour.Turret.side'] = Turret[1]
                tank['Armour.Turret.back'] = Turret[2]
                
                tank['Crew'] = surv_box.contents[3].contents[3].contents[1].contents[1].text.replace(' people', '')
                tank['Visibility'] = surv_box.contents[3].contents[5].contents[1].contents[1].text.replace('\xa0%', '')
            
        # ----- Mobility ----
        if config.SPECS_MOBILITY:
            mobility_box = specs_boxes[1]
            
            if AB:          
                tank['Speed.Forward'] = mobility_box.contents[3].contents[1].contents[3].contents[1].contents[0].split(' ', 3)[0]
                tank['Speed.Back'] = mobility_box.contents[3].contents[1].contents[3].contents[1].contents[0].split(' ', 3)[2]
                tank['HP'] = mobility_box.contents[3].contents[7].contents[3].contents[1].contents[0].split(' hp', 1)[0].replace(' ', '')
                tank['HP/t'] = mobility_box.contents[3].contents[9].contents[3].contents[1].contents[0].split(' ', 1)[0].replace('.', ',')
            else:          
                tank['Speed.Forward'] = mobility_box.contents[3].contents[1].contents[5].contents[1].contents[0].split(' ', 3)[0]
                tank['Speed.Back'] = mobility_box.contents[3].contents[1].contents[5].contents[1].contents[0].split(' ', 3)[2]
                tank['HP'] = mobility_box.contents[3].contents[7].contents[5].contents[1].contents[0].split(' hp', 1)[0].replace(' ', '')
                tank['HP/t'] = mobility_box.contents[3].contents[9].contents[5].contents[1].contents[0].split(' ', 1)[0].replace('.', ',')

            tank['Weight'] = mobility_box.contents[3].parent.contents[3].contents[5].contents[1].contents[1].text.replace('.', ',')[:-2]

        # ----- Economy ----
        if config.SPECS_ECONOMY:
            econ_box = specs_boxes[2]
            repair_cost = None
            reward = None

            for databox in econ_box.contents[1].contents:
                if 'Repair cost' in databox.text:
                    repair_cost = databox
                elif 'Reward for battle' in databox.text:
                    reward = databox


            if AB:
                tank['Eco.Repair'] = RmvSpaces(repair_cost.contents[3].contents[1].text)

                if tank['Premium'] == '•':
                    tank['Eco.Reward.Lions'] = toFloat(str(2 * float(reward.contents[3].contents[1].text.replace(' 2 ×\xa0', '').split(' / ')[0]) / 100))
                    tank['Eco.Reward.RP'] = toFloat(str(2 * float(reward.contents[5].contents[1].text.replace(' 2 ×\xa0', '').split(' / ')[0]) / 100))
                else:
                    tank['Eco.Reward.Lions'] = toFloat(str(float(reward.contents[3].contents[1].text.split(' / ')[0]) / 100))
                    tank['Eco.Reward.RP'] = toFloat(str(float(reward.contents[5].contents[1].text.split(' / ')[0]) / 100))
            else:
                tank['Eco.Repair'] = RmvSpaces(repair_cost.contents[5].contents[1].text)

                if tank['Premium'] == '•':
                    tank['Eco.Reward.Lions'] = toFloat(str(2 * float(reward.contents[3].contents[1].text.split(' / ')[1]) / 100))
                    tank['Eco.Reward.RP'] = toFloat(str(2 * float(reward.contents[5].contents[1].text.split(' / ')[1]) / 100))
                else:
                    tank['Eco.Reward.Lions'] = toFloat(str(float(reward.contents[3].contents[1].text.split(' / ')[1]) / 100))
                    tank['Eco.Reward.RP'] = toFloat(str(float(reward.contents[5].contents[1].text.split(' / ')[1]) / 100))

        # ----- Armament ----
        if config.SPECS_ARMAMENT:
            #  ----- Defining Empty List Items ----
            tank['Arma.Mods'] = ''

            tank['Arma.Main.Caliber'] = ''
            tank['Arma.Main.Ammo'] = ''
            tank['Arma.Main.Rate'] = ''
            tank['Arma.Main.Reload'] = ''
            tank['Arma.Main.Mods'] = ''
            tank['Arma.Main.Penetration'] = 0

            tank['MG.1st.Caliber'] = ''
            tank['MG.1st.Ammo'] = ''
            tank['MG.1st.Rate'] = ''
            tank['MG.1st.Reload'] = ''

            tank['MG.2nd.Caliber'] = ''
            tank['MG.2nd.Ammo'] = ''
            tank['MG.2nd.Rate'] = ''
            tank['MG.2nd.Reload'] = ''

            #  ----- Defining HTML Elements ----
            arma_mods = specs_boxes[3]
            arma_main_box = specs_boxes[4]
            arma_mg_first = None
            arma_mg_second = None

            with suppress(IndexError):
                arma_mg_first = specs_boxes[5]
                arma_mg_second = specs_boxes[6]
                
            
            #  ----- Penetration Search  ----
            wikitables = sp.find_all(class_='wikitable')
            penetrations = []

            for table in wikitables:
                if 'Penetration statistics' in table.text:
                    for mm in table.contents[6:]:
                        if mm != '\n':
                            try:
                                penetrations.append(int(mm.contents[7].text))
                            except(ValueError):
                                penetrations.append(0)

            #  ----- Working with Mods ----
            mods = []
            main_mods = []            

            with suppress(IndexError):
                if 'Setup 1:' not in arma_mods.text:
                    for feature in arma_mods.contents[0].contents:
                        mods.append(feature.contents[3].contents[0])

            with suppress(IndexError):
                for feature in arma_main_box.contents[3].contents:
                    main_mods.append(feature.contents[3].text)
                
            #  ----- Main Armament ----
            tank['Arma.Mods'] = ' | '.join(mods)
            try:
                tank['Arma.Main.Caliber'] = toFloat(str(float(arma_main_box.contents[1].contents[-1].text.split(' ', 1)[0])))
            except:
                tank['Arma.Main.Caliber'] = ''
            tank['Arma.Main.Mods'] = ' | '.join(main_mods)
            tank['Arma.Main.Penetration'] = max(penetrations)

            for spec in arma_main_box.contents[5].contents:
                if spec.text != '\n':
                    match spec.contents[1].contents[0].text:
                        case 'Ammunition':
                            tank['Arma.Main.Ammo'] = RmvSpaces(spec.contents[1].contents[1].text.replace('rounds', ''))
                        case 'Fire rate':
                            tank['Arma.Main.Rate'] = RmvSpaces(spec.contents[1].contents[1].text.replace('shots/min', ''))
                        case 'Reload':
                            tank['Arma.Main.Reload'] = toFloat(spec.contents[-2].contents[1].text.split(' ', 1)[0])  

            #  ----- First Machine Gun [Kelly] ----
            if arma_mg_first != None:
                try:
                    tank['MG.1st.Caliber'] = toFloat(str(float(arma_mg_first.contents[1].text.split(' ', 1)[0])))
                except:
                    tank['MG.1st.Caliber'] = ''
                for spec in arma_mg_first.contents[5].contents:
                    if spec.text != '\n':
                        match spec.contents[1].contents[0].text:
                            case 'Ammunition':
                                tank['MG.1st.Ammo'] = RmvSpaces(spec.contents[1].contents[1].text.replace('rounds', ''))
                            case 'Fire rate':
                                tank['MG.1st.Rate'] = RmvSpaces(spec.contents[1].contents[1].text.replace('shots/min', ''))
                            case 'Reload':
                                tank['MG.1st.Reload'] = toFloat(spec.contents[-2].contents[1].text.split(' ', 1)[0])

            #  ----- Second Machine Gun ----
            if arma_mg_second != None:
                try:
                    tank['MG.2nd.Caliber'] = toFloat(str(float(arma_mg_second.contents[1].text.split(' ', 1)[0])))
                except:
                    tank['MG.2nd.Caliber'] = ''
                for spec in arma_mg_second.contents[5].contents:
                    if spec.text != '\n':
                        match spec.contents[1].contents[0].text:
                            case 'Ammunition':
                                tank['MG.2nd.Ammo'] = RmvSpaces(spec.contents[1].contents[1].text.replace('rounds', ''))
                            case 'Fire rate':
                                tank['MG.2nd.Rate'] = RmvSpaces(spec.contents[1].contents[1].text.replace('shots/min', ''))
                            case 'Reload':
                                tank['MG.2nd.Reload'] = toFloat(spec.contents[-2].contents[1].text.split(' ', 1)[0])

        # ----- Pros & Cons ----
        if config.SPECS_PROS_AND_CONS:
            uls = sp.find_all('ul')
            tank['PROS_CONS.Pros'] = 0
            tank['PROS_CONS.Cons'] = 0
            tank['PROS_CONS.Ratio'] = 0.00

            for ul in uls:
                if ul.previous_element.previous_element.previous_element == 'Pros:':
                    filtered = list(filter(lambda elem: elem.text != '\n', ul.contents))
                    tank['PROS_CONS.Pros'] = len(filtered)
                elif ul.previous_element.previous_element.previous_element == 'Cons:':
                    filtered =  list(filter(lambda elem: elem.text != '\n', ul.contents))
                    tank['PROS_CONS.Cons'] = len(filtered)

            with(suppress(DivisionByZero)):
                tank['PROS_CONS.Ratio'] = round(tank['PROS_CONS.Pros'] / tank['PROS_CONS.Cons'], 2)
        
        # os.system('cls')
        self.bar.next()
        # print(f'\nCurrent URL -> {response.url}')
        yield tank

filename = 'Tanks.csv'
if os.path.exists(filename):
    os.remove(filename)

# ----- Collecting page IDs ----
class IdCollector():
    os.system('cls')
    
    if DEBUG:
        Tanks.start_urls.append('https://wiki.warthunder.com/AEC_AA')
    else:
        for category in CATEGORIES:
            r = requests.get(API_URL + category)
            json = r.json()
            for page in json['query']['pages']:
                Tanks.start_urls.append(INDEX + page)

        print('URLs Collected...')
    
    # ----- Start Scraping Scrapy Scraper -----
    process = CrawlerProcess(settings={
        'LOG_LEVEL': 'CRITICAL',
        'FEEDS': {
            filename: {'format': 'csv'},
        },
    })
    
    process.crawl(Tanks)
    process.start()

    print('\n\nPress any key to exit...')
    input()