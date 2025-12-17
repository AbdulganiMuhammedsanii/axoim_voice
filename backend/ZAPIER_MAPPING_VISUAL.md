# Zapier Field Mapping - Visual Step-by-Step

## Understanding: It's a DROPDOWN, Not Manual Typing

When you click on a field in Zapier, you'll see a **dropdown menu** with options. You **select** from the dropdown - you don't manually type field names.

## Step-by-Step Visual Guide

### Step 1: Test Your Webhook First (IMPORTANT!)

1. In your Zap, find the **Webhook trigger** step
2. Click **"Test trigger"** button
3. Zapier will show you a sample of the data it received
4. You'll see something like:
   ```
   appointment_id: "abc123"
   title: "Consultation"
   start_time: "2024-12-20T14:00:00Z"
   attendee_email: "john@example.com"
   ... etc
   ```
5. **This is crucial** - Zapier needs this test data to show you the dropdown options

### Step 2: Add Google Calendar Action

1. Click **"+ Add step"** or the **"+"** button
2. Search for **"Google Calendar"**
3. Select **"Create Detailed Event"**
4. Click **"Continue"**
5. Connect your Google account if needed

### Step 3: Map Fields - The DROPDOWN Way

#### For "Event Title" field:

1. **Click on the "Event Title" field** (it's a text box)
2. You'll see a button that looks like: **[📊]** or says **"Insert data"** or **"Map from webhook"**
3. **Click that button**
4. A **dropdown menu appears** showing:
   ```
   ┌─────────────────────────────┐
   │ Use custom value             │
   │ ─────────────────────────── │
   │ Map from webhook            │
   │   ├─ appointment_id         │
   │   ├─ title          ← SELECT THIS
   │   ├─ description            │
   │   ├─ start_time             │
   │   ├─ end_time               │
   │   ├─ timezone               │
   │   ├─ attendee_email         │
   │   ├─ attendee_name          │
   │   └─ created_at            │
   └─────────────────────────────┘
   ```
5. **Click on `title`** from the dropdown
6. The field will now show: `{{title}}` or display the mapped field

#### For "Start Time" field:

1. Click on **"Start Time"** field
2. Click the **data/insert button** (📊)
3. From the dropdown, select **`start_time`**
4. Done!

#### For "End Time" field:

1. Click on **"End Time"** field
2. Click the **data/insert button** (📊)
3. From the dropdown, select **`end_time`**
4. Done!

#### For "Attendees" field:

1. Click on **"Attendees"** field
2. Click the **data/insert button** (📊)
3. From the dropdown, select **`attendee_email`**
4. Done!

#### For "Description" field:

1. Click on **"Description"** field
2. Click the **data/insert button** (📊)
3. From the dropdown, select **`description`**
4. Done!

### Step 4: Email Action - Similar Process

#### For "To" field:

1. Click on **"To"** field
2. Click the **data/insert button** (📊)
3. From the dropdown, select **`attendee_email`**
4. Done!

#### For "Subject" field:

1. Click on **"Subject"** field
2. Click the **data/insert button** (📊)
3. **BUT** - for subject, you want to use **"Use custom value"** instead
4. Type: `Appointment Confirmation: {{title}}`
5. The `{{title}}` will automatically pull from webhook

#### For "Body" field:

1. Click on **"Body"** or **"Message"** field
2. Click the **data/insert button** (📊)
3. Select **"Use custom value"**
4. Paste this HTML:
   ```html
   <h2>Appointment Confirmation</h2>
   <p>Hello {{attendee_name}},</p>
   <p>Your appointment: {{title}}</p>
   <p>Time: {{start_time}} to {{end_time}}</p>
   ```

## What You'll Actually See in Zapier

### Before Mapping:
```
Event Title: [________________] [📊]
```

### After Clicking the 📊 Button:
```
Event Title: [________________] [📊]
             ┌─────────────────┐
             │ Use custom value│
             │ ─────────────── │
             │ Map from webhook│
             │   • title       │ ← Click this
             │   • description │
             │   • start_time  │
             └─────────────────┘
```

### After Selecting:
```
Event Title: [{{title}}] [📊]
```

## Key Points

1. **You DON'T type `title`** - you select it from a dropdown
2. **The dropdown only appears AFTER you test the webhook trigger**
3. **Click the 📊 or "Insert data" button** to see the dropdown
4. **Select the field name** from the dropdown list
5. **Zapier automatically adds `{{field_name}}`** syntax

## If You Don't See the Dropdown

If you don't see field options in the dropdown:

1. **Go back and test the webhook trigger first**
   - This is the #1 reason - Zapier needs sample data
2. **Make sure you clicked the 📊 button** (not just the text field)
3. **Look for "Map from webhook"** option in the dropdown
4. **Refresh the page** and try again

## Quick Reference: What to Click

| Field | Action |
|-------|--------|
| Event Title | Click 📊 → Select `title` from dropdown |
| Start Time | Click 📊 → Select `start_time` from dropdown |
| End Time | Click 📊 → Select `end_time` from dropdown |
| Attendees | Click 📊 → Select `attendee_email` from dropdown |
| Description | Click 📊 → Select `description` from dropdown |
| Email To | Click 📊 → Select `attendee_email` from dropdown |
| Email Subject | Click 📊 → Select "Use custom value" → Type: `Appointment Confirmation: {{title}}` |
| Email Body | Click 📊 → Select "Use custom value" → Paste HTML template |

## Testing

After mapping all fields:

1. Click **"Test action"** on Google Calendar step
2. Check your Google Calendar - event should appear
3. Click **"Test action"** on Email step  
4. Check email inbox - confirmation should arrive
5. If both work, **turn ON your Zap** (toggle at top)

## Still Confused?

The key is: **It's a visual dropdown interface, not manual typing**. Zapier shows you all available fields after you test the webhook, and you just click to select them.

