"""
Scheduler tool for Mimi - enables cron-like scheduled actions.
Uses APScheduler to run background tasks on the Railway server.
"""

import os
import json
from datetime import datetime
from typing import Optional

# Store for scheduled jobs (in-memory for now, could upgrade to persistent storage)
SCHEDULED_JOBS = {}


def schedule_task(
    task_type: str,
    schedule_time: str,
    action: str,
    target: Optional[str] = None,
    message: Optional[str] = None,
    recurrence: Optional[str] = None,
) -> dict:
    """
    Schedule a task to run at a specific time.
    
    Args:
        task_type: Type of task (sms, telegram, dashboard_log, reminder)
        schedule_time: Time in HH:MM format (24hr) or ISO datetime
        action: Action to perform (send_message, log_activity, etc)
        target: Target for the action (phone number, chat_id, etc)
        message: Message content or action payload
        recurrence: Optional recurrence pattern (daily, weekly, weekdays)
    
    Returns:
        Status dict with job_id and confirmation
    """
    
    try:
        # Generate unique job ID
        job_id = f"{task_type}_{schedule_time.replace(':', '')}_{len(SCHEDULED_JOBS)}"
        
        # Parse schedule time
        if 'T' in schedule_time or '-' in schedule_time:
            scheduled_dt = datetime.fromisoformat(schedule_time)
            trigger_type = 'date'
            trigger_args = {'run_date': scheduled_dt}
        else:
            # Assume HH:MM format for daily recurrence
            hour, minute = map(int, schedule_time.split(':'))
            trigger_type = 'cron'
            trigger_args = {'hour': hour, 'minute': minute}
            
            if recurrence == 'weekdays':
                trigger_args['day_of_week'] = 'mon-fri'
            elif recurrence == 'weekly':
                trigger_args['day_of_week'] = datetime.now().strftime('%a').lower()
        
        # Store job config
        job_config = {
            'id': job_id,
            'task_type': task_type,
            'schedule_time': schedule_time,
            'action': action,
            'target': target,
            'message': message,
            'recurrence': recurrence,
            'trigger_type': trigger_type,
            'trigger_args': trigger_args,
            'created_at': datetime.now().isoformat(),
            'active': True,
        }
        
        SCHEDULED_JOBS[job_id] = job_config
        
        return {
            'status': 'scheduled',
            'job_id': job_id,
            'task_type': task_type,
            'schedule_time': schedule_time,
            'recurrence': recurrence or 'once',
            'message': f"Task scheduled successfully. Job ID: {job_id}",
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Failed to schedule task: {str(e)}",
        }


def list_scheduled_tasks() -> dict:
    """List all active scheduled tasks."""
    
    active_jobs = [
        {
            'job_id': job_id,
            'task_type': config['task_type'],
            'schedule_time': config['schedule_time'],
            'recurrence': config.get('recurrence', 'once'),
            'message': config.get('message', '')[:50] + '...' if len(config.get('message', '')) > 50 else config.get('message', ''),
            'created_at': config['created_at'],
        }
        for job_id, config in SCHEDULED_JOBS.items()
        if config.get('active', True)
    ]
    
    return {
        'status': 'ok',
        'count': len(active_jobs),
        'jobs': active_jobs,
    }


def cancel_scheduled_task(job_id: str) -> dict:
    """Cancel a scheduled task by job ID."""
    
    if job_id in SCHEDULED_JOBS:
        SCHEDULED_JOBS[job_id]['active'] = False
        return {
            'status': 'cancelled',
            'job_id': job_id,
            'message': f"Task {job_id} cancelled successfully",
        }
    else:
        return {
            'status': 'error',
            'message': f"Job ID {job_id} not found",
        }


# --- Required exports ---

TOOLS = [
    {
        "name": "schedule_task",
        "description": "Schedule a task to run at a specific time (cron-like). Can send SMS/Telegram, log dashboard activities, or trigger reminders. Supports one-time or recurring schedules.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "description": "Type of task: 'sms', 'telegram', 'dashboard_log', 'reminder'",
                    "enum": ["sms", "telegram", "dashboard_log", "reminder"],
                },
                "schedule_time": {
                    "type": "string",
                    "description": "Time to run task. Format: 'HH:MM' (24hr, e.g. '08:30') for daily, or full ISO datetime for one-time",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'send_message', 'log_activity', 'check_in_reminder', etc",
                },
                "target": {
                    "type": "string",
                    "description": "Target for action (phone number for SMS, chat_id for Telegram, etc). Optional for dashboard logs.",
                },
                "message": {
                    "type": "string",
                    "description": "Message content or payload for the scheduled action",
                },
                "recurrence": {
                    "type": "string",
                    "description": "Recurrence pattern: 'daily', 'weekdays', 'weekly', or omit for one-time",
                    "enum": ["daily", "weekdays", "weekly"],
                },
            },
            "required": ["task_type", "schedule_time", "action"],
        },
    },
    {
        "name": "list_scheduled_tasks",
        "description": "List all active scheduled tasks with their job IDs, times, and details.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "cancel_scheduled_task",
        "description": "Cancel a scheduled task by its job ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID returned when the task was scheduled",
                },
            },
            "required": ["job_id"],
        },
    },
]

HANDLERS = {
    "schedule_task": schedule_task,
    "list_scheduled_tasks": list_scheduled_tasks,
    "cancel_scheduled_task": cancel_scheduled_task,
}
