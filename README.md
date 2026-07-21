# ✈️ Weather Delay Risk Pipeline

An end-to-end data engineering pipeline that ingests real-time weather and flight data to compute a daily **delay risk score** per airport.

---

## 🏗️ Architecture

```
Open-Meteo API  ──┐
                   ├──► S3 Raw (JSON) ──► S3 Processed (Parquet) ──► S3 Serving ──► FastAPI
AviationStack  ──┘
BTS Historical ──┘
         ↑
  Airflow DAG runs this every day at 6am UTC
```

---

## 🗂️ Project Structure

```
weather-delay-risk/
├── ingestion/
│   ├── weather_api.py       # Fetches weather from Open-Meteo
│   ├── flight_api.py        # Fetches flights from AviationStack
│   └── upload_to_s3.py      # Uploads raw data to S3
├── transformation/
│   ├── clean_weather.py     # Cleans weather data
│   ├── clean_flights.py     # Cleans flight data
│   └── risk_score.py        # Computes delay risk score
├── dags/
│   └── pipeline_dag.py      # Airflow DAG (runs daily at 6am)
├── serving/
│   └── main.py              # FastAPI endpoint
├── notebooks/
│   ├── cleaning.ipynb       # Data exploration & cleaning
│   └── risk_score.ipynb     # Risk score exploration
├── Dockerfile               # FastAPI container
├── docker-compose.yml       # Runs Airflow + FastAPI + Postgres
└── requirements.txt
```

---

## 🚀 How to Run

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/weather-delay-risk.git
cd weather-delay-risk
```

### 2. Set up environment variables
Create a `.env` file:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_BUCKET_NAME=your_bucket
AWS_REGION=eu-west-1
AVIATIONSTACK_API_KEY=your_key
```

### 3. Start everything
```bash
docker compose up airflow-init
docker compose up -d
```

### 4. Access the services
| Service | URL |
|---|---|
| Airflow UI | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## 📡 API Endpoints

### Get risk score for one airport
```
GET /risk?airport=JFK
```
Response:
```json
{
  "airport": "JFK",
  "date": "2026-07-20",
  "risk_score": 0.42,
  "risk_label": "Moderate",
  "avg_windspeed": 23.4,
  "total_precip": 2.1,
  "avg_visibility": 8200.0,
  "delay_rate": 0.223,
  "avg_dep_delay": 18.5
}
```

### Get risk scores for all airports
```
GET /risk/all
```

---

## 🧠 Risk Score Logic

The risk score is a weighted combination of 4 factors:

| Factor | Weight | Logic |
|---|---|---|
| Max wind speed | 25% | Higher wind = harder takeoff |
| Precipitation | 30% | Rain/snow = most impactful |
| Visibility | 25% | Fog = guaranteed delays |
| Historical delay rate | 20% | Airport's track record |

```
risk_score = 0.25×wind + 0.30×precip + 0.25×visibility + 0.20×historical
```

Risk labels:
- 🟢 Low → score < 0.2
- 🟡 Moderate → score < 0.4
- 🟠 High → score < 0.6
- 🔴 Severe → score ≥ 0.6

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Ingestion | Python, Requests, AviationStack API, Open-Meteo API |
| Storage | AWS S3, Parquet, Medallion Architecture |
| Transformation | Pandas, PyArrow |
| Orchestration | Apache Airflow, Docker Compose |
| Serving | FastAPI, Uvicorn |
| Infrastructure | Docker, PostgreSQL |

---

## ✈️ Tracked Airports

JFK · LAX · ORD · ATL · DFW