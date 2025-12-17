# Production-Grade Appointment Scheduling Implementation

This document explains the complete, end-to-end appointment scheduling system with strict validation, email sending, and calendar integration.

## Architecture Overview

The appointment flow is enforced at multiple levels:

1. **System Prompt** - Instructs AI to follow strict flow
2. **Email Validation** - Server-side validation before proceeding
3. **Database Persistence** - All appointments saved immediately
4. **Google Calendar** - Real calendar events created
5. **Email Confirmation** - Real emails sent via Resend
6. **Comprehensive Logging** - Every step logged for debugging

## Conversation Flow (Enforced)

The AI agent MUST follow this exact flow:

```
1. User: "I want to schedule an appointment"
   ↓
2. AI: Asks for meeting type and preferred time
   ↓
3. User: Provides time
   ↓
4. AI: "Great! What email address should I send the confirmation to?"
   ↓
5. User: Provides email
   ↓
6. AI: Validates email (if invalid, re-asks)
   ↓
7. AI: Confirms all details
   ↓
8. AI: Calls create_appointment tool
   ↓
9. Backend: Validates email → Saves to DB → Creates calendar → Sends email
   ↓
10. AI: "I've created your appointment and sent a confirmation to [email]"
```

## Implementation Details

### 1. Email Validation Service (`validation_service.py`)

- **RFC 5322 compliant regex** validation
- **Length checks** (max 254 characters)
- **Format validation** (no consecutive dots, proper structure)
- **Normalization** (trim + lowercase)

**Usage:**
```python
is_valid, error_msg = validation_service.validate_email(email)
if not is_valid:
    # Re-ask user
```

### 2. Email Sending Service (`email_service.py`)

- **Resend API integration** for sending emails
- **HTML + Plain text** email templates
- **Professional styling** with company branding
- **Includes calendar link** if available
- **Error handling** with detailed logging

**Configuration:**
- Set `RESEND_API_KEY` in `.env`
- Set `RESEND_FROM_EMAIL` (use `onboarding@resend.dev` for testing)

### 3. Appointment API Endpoint (`appointments.py`)

**Flow:**
1. **Validate email** - Hard fail if invalid
2. **Save to database** - Always saved, even if calendar/email fail
3. **Create Google Calendar event** - With proper error handling
4. **Send confirmation email** - With calendar link included
5. **Log everything** - Comprehensive logging at each step

**Error Handling:**
- Email validation failures → HTTP 400 with clear message
- Calendar failures → Logged, appointment still saved
- Email failures → Logged, appointment still saved
- All errors stored in `appointment.meta_data`

### 4. System Prompt (`prompt_service.py`)

The prompt explicitly instructs:
- **ALWAYS ask for email FIRST** after time is agreed
- **DO NOT proceed** without valid email
- **Re-ask if email invalid**
- **Confirm details** before creating
- **Only claim success** after tool succeeds

### 5. State Management (`state_service.py`)

Added methods for tracking appointment state:
- `set_appointment_state()` - Store appointment info
- `get_appointment_state()` - Retrieve appointment info
- `update_appointment_field()` - Update specific fields

### 6. Real-Time Transcript Saving

- Frontend saves transcripts as they come in
- `/api/call/transcript` endpoint for real-time saving
- Transcripts persisted immediately, not just on call end

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
source voicenv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add to `backend/.env`:

```bash
# Google Calendar (already configured)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_CALENDAR_ID=primary

# Resend Email Service (NEW)
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev  # For testing, or your verified domain
```

### 3. Get Resend API Key

1. Go to [https://resend.com](https://resend.com)
2. Sign up for free account
3. Get API key from dashboard
4. Add to `.env` file

See `RESEND_SETUP.md` for detailed instructions.

## Testing the Flow

1. **Start backend server:**
   ```bash
   cd backend
   source voicenv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend:**
   ```bash
   npm run dev
   ```

3. **Test appointment flow:**
   - Start a voice call
   - Say: "I want to schedule an appointment"
   - AI will ask for time
   - AI will ask: "What email should I send the confirmation to?"
   - Provide your email
   - AI will create appointment

4. **Check results:**
   - **Backend logs** - Should show:
     - `📧 Validating email: [email]`
     - `✅ Email validated`
     - `📅 Creating appointment`
     - `📆 Creating Google Calendar event`
     - `📧 Sending confirmation email`
     - `📊 Appointment creation summary`
   - **Database** - Check `appointments` table
   - **Email inbox** - Should receive confirmation email
   - **Google Calendar** - Should see the event

## Logging

All operations are logged with emoji prefixes for easy scanning:

- `📧` - Email operations
- `📅` - Appointment operations
- `📆` - Calendar operations
- `✅` - Success
- `❌` - Error
- `📊` - Summary/status

## Error Handling

The system is designed to be resilient:

1. **Email validation fails** → HTTP 400, clear error message, AI re-asks
2. **Calendar creation fails** → Appointment still saved, error logged
3. **Email sending fails** → Appointment still saved, error logged
4. **All errors stored** in `appointment.meta_data` for debugging

## Database Schema

Appointments are stored with:
- `id` - Unique appointment ID
- `call_id` - Associated call (if from voice call)
- `org_id` - Organization
- `title`, `description` - Appointment details
- `start_time`, `end_time` - When
- `attendee_email`, `attendee_name` - Who
- `google_calendar_event_id` - Calendar event ID
- `google_calendar_link` - Link to view event
- `calendar_invite_sent` - Boolean flag
- `status` - scheduled/confirmed/cancelled
- `meta_data` - JSONB with errors, email IDs, etc.

## Production Checklist

- [x] Email validation with regex
- [x] Email sending service (Resend)
- [x] Google Calendar integration
- [x] Real-time transcript saving
- [x] Comprehensive logging
- [x] Error handling at all levels
- [x] State management
- [x] System prompt enforcement
- [ ] Resend API key configured
- [ ] Google Calendar credentials configured
- [ ] Test end-to-end flow

## Troubleshooting

### Appointments not saving
- Check backend logs for errors
- Verify database connection
- Check `appointments` table exists

### Email not sending
- Verify `RESEND_API_KEY` is set
- Check Resend dashboard for delivery status
- Check backend logs for email errors

### Calendar not creating
- Verify Google Calendar credentials
- Check backend logs for calendar errors
- Verify `GOOGLE_REFRESH_TOKEN` is valid

### AI not asking for email
- Check system prompt is being used
- Verify Realtime API session configuration
- Check backend logs for tool calls

