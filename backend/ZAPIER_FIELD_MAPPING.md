# Zapier Field Mapping Guide

This guide shows you exactly how to map fields from the webhook to Google Calendar and Email in Zapier's interface.

## Understanding "Map from Webhook"

When Zapier says "Map from webhook", it means you're selecting which data from the webhook payload to use in your action (Google Calendar or Email).

## Step-by-Step: Google Calendar Field Mapping

### 1. After Adding Google Calendar Action

When you add the "Create Detailed Event" action, you'll see a form with fields like:
- Calendar
- Event Title
- Start Time
- End Time
- Description
- Attendees
- etc.

### 2. Click on Each Field to Map

For each field, you'll see a dropdown or button that says something like:
- "Insert data" or
- "Map from webhook" or
- A dropdown with "Use custom value" / "Map from webhook"

**Click on the field** → **Select "Map from webhook"** or **Click the data icon** → **Select the field name**

### 3. Exact Field Mappings

Here's what to map for each Google Calendar field:

| Google Calendar Field | Map From Webhook Field | Example Value |
|----------------------|------------------------|---------------|
| **Calendar** | (Select your calendar manually) | "primary" or your calendar name |
| **Event Title** | `title` | "Consultation with John Doe" |
| **Start Time** | `start_time` | "2024-12-20T14:00:00Z" |
| **End Time** | `end_time` | "2024-12-20T15:00:00Z" |
| **Description** | `description` | "Initial consultation" |
| **Attendees** | `attendee_email` | "john@example.com" |
| **Location** | (Leave blank or use custom value) | Optional |

### 4. Visual Example

When you click on "Event Title" field, you'll see:
```
Event Title: [Dropdown ▼]
  └─ Use custom value
  └─ Map from webhook
      ├─ appointment_id
      ├─ title          ← SELECT THIS
      ├─ description
      ├─ start_time
      ├─ end_time
      ├─ timezone
      ├─ attendee_email
      ├─ attendee_name
      └─ created_at
```

**Select `title` from the list.**

## Step-by-Step: Email Field Mapping

### 1. After Adding Email Action

When you add the "Send Email" action (Gmail or Email by Zapier), you'll see fields like:
- To
- Subject
- Body/Message

### 2. Map Email Fields

| Email Field | Map From Webhook Field | Notes |
|-------------|------------------------|-------|
| **To** | `attendee_email` | The recipient's email |
| **Subject** | Use custom value with template | "Appointment Confirmation: {{title}}" |
| **Body** | Use custom value with template | See template below |

### 3. Email Subject Template

Instead of mapping, use a **custom value** with Zapier's template syntax:

```
Appointment Confirmation: {{title}}
```

This will insert the `title` field from the webhook.

### 4. Email Body Template (HTML)

Use a **custom value** with this HTML template:

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

### 5. How to Use Templates in Zapier

1. Click on the "Subject" or "Body" field
2. Select **"Use custom value"** (not "Map from webhook")
3. Paste the template above
4. Zapier will automatically replace `{{field_name}}` with the actual values

## Complete Mapping Reference

### Webhook Payload Structure

The backend sends this JSON to your webhook:

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

### All Available Fields

You can map any of these fields:
- `appointment_id` - Internal appointment ID
- `title` - Appointment title
- `description` - Appointment description
- `start_time` - Start time (ISO 8601 format)
- `end_time` - End time (ISO 8601 format)
- `timezone` - Timezone (e.g., "UTC", "America/New_York")
- `attendee_email` - Attendee's email address
- `attendee_name` - Attendee's name
- `created_at` - When appointment was created

## Tips for Mapping

### 1. Finding the Field List

When you click "Map from webhook", Zapier shows you all available fields from the test webhook. If you don't see the fields:
- Make sure you've tested the webhook trigger first
- The fields appear based on the test data Zapier received

### 2. Using Custom Values vs Mapping

- **Map from webhook**: Use when you want the exact value from webhook
- **Use custom value**: Use when you want to combine fields or add static text

Example custom value for subject:
```
Appointment: {{title}} on {{start_time}}
```

### 3. Conditional Fields

In email body, you can use `{% if description %}` to only show description if it exists.

### 4. Date Formatting

If you need to format dates, you can:
- Use Zapier's "Formatter" step between webhook and actions
- Or format in the email template using Zapier's date functions

## Testing Your Mappings

1. **Test Google Calendar Action**:
   - Click "Test action" in Zapier
   - Check your Google Calendar
   - Verify the event was created with correct data

2. **Test Email Action**:
   - Click "Test action" in Zapier
   - Check the email inbox (use `attendee_email` from test)
   - Verify email content is correct

3. **Test Full Zap**:
   - Send a real webhook from your backend
   - Check both calendar and email
   - Verify all fields are mapped correctly

## Common Issues

### Field Not Showing Up

If a field doesn't appear in the mapping dropdown:
1. Make sure you tested the webhook trigger first
2. The field name must match exactly (case-sensitive)
3. Try refreshing the Zap or re-testing the trigger

### Date/Time Not Working

If dates aren't showing correctly:
- Google Calendar expects ISO 8601 format (which we send)
- If issues persist, add a Formatter step to convert the date

### Email Template Not Rendering

If `{{field_name}}` shows literally instead of the value:
- Make sure you selected "Use custom value" not "Map from webhook"
- Check that field names match exactly (case-sensitive)
- Test the template in Zapier's preview

## Quick Checklist

- [ ] Webhook trigger tested and receiving data
- [ ] Google Calendar action added and connected
- [ ] All Google Calendar fields mapped correctly
- [ ] Google Calendar action tested successfully
- [ ] Email action added and connected
- [ ] Email "To" field mapped to `attendee_email`
- [ ] Email subject uses template with `{{title}}`
- [ ] Email body uses HTML template with all fields
- [ ] Email action tested successfully
- [ ] Full Zap tested end-to-end
- [ ] Zap is turned ON (toggle at top)

## Need Help?

If you're stuck:
1. Check Zapier's help docs: https://help.zapier.com
2. Look at the webhook test data to see exact field names
3. Use Zapier's "Test" feature to see what data is available
4. Check backend logs to see what's being sent to webhook

