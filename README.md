# YRHacks 2025 Discord Bot

This is the official Discord bot for [YRHacks](https://yrhacks.ca), York Region's Annual hackathon and Canada's largest high school hackathon.

## Features

- User verification through form registrations
- Team creation, management, and invitations
- Profile management
- Logging and error handling

## Prerequisites

Before setting up the bot, ensure you have the following:

- Python 3.11 or higher
- A supabase account and project
- A Discord bot
  - Enable the Privileged Server Members Intent on the Discord Developer Portal

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yrhacks/yrhacks-2025-bot.git
   cd yrhacks-2025-bot
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python3 -m venv venv  # On Windows: py -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**
   - Copy the schema in `data/schema.sql` and execute it in the Supabase SQL editor for your project

5. **Configure the Bot**
   - Duplicate the example files:
   ```bash
   cp data/config.example.toml data/config.toml
   cp .env.example .env
   cp data/registrations.example.json data/registrations.json
   ```
   - Edit `data/config.toml` with your bot's configuration
   - Edit `.env` with your bot's Discord token and your Supabase credentials
   - Edit `data/registrations.json` with the list of registrations

6. **Run the Bot**
   ```bash
   python3 main.py  # On Windows: py main.py
   ```

The bot is now up and running!

## Deployment
To deploy the bot with a systemd service—for example, on a Google Cloud Compute VM:

1. Copy the example service file:
   ```bash
   cp yrhacks-bot.example.service yrhacks-bot.service
   ```

2. Edit `yrhacks-bot.service` to match your deployment environment

3. Move the service file to `/etc/systemd/system/` on your deployment machine:
   ```bash
   sudo mv yrhacks-bot.service /etc/systemd/system/
   ```

4. Enable and start the service:
   ```bash
   sudo systemctl enable yrhacks-bot
   sudo systemctl start yrhacks-bot
   ```

The bot service will now run in the background!
