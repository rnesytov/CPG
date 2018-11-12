from gateway.jobs.sync_tx_outputs import SyncTxOutputs
from gateway.jobs.send_notifications import SendNotifications
from gateway.jobs.deactivate_unused_accounts import DeactivateUnusedAccounts

JOBS_LIST = [SyncTxOutputs, SendNotifications, DeactivateUnusedAccounts]


def init_jobs(scheduler, app):
    for job_class in JOBS_LIST:
        job = job_class(app)

        if job.enabled:
            scheduler.add_job(job.__call__,
                              trigger='interval',
                              seconds=job.job_settings.interval,
                              name=job.job_name)
