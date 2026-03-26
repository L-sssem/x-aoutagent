"""Application entry point for starting scheduled jobs."""

from services.scheduler import SchedulerService


def main() -> None:
    """Start the scheduler service."""
    scheduler = SchedulerService()
    # ここに日次・週次スケジュールを登録する
    scheduler.start()


if __name__ == "__main__":
    main()
