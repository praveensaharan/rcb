# FastAPI Coin Scraper

This FastAPI application allows you to start scraping cryptocurrency information and check the status of the scraping jobs. The results are processed in the background.

## Features

- Start scraping tasks for given cryptocurrencies.
- Check the status of scraping tasks.
- Background task processing.
- CORS support.

## Prerequisites

- Python 3.7+
- Redis server (if using Redis for task management)
- Environment file (.env) with necessary configurations

## Setup Instructions

### Step 1: Clone the Repository

```shell
git clone https://github.com/praveensaharan/fastapi-webscrap.git
cd fastapi-webscrap
```

### Step 2: Create and Activate a Virtual Environment

```shell
python -m venv env
# On Windows
.\env\Scripts\activate
# On macOS/Linux
source env/bin/activate
```

### Step 3: Install Dependencies

```shell
pip install -r requirements.txt
```

### Step 4: Create a .env File

Create a .env file in the root directory of the project and add your environment variables:

```
REDIS_URL=redis://default:your_redis_url
```

### Step 5: Run the FastAPI Application

```shell
uvicorn main:app --reload
```

The application will be available at http://127.0.0.1:8000.

## API Endpoints

- `GET /`: Returns a greeting message.

  Response:

  ```json
  {
    "message": "Hello World"
  }
  ```

- `POST /api/taskmanager/start_scraping`: Start a new scraping task for the specified cryptocurrencies.

  Request Body (raw and json):

  ```json
  {
    "coins": ["DUKO", "Bitcoin", "Ethereum", "Litecoin"]
  }
  ```

  Response:

  ```json
  {
    "job_id": "unique-job-id"
  }
  ```

- `GET /api/taskmanager/scraping_status/{job_id}`: Check the status of a scraping job.

  Response:

  ```json
  {
    "job_id": "e0d93c18-1d8f-4943-97eb-0503d884e030",
    "tasks": [
      {
        "coin": "DUKO",
        "output": {
          "price": 0.004688,
          "price_change": -18.06,
          "market_cap": 45305655,
          "market_cap_rank": 669,
          "volume": 12782254,
          "volume_rank": 386,
          "volume_change": 28.21,
          "circulating_supply": 9663955990,
          "total_supply": 9999609598,
          "diluted_market_cap": 46879235,
          "contracts": [
            {
              "name": "Solana",
              "address": "HLptm5e6rTgh4EKgDpYFrnRHbjpkMyVdEeREEa2G7rf9"
            }
          ],
          "official_links": [
            {
              "name": "website",
              "link": "https://dukocoin.com/"
            }
          ],
          "socials": [
            {
              "name": "𝕏twitter",
              "url": "https://twitter.com/dukocoin"
            },
            {
              "name": "telegram",
              "url": "https://t.me/+jlScZmFrQ8g2MDg8"
            }
          ]
        }
      }
    ]
  }
  ```

Notes:

- Make sure your Redis server is running and accessible using the URL provided in the .env file.
- Ensure you have a coin_market_cap module or script with the start_scraping_async and scraping_status functions defined.

License:
This project is licensed under the MIT License.
