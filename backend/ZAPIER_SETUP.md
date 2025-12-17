# Zapier Integration Setup Guide

This guide explains how to set up Zapier to handle appointment scheduling, Google Calendar events, and email confirmations.

## Overview

Instead of managing Google Calendar OAuth and email service APIs directly, we use Zapier webhooks to:
1. **Create Google Calendar events** - Zapier handles Google Calendar authentication
2. **Send confirmation emails** - Zapier handles email service authentication

## Prerequisites

1. A Zapier account (free tier works)
2. Google Calendar access
3. Email service (Gmail, Outlook, or any email service Zapier supports)

## Step 1: Create Zapier Webhook

1. **Log into Zapier**: Go to https://zapier.com and sign in

2. **Create a New Zap**: Click "Create Zap"

3. **Set Up Trigger**:
   - **Trigger App**: Search for "Webhooks by Zapier"
   - **Trigger Event**: Select "Catch Hook"
   - Click "Continue"
   - Copy the **Webhook URL** (looks like: `https://hooks.zapier.com/hooks/catch/xxxxx/xxxxx/`)
   - Save this URL - you'll need it for the `.env` file

4. **Test the Webhook**:
   - Click "Test trigger"
   - Zapier will show you a sample payload
   - This confirms your webhook is ready

## Step 2: Add Google Calendar Action

1. **Add Action**:
   - Click "+" to add an action step
   - **Action App**: Search for "Google Calendar"
   - **Action Event**: Select "Create Detailed Event"
   - Click "Continue"

2. **Connect Google Calendar**:
   - Click "Sign in to Google Calendar"
   - Authorize Zapier to access your Google Calendar
   - Select the calendar you want to use (usually "primary")

3. **Map Fields**:
   - **Calendar**: Select your calendar
   - **Event Title**: Map from webhook `title`
   - **Start Time**: Map from webhook `start_time`
   - **End Time**: Map from webhook `end_time`
   - **Description**: Map from webhook `description`
   - **Attendees**: Map from webhook `attendee_email`
   - **Location**: (Optional) Leave blank or add a default
   - Click "Continue"

4. **Test Google Calendar Action**:
   - Click "Test action"
   - Check your Google Calendar - you should see a test event
   - If successful, continue

## Step 3: Add Email Action

1. **Add Another Action**:
   - Click "+" to add another action step
   - **Action App**: Search for your email service (e.g., "Gmail", "Outlook", "Email by Zapier")
   - **Action Event**: Select "Send Email" or "Send Outbound Email"
   - Click "Continue"

2. **Connect Email Service**:
   - Sign in to your email service
   - Authorize Zapier access

3. **Map Email Fields**:
   - **To**: Map from webhook `attendee_email`
   - **Subject**: Create a template like: `Appointment Confirmation: {{title}}`
   - **Body**: Create an HTML email template:
     ```html
     <h2>Appointment Confirmation</h2>
     <p>Hello {{attendee_name}},</p>
     <p>Your appointment has been confirmed:</p>
     <ul>
       <li><strong>Title:</strong> {{title}}</li>
       <li><strong>Date & Time:</strong> {{start_time}} to {{end_time}}</li>
       <li><strong>Timezone:</strong> {{timezone}}</li>
     </ul>
     {% if description %}
     <p><strong>Description:</strong> {{description}}</p>
     {% endif %}
     <p>You should receive a calendar invitation shortly.</p>
     <p>Thank you!</p>
     ```
   - Click "Continue"

4. **Test Email Action**:
   - Click "Test action"
   - Check your email inbox (and the attendee email if different)
   - If successful, continue

## Step 4: Configure Backend

1. **Add to `.env` file**:
   ```bash
   # Zapier Configuration
   ZAPIER_API_KEY=MWRjNTFmZDUtYThkNS00NzlhLWJhMzEtOWJiOWI1NGNhYTc0OmQ2M2ExYWI1LWY2OGItNGEzYS05OGVmLWJlNGZiNTIyYjljYw==
   ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/xxxxx/xxxxx/
   ```
   
   Replace `xxxxx/xxxxx/` with your actual webhook URL from Step 1.

2. **Restart Backend**:
   ```bash
   # Stop the current server (Ctrl+C)
   # Restart it
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Step 5: Activate Your Zap

1. **Review Your Zap**:
   - You should see: Webhook → Google Calendar → Email
   - Review all steps

2. **Turn On Zap**:
   - Click the toggle at the top to turn the Zap ON
   - Your Zap is now active!

## Step 6: Test the Integration

1. **Start a Voice Call**:
   - Use the frontend to start a call
   - Ask the agent to schedule an appointment
   - Provide: date/time, email, name

2. **Verify**:
   - Check your Google Calendar - event should appear
   - Check the attendee's email - confirmation should arrive
   - Check backend logs for success messages

## Webhook Payload Format

The backend sends this payload to Zapier:

```json
{
  "appointment_id": "uuid-here",
  "title": "Consultation with John Doe",
  "description": "Initial consultation",
  "start_time": "2024-12-20T14:00:00Z",
  "end_time": "2024-12-20T15:00:00Z",
  "timezone": "UTC",
  "attendee_email": "john@example.com",
  "attendee_name": "John Doe",
  "created_at": "2024-12-20T12:00:00Z"
}
```

## Optional: Return Data from Zapier

If you want Zapier to return calendar event ID or link, you can add a "Code by Zapier" step:

1. **Add Code Step** (after Google Calendar):
   - Action: "Code by Zapier" → "Run Python"
   - Input Data: Map `event_id` and `html_link` from Google Calendar step
   - Code:
     ```python
     return {
       "calendar_event_id": input_data.get("event_id"),
       "calendar_link": input_data.get("html_link"),
       "email_sent": True
     }
     ```
   - This will be included in the webhook response

## Troubleshooting

### Webhook Not Receiving Data
- Check that `ZAPIER_WEBHOOK_URL` is correct in `.env`
- Verify the webhook URL is active in Zapier
- Check backend logs for error messages

### Google Calendar Event Not Created
- Verify Google Calendar is connected in Zapier
- Check that field mappings are correct
- Test the Google Calendar action manually in Zapier

### Email Not Sent
- Verify email service is connected in Zapier
- Check email template for errors
- Test the email action manually in Zapier

### Zap Not Triggering
- Make sure the Zap is turned ON (toggle at top)
- Check Zap history in Zapier dashboard
- Verify webhook is receiving data (check Zapier webhook logs)

## Benefits of Using Zapier

1. **No OAuth Setup**: Zapier handles all authentication
2. **Easy Configuration**: Visual interface, no code needed
3. **Reliable**: Zapier handles retries and error handling
4. **Flexible**: Easy to add more actions (SMS, Slack, etc.)
5. **Maintainable**: Update workflows without code changes

## Next Steps

- Add SMS notifications
- Add Slack notifications for new appointments
- Add calendar sync with other services
- Add appointment reminders

