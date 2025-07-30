# app/routes/scheduled.py
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI
from pytz import timezone
from sqlalchemy.orm import Session
from app.database import get_db
import asyncio

from app.services.daily_predictions import generate_daily_predictions, get_last_run_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedulers", tags=['prediction schedulers'])

# Global task reference to allow cancellation
daily_prediction_task = None

@asynccontextmanager
async def lifespan(app:FastAPI):
    # On startup
    db = next(get_db())
    try:
        # Start the daily prediction task
        asyncio.create_task(run_daily_predictions_continuously(db))
        yield
    finally:
        # On shutdown
        db.close()
        if daily_prediction_task:
            daily_prediction_task.cancel()

async def run_daily_predictions_continuously(db: Session):
    """Run predictions daily at 2 AM"""
    while True:
        try:
            now = datetime.now(timezone("Africa/Blantyre"))
            target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
            
            # If it's already past 2 AM today, schedule for tomorrow
            if now > target_time:
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"Next prediction run at {target_time} (in {wait_seconds/3600:.1f} hours)")
            
            await asyncio.sleep(wait_seconds)
            
            logger.info("Starting scheduled daily predictions")
            await generate_daily_predictions(db)
            
        except asyncio.CancelledError:
            logger.info("Daily prediction task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in daily prediction task: {str(e)}")
            await asyncio.sleep(3600)  # Wait an hour before retrying


@router.post("/trigger-daily-predictions")
async def manual_trigger(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger the daily prediction job"""
    background_tasks.add_task(generate_daily_predictions, db)
    return {"message": "Daily prediction job started in background"}

@router.get("/prediction-task-status")
async def get_task_status(db:Session = Depends(get_db)):
    """Check status of the daily prediction task"""
    return {
        "running": daily_prediction_task is not None and not daily_prediction_task.done(),
        "last_run": get_last_run_time(db=db)  # You'd need to implement this
    }