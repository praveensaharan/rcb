from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
from fastapi import FastAPI, HTTPException
from uuid import uuid4
from pydantic import BaseModel
from redis import Redis
import json
import re
from fastapi import BackgroundTasks

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

redis = Redis.from_url(
    "redis://default:8tsTMWeUZNGI2FutCPKJd9aVJUVGtz9g@redis-12696.c80.us-east-1-2.ec2.redns.redis-cloud.com:12696")


class CoinRequest(BaseModel):
    coins: list[str]


class CoinMarketCap:
    def __init__(self):
        pass

    def make_request(self, coin_name):
        url = f"https://coinmarketcap.com/currencies/{coin_name.lower()}/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Error making request: {e}")
            return None

    def extract_text(self, element, default=''):
        return element.text.strip() if element else default

    def extract_href(self, element, default=''):
        return element.get('href') if element else default

    def clean_number(self, number_str):
        return re.sub(r'[^\d.]', '', number_str) if number_str else None

    def scrape_data(self, coin_name, job_id):
        content = self.make_request(coin_name)
        if content is None:
            return {"coin": coin_name, "output": {}}

        soup = BeautifulSoup(content, 'html.parser')

        price_element = soup.find(
            'span', class_='sc-d1ede7e3-0 fsQm base-text')
        price = self.clean_number(
            self.extract_text(price_element).replace('$', ''))

        price_change = None
        div_element = soup.find(
            'div', class_='sc-d1ede7e3-0 kzFEmO')
        if div_element is not None:

            p_element = div_element.find(
                'p', class_=lambda x: x and 'sc-71024e3e-0' in x)

            if p_element:
                price_change_text = p_element.get_text().split('%')[0]
                price_change = float(price_change_text)
                price_change_color = p_element.get('color')
                if price_change_color == 'red':
                    price_change = -abs(price_change)

        market_cap_elements = soup.find_all(
            'dd', class_='sc-d1ede7e3-0 hPHvUM base-text')
        market_cap = self.clean_number(self.extract_text(market_cap_elements[0]).replace(
            '$', '').replace(',', '').split('%')[1])
        market_cap_rank = self.extract_text(soup.find_all(
            'span', class_='text slider-value rank-value')[0]).replace('#', '')

        volume = self.clean_number(self.extract_text(market_cap_elements[1]).replace(
            '$', '').replace(',', '').split('%')[1])
        volume_rank = self.extract_text(soup.find_all(
            'span', class_='text slider-value rank-value')[1]).replace('#', '')

        volume_change = self.clean_number(self.extract_text(
            market_cap_elements[2]).replace(',', '').replace("%", ""))
        circulating_supply = self.clean_number(self.extract_text(
            market_cap_elements[3]).replace(',', '').replace(' DUKO', ''))
        total_supply = self.clean_number(self.extract_text(market_cap_elements[4]).replace(
            ',', '').replace(' DUKO', ''))
        diluted_market_cap = self.clean_number(self.extract_text(
            market_cap_elements[6]).replace('$', '').replace(' DUKO', ''))

        contracts = []
        contract_elements = soup.find_all(
            'div', class_='sc-d1ede7e3-0 sc-7f0f401-0 sc-96368265-0 bwRagp gQoblf eBvtSa flexStart')

        for contract_element in contract_elements:
            name = self.extract_text(contract_element.find(
                'span', class_='sc-71024e3e-0 dEZnuB')).replace(":", "").strip()
            address_link = contract_element.find('a')
            address = self.extract_href(address_link).split(
                '/')[-1] if address_link else ''
            contracts.append({"name": name, "address": address})

        website_div = soup.find(
            'div', class_='sc-d1ede7e3-0 sc-7f0f401-0 gRSwoF gQoblf')
        website_link = self.extract_href(
            website_div.find('a')) if website_div else ''

        social_divs = soup.find_all(
            'div', class_='sc-d1ede7e3-0 sc-7f0f401-2 bwRagp kXjUeJ')
        social_links = []
        for social_div in social_divs:
            for link_div in social_div.find_all('div', class_='sc-d1ede7e3-0 sc-7f0f401-0 gRSwoF gQoblf'):
                social_name = self.extract_text(link_div.find('a')).split()[-1]
                social_url = self.extract_href(link_div.find('a'))
                social_links.append(
                    {"name": social_name.lower(), "url": social_url})
        if len(social_links) > 0:
            social_links.pop(0)

        data = {
            "coin": coin_name,
            "output": {
                "price": float(price) if price else None,
                "price_change": float(price_change) if price_change else None,
                "market_cap": float(market_cap) if market_cap else None,
                "market_cap_rank": int(market_cap_rank) if market_cap_rank else None,
                "volume": float(volume) if volume else None,
                "volume_rank": int(volume_rank) if volume_rank else None,
                "volume_change": float(volume_change) if volume_change else None,
                "circulating_supply": float(circulating_supply) if circulating_supply else None,
                "total_supply": float(total_supply) if total_supply else None,
                "diluted_market_cap": float(diluted_market_cap) if diluted_market_cap else None,
                "contracts": contracts,
                "official_links": [{"name": "website", "link": website_link if website_link else None}],
                "socials": social_links
            }
        }
        redis.rpush(job_id, json.dumps(data))
        redis.expire(job_id, 3600)
        return data

    def start_scraping(self, coins, job_id):

        tasks = []
        for coin in coins:
            tasks.append({"coin": coin, "job_id": job_id})
            self.scrape_data(coin, job_id)
        for task in tasks:
            redis.rpush(job_id + "_tasks", json.dumps(task))
        redis.expire(job_id + "_tasks", 3600)
        redis.set(f"{job_id}_status", "completed")
        redis.expire(f"{job_id}_status", 3600)
        return job_id

    async def start_scraping_async(self, coins, job_id):
        self.start_scraping(coins, job_id)

    def scraping_status(self, job_id):
        status = redis.get(f"{job_id}_status")
        if status:
            tasks = [json.loads(task) for task in redis.lrange(
                job_id + "_tasks", 0, -1)]
            data = [json.loads(item) for item in redis.lrange(job_id, 0, -1)]
            output_dict = {item["coin"]: item["output"] for item in data}
            tasks_with_output = [{"coin": task["coin"], "output": output_dict.get(
                task["coin"], {})} for task in tasks]
            return {"job_id": job_id, "tasks": tasks_with_output}
        else:
            return None


coin_market_cap = CoinMarketCap()


@ app.get("/")
async def root():
    return {"message": "Hello World"}


@ app.post("/api/taskmanager/start_scraping")
async def start_scraping(coins_request: CoinRequest, background_tasks: BackgroundTasks):
    coins = coins_request.coins
    job_id = str(uuid4())
    background_tasks.add_task(
        coin_market_cap.start_scraping_async, coins, job_id)
    return {"job_id": job_id}


@ app.get("/api/taskmanager/scraping_status/{job_id}")
async def scraping_status(job_id: str):
    status = coin_market_cap.scraping_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return status
