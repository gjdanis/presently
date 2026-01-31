"""
Email sending helper using AWS SES
"""

import os

import boto3
from botocore.exceptions import ClientError

# Initialize SES client
ses_client = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def send_email(to_email, subject, html_body, text_body):
    """
    Send email via AWS SES

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body

    Returns:
        bool: True if sent successfully, False otherwise
    """
    sender = os.environ.get("SENDER_EMAIL", "noreply@presently.com")

    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                },
            },
        )

        print(f"✅ Email sent successfully to {to_email}. MessageId: {response['MessageId']}")
        return True

    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        print(f"❌ Error sending email to {to_email}: {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending email: {str(e)}")
        return False
