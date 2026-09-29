import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
PUBLIC_DASHBOARD_URL = os.getenv("PUBLIC_DASHBOARD_URL", "https://app.supabase.com/project/bamsulmqreckuoqtugkj")

def send_slack_alert(anomaly_data: dict, ai_explanation: dict, webhook_url: str = None) -> bool:
    """
    Formulates and sends a concise, business-friendly Slack alert when a 
    HIGH or CRITICAL anomaly is detected.
    """
    target_webhook = webhook_url or SLACK_WEBHOOK_URL

    metric_name = anomaly_data.get("metric_name", "KPI Anomaly")
    curr_val = anomaly_data.get("current_value")
    exp_val = anomaly_data.get("expected_value")
    change_pct = anomaly_data.get("change_percent")
    severity = anomaly_data.get("severity", "WARNING")

    summary_text = ai_explanation.get("summary", "Cause cannot be determined from the available data.")
    
    signals_list = ai_explanation.get("possible_contributing_signals", [])
    signals_text = "\n".join([f"• {s}" for s in signals_list]) if signals_list else "• Cause cannot be determined from the available data."

    actions_list = ai_explanation.get("recommended_actions", ai_explanation.get("recommended_investigation", []))
    actions_text = "\n".join([f"• {a}" for a in actions_list]) if actions_list else "• Check raw database logs manually."

    # Construct formatted Slack block message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 KPI Anomaly Detected: {metric_name}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Metric:*\n{metric_name}"},
                {"type": "mrkdwn", "text": f"*Severity:*\n`{severity}`"},
                {"type": "mrkdwn", "text": f"*Current Value:*\n`{curr_val}`"},
                {"type": "mrkdwn", "text": f"*Expected Value:*\n`{exp_val}`"},
                {"type": "mrkdwn", "text": f"*Change:*\n`{change_pct}%`"}
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*AI Summary:*\n{summary_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Possible Contributing Signals:*\n{signals_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommended Investigation:*\n{actions_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Dashboard:*\n<{PUBLIC_DASHBOARD_URL}|View Observability Dashboard>"
            }
        }
    ]

    payload = {"blocks": blocks}

    # If no valid Slack URL is provided, display payload locally
    if not target_webhook or "hooks.slack.com" not in target_webhook:
        print("\nℹ️ [DRY RUN] SLACK_WEBHOOK_URL not configured. Formatted alert payload:")
        print(json.dumps(payload, indent=2))
        return True

    try:
        response = requests.post(target_webhook, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        if response.status_code == 200:
            print("✅ Slack alert successfully sent!")
            return True
        else:
            print(f"❌ Failed to send Slack alert. Status Code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending Slack notification: {str(e)}")
        return False