import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from notifications.slack import send_slack_alert

def main():
    print("--- 🛠️ TESTING SLACK ALERTING MODULE ---")

    mock_anomaly = {
        "metric_name": "refund_rate",
        "current_value": 48.5,
        "expected_value": 5.2,
        "change_percent": 832.69,
        "severity": "CRITICAL"
    }

    mock_ai_explanation = {
        "summary": "Cause cannot be determined from the available data.",
        "possible_contributing_signals": [
            "completed_orders dropped by 45.0%",
            "daily_revenue dropped by 50.2%"
        ],
        "recommended_investigation": [
            "Investigate order processing and customer support logs for bulk refunds.",
            "Review recent product changes or payment gateway errors."
        ]
    }

    print("\nSending test alert...")
    success = send_slack_alert(mock_anomaly, mock_ai_explanation)
    if success:
        print("✅ Test execution completed successfully!")

if __name__ == "__main__":
    main()