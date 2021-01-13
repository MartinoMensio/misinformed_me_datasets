from fastapi import Depends, FastAPI
import schedule
import threading
import time


from .routers import data

app = FastAPI()


app.include_router(data.router, prefix='/data', tags=['data'])
# app.include_router(items.router)

def update_daily():
    print('hello from job')
    data.update_data()
    print('job successful')

def update_weekly():
    data.scrape_all()

def scheduler():
    schedule.every().monday.at('22:00').do(update_daily)
    schedule.every().tuesday.at('22:00').do(update_daily)
    schedule.every().wednesday.at('10:21').do(update_daily)
    schedule.every().thursday.at('22:00').do(update_daily)
    schedule.every().friday.at('22:00').do(update_daily)
    schedule.every().saturday.at('22:00').do(update_daily)
    schedule.every().sunday.at('22:00').do(update_daily)
    # schedule.every().sunday.at('12:00').do(update_weekly)
    print('\n'.join(str(el) for el in schedule.jobs))
    print('scheduler ready')
    while True:
        schedule.run_pending()
        time.sleep(1)


@app.on_event("startup")
async def startup_event():
    job_thread = threading.Thread(target=scheduler)
    job_thread.daemon = True
    job_thread.start()



@app.get("/")
async def root():
    return {"message": "ClaimReview scraper API. See the OpenAPI description at /docs"}