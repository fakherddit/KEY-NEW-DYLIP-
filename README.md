# KEY-NEW-DYLIP-

## StoneiOS Cheats Key Management System

A comprehensive Telegram bot and API server for managing license keys, device tracking, and user access control.

## Features

### Key Management
- 🔑 **Generate Keys** with custom durations (1 day, 7 days, 30 days, or lifetime)
- 👥 **Device Limits** - Single user, multi-user, or global unlimited keys
- 🚫 **Ban/Unban Keys** - Instantly revoke or restore access
- ⏸ **Pause Keys** - Temporarily suspend key usage
- 🔄 **Reset HWID** - Clear device registrations for key reuse
- 🗑️ **Delete Keys** - Permanently remove keys from database

### User Features
- 📋 **List All Keys** - View all active keys with status
- 🔍 **Check Key Stats** - See device usage and expiration details
- 🛒 **Buy Keys** - Direct link to purchase

### Security
- 🔒 **Admin-only Access** - Bot restricted to authorized admin user
- 🔐 **HWID Tracking** - Hardware ID-based device authentication
- ⏰ **Expiration Dates** - Automatic key expiry management
- 📊 **Real-time Status** - Active, banned, or paused states

## Installation

### Prerequisites
- Python 3.7+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram Admin User ID

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/fakherddit/KEY-NEW-DYLIP-.git
cd KEY-NEW-DYLIP-
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export BOT_TOKEN="your_telegram_bot_token"
export ADMIN_ID="your_telegram_user_id"
```

4. Run the server:
```bash
python server.py
```

### Deploy on Render

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Set environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `ADMIN_ID`: Your Telegram user ID
5. Deploy!

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token from BotFather | Yes |
| `ADMIN_ID` | Telegram User ID of admin (set to 0 to allow all) | Yes |
| `PORT` | Server port (default: 5000) | No |

## Bot Commands

### Quick Actions (Keyboard Buttons)
- `🔑 Gen 1 Day (1 Device)` - Generate 24-hour key
- `🔑 Gen 7 Days (1 Device)` - Generate 1-week key
- `🔑 Gen 30 Days (1 Device)` - Generate 1-month key
- `🌍 Gen Global Key` - Generate unlimited device key
- `📋 List Keys` - View all keys
- `🛠 Custom Gen` - Custom key generation

### Management Commands
- `/start` or `/help` - Show main menu
- `/gen [days] [devices]` - Generate custom key
  - Example: `/gen 30 5` (30 days, 5 devices)
- `/reset_[KEY]` - Reset device bindings for a key
- `/ban_[KEY]` - Ban a specific key
- `/del_[KEY]` - Delete a key

### Quick Ban
Simply paste a key in chat to instantly ban it!

## API Endpoints

### POST /check
Validates a key and registers device.

**Request:**
```json
{
  "key": "STONEIOS-XXXXXXXXXX",
  "udid": "device_hardware_id"
}
```

**Note:** `udid` stands for Unique Device ID (also referred to as HWID - Hardware ID in the bot interface).

**Response (Success):**
```json
{
  "status": "success",
  "expiry": "2026-02-28",
  "message": "Welcome Back"
}
```

**Response (Failure):**
```json
{
  "status": "failed",
  "message": "Key EXPIRED"
}
```

### GET /
Health check endpoint.

## Key Format

Keys follow the format: `STONEIOS-XXXXXXXXXX`

Where `XXXXXXXXXX` is a 10-character random string of uppercase letters and digits.

## Data Storage

Keys are stored in `keys.json` with the following structure:

```json
{
  "STONEIOS-ABC123XYZ0": {
    "expiry": "2026-02-28",
    "max_devices": 1,
    "used_hwids": ["device1_hwid"],
    "status": "active",
    "created_at": "2026-01-30 22:00:00"
  }
}
```

**Note:** On Render's free tier, file storage resets on restart. For production, consider using a database (PostgreSQL, MongoDB, etc.).

## Key Types

1. **Single Device Key** - Binds to one device only
2. **Multi-Device Key** - Allows N devices (specified during generation)
3. **Global Key** - Unlimited devices (max_devices > 900000)

## Key States

- **Active** ✅ - Key is working normally
- **Banned** ❌ - Key is permanently disabled
- **Paused** ⏸ - Key is temporarily suspended

## Security Considerations

⚠️ **Important Security Notes:**

1. **Never commit your BOT_TOKEN** to version control
2. **Restrict ADMIN_ID** to trusted users only
3. Consider using environment-specific configs
4. Use HTTPS for API endpoints in production
5. Implement rate limiting for API calls
6. Regular backups of keys.json

## Development

### Project Structure
```
KEY-NEW-DYLIP-/
├── server.py          # Main application (Bot + API)
├── requirements.txt   # Python dependencies
├── keys.json         # Key database (auto-generated)
└── README.md         # This file
```

### Adding Features

To add new bot commands:
1. Add handler in `server.py` using `@bot.message_handler()`
2. Implement command logic
3. Update keyboard buttons if needed
4. Test locally before deploying

## Troubleshooting

### Bot not responding
- Verify BOT_TOKEN is correct
- Check ADMIN_ID matches your Telegram user ID
- View server logs for errors

### Keys not persisting
- Ensure write permissions for keys.json
- On Render free tier, use external database for persistence

### API not accessible
- Check PORT environment variable
- Verify firewall settings
- Ensure server is running on 0.0.0.0

## Support & Contact

For purchases or support, contact: [@FAKHERDDIN5](https://t.me/FAKHERDDIN5)

## License

This project is provided as-is for educational and commercial use.

## Disclaimer

This software is provided for license key management purposes. Users are responsible for complying with all applicable laws and regulations in their jurisdiction.