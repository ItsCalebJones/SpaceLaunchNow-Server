from apscheduler.schedulers.background import BackgroundScheduler

from bot.app.DailyDigest import run_daily, run_weekly
from bot.utils.util import log

TAG = "Notification Server"


def start_scheduler():
    log(TAG, "Initializing server...")
    scheduler = BackgroundScheduler()
    scheduler.start()
    log(TAG, "Created background scheduler.")
    scheduler.add_job(run_daily, trigger='cron', day_of_week='mon-sun', hour=10, minute=30)
    scheduler.add_job(run_weekly, trigger='cron', day_of_week='fri', hour=12, minute=30)
    log(TAG, "Added cronjobs to background scheduler.")
    # Notifications.NotificationServer(scheduler).run()
    run_daily()
    log(TAG, "Notification Server started.")

