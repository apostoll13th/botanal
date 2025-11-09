# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Telegram expense tracking bot built with python-telegram-bot. The bot helps users track expenses, manage budgets, set savings goals, and receive financial reminders. Currently, all code is in a single file (bot.py) which needs refactoring for deployment on Ubuntu server.

**NEW**: The project now includes a web interface for viewing statistics and analytics through a browser.

## Key Commands

### Running the Bot
```bash
# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Run the bot
python bot.py
```

### Running the Web Interface
```bash
# Quick start (runs db + backend + frontend)
docker compose up --build

# Или только веб-часть (поднимет backend, frontend и их зависимости)
./start_web_interface.sh
```

### Dependencies Installation
```bash
# Bot dependencies
pip install python-telegram-bot matplotlib pandas python-dotenv

# Web interface backend
cd backend && pip install -r requirements.txt
```

## Architecture Overview

### Project Structure
- **bot.py** (1,150+ lines): Main Telegram bot functionality
- **backend/**: Flask API for web interface
  - app.py: REST API endpoints
  - requirements.txt: Flask dependencies
- **frontend/**: Web interface (HTML/JS/CSS)
  - index.html: Main page with tabs
  - app.js: JavaScript logic and API calls
  - styles.css: Responsive styling
- **database_migrations.py**: Database migration system

### Current Bot Structure (Monolithic)
- **bot.py**: Contains all functionality including:
  - Database operations (PostgreSQL via psycopg2)
  - Telegram handlers and conversations
  - Chart generation with matplotlib
  - User management and authentication
  - Scheduled tasks and reminders

### Database Schema
- **expenses**: Tracks user expenses (id, user_id, category, amount, date, description, user_name)
- **budgets**: Budget limits by category/period (id, user_id, category, amount, period, user_name)
- **savings_goals**: Financial targets (id, user_id, goal_name, target_amount, current_amount, user_name)
- **reminders**: Scheduled reminders (id, user_id, text, frequency, next_run)
- **users**: User information (user_id, username, user_name)

### Core Features
1. **Expense Management**: Add expenses with categories, view reports
2. **Budget Tracking**: Set budgets by category (daily/weekly/monthly)
3. **Savings Goals**: Create and track progress
4. **Reports**: Generate daily/weekly/monthly reports with charts
5. **Reminders**: Set recurring reminders
6. **Multi-user**: Supports multiple users with username tracking

### Conversation Flows
- EXPENSE_ENTRY: Multi-step expense addition
- BUDGET_SETTING: Category and amount selection
- GOAL_CREATION: Savings goal setup
- REMINDER_CREATION: Reminder configuration

## Important Refactoring Needs

### Before Ubuntu Deployment
1. **Create requirements.txt** with proper versions
2. **Split bot.py** into modules:
   - handlers.py: Command and conversation handlers
   - database.py: Database operations
   - utils.py: Helper functions and chart generation
   - config.py: Configuration management
3. **Add .env.example** file for configuration
4. **Implement proper database migrations** (currently uses try/catch)
5. **Add logging** throughout the application
6. **Create systemd service** for Ubuntu deployment
7. **Add error handling** for network issues and database locks

### Database Migration Issues
The code handles missing columns by catching exceptions and adding them dynamically. This should be replaced with proper migration system.

## Deployment Considerations

### Ubuntu Server Setup
1. Ensure Python 3.8+ is installed
2. Set up virtual environment
3. Configure systemd service for auto-restart
4. Set up logging to file
5. Consider using supervisor or systemd for process management
6. Set up proper file permissions for database

### Security Considerations
- Bot token must be in environment variable, never hardcoded
- Database file permissions should be restricted
- Consider adding user authentication beyond Telegram user_id
- Implement rate limiting for expensive operations (chart generation)

## Common Development Tasks

### Adding New Command
1. Add handler in main() function
2. Create handler function following existing pattern
3. Add to help message in help_command()

### Adding Database Column
1. Add column in init_db() function
2. Update relevant INSERT/UPDATE queries
3. Handle backward compatibility in existing records

### Testing
Currently no tests exist. When adding tests:
- Mock telegram.Update and telegram.ext.CallbackContext
- Test database operations separately
- Test chart generation with sample data

## Known Issues
1. All code in single file makes maintenance difficult
2. Database migrations handled with try/catch blocks
3. Mixed Russian/English in UI and comments
4. No input validation for amounts
5. No pagination for large reports
6. Chart generation can be slow for large datasets
