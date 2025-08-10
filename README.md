# Backchodi Battle MCP Server for Puch AI

This is an AI-powered Hinglish backchodi (witty banter) battle game server that works with Puch AI. Challenge the AI or battle with friends in epic roasting competitions!

## What is MCP?

MCP (Model Context Protocol) allows AI assistants like Puch to connect to external tools and data sources safely. Think of it like giving your AI extra superpowers without compromising security.

## What's Included?

## Main Server

- **[`mcp-bearer-token/backchodi-battle-puch.py`](./mcp-bearer-token/backchodi-battle-puch.py)**  
  The Backchodi Battle MCP server featuring:
  - **Solo Mode**: Battle against Grok AI with intelligent scoring
  - **Duel Mode**: Challenge friends in epic backchodi battles
  - **Dynamic AI Responses**: Grok-3-Beta powered witty comebacks
  - **Contextual Scoring**: AI judges your humor, creativity, and Hinglish skills
  - **User Authentication**: Bearer token auth with user isolation
  - **Personalized Experience**: Custom verdicts and announcements

## Available Tools

- `start_backchodi_battle` - Start solo or duel battles
- `send_backchodi` - Send your witty responses
- `join_battle` - Join friend's duel battles
- `get_game_status` - Check battle progress
- `list_active_games` - View your ongoing battles
- `test_grok_connection` - Test AI integration
- `get_game_rules` - Learn how to play

## Quick Setup Guide

### Step 1: Install Dependencies

First, make sure you have Python 3.11 or higher installed. Then:

```bash
# Create virtual environment
uv venv

# Install all required packages
uv sync

# Activate the environment
source .venv/bin/activate
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root and add your details:

```env
AUTH_TOKEN=your_secret_token_here
MY_NUMBER=919876543210
XAI_API_KEY=your_grok_api_key_here
```

**Important Notes:**

- `AUTH_TOKEN`: This is your secret token for authentication. Keep it safe!
- `MY_NUMBER`: Your WhatsApp number in format `{country_code}{number}` (e.g., `919876543210` for +91-9876543210)
- `XAI_API_KEY`: Your X.AI API key for Grok integration. Get it from https://x.ai/

### Step 3: Run the Backchodi Battle Server

```bash
cd mcp-bearer-token
python backchodi-battle-puch.py
```

You'll see: `🔥 Starting Backchodi Battle MCP server on http://0.0.0.0:8086`

### Step 4: Make It Public (Required by Puch)

Since Puch needs to access your server over HTTPS, you need to expose your local server:

#### Option A: Using ngrok (Recommended)

1. **Install ngrok:**
   Download from https://ngrok.com/download

2. **Get your authtoken:**
   - Go to https://dashboard.ngrok.com/get-started/your-authtoken
   - Copy your authtoken
   - Run: `ngrok config add-authtoken YOUR_AUTHTOKEN`

3. **Start the tunnel:**
   ```bash
   ngrok http 8086
   ```

#### Option B: Deploy to Cloud

You can also deploy this to services like:

- Railway
- Render
- Heroku
- DigitalOcean App Platform

## How to Connect with Puch AI

1. **[Open Puch AI](https://wa.me/+919998881729)** in your browser
2. **Start a new conversation**
3. **Use the connect command:**
   ```
   /mcp connect https://your-domain.ngrok.app/mcp your_secret_token_here
   ```

### Debug Mode

To get more detailed error messages:

```
/mcp diagnostics-level debug
```

## How to Play Backchodi Battle

### Solo Mode
1. Start a solo battle: AI creates **CHALLENGING** backchodi that demands response
2. You must cleverly counter the AI's specific challenge
3. AI judges how well you responded to its challenge (1-10)
4. Battle continues for 5 intense rounds
5. Goal: Average 7+ for "Ultimate Backchod" status!

### Duel Mode
1. Start a duel battle and share session ID with a friend
2. Friend joins using the session ID
3. AI provides challenging topics that demand clever responses
4. Both players must address the challenges with wit and creativity
5. AI judges responses based on challenge context after 5 rounds
6. Highest average score wins the epic battle!

### Pro Tips for Challenge-Response Battles
- **Address the Challenge**: Always respond directly to what AI asks/challenges
- **Turn it Around**: Try to flip the AI's challenge back on them
- **Use Hinglish**: Mix Hindi and English naturally with slang like "yaar", "bhai", "arre"
- **Be Clever**: Show quick thinking and unexpected responses
- **Counter-Roast**: Don't just defend, attack back smartly
- **Stay Relevant**: Your comeback should connect to the AI's specific challenge
- **Cultural References**: Use popular culture and trends in your counters
- **Timing matters**: Quick, witty responses score higher!

## 🤖 AI-Powered Features

### Grok-3-Beta Integration
- **Challenging AI**: Creates powerful backchodi that demand specific responses
- **Challenge-Based Scoring**: AI judges how well you counter its specific challenges
- **Dynamic Challenges**: Never see the same AI challenge twice
- **Contextual Intelligence**: AI understands your response in context of its challenge
- **Personalized Verdicts**: Custom game-ending announcements with your name
- **Sports Commentary**: Epic winner announcements for duel battles
- **Cultural Authenticity**: AI trained on Hinglish humor and Indian culture

### New Challenge-Based Scoring
- **Response Relevance** (1-3 points): How well you address AI's specific challenge
- **Comeback Quality** (1-3 points): Wit and cleverness of your counter-attack
- **Hinglish Style** (1-2 points): Natural Hindi-English mix and slang usage
- **Creativity & Impact** (1-2 points): Originality and punch of response

### Bonus Points For
- **Turning Tables**: Flipping AI's challenge back on them
- **Smart Deflection**: Cleverly avoiding and counter-roasting
- **Quick Thinking**: Unexpected, intelligent responses
- **Counter-Attack**: Not just defending but attacking back

### Fallback System
- Server works even without Grok API
- Graceful degradation to hardcoded responses
- Never crashes, always entertaining!

## 📚 **Additional Documentation Resources**

### **Official Puch AI MCP Documentation**

- **Main Documentation**: https://puch.ai/mcp
- **Protocol Compatibility**: Core MCP specification with Bearer & OAuth support
- **Command Reference**: Complete MCP command documentation
- **Server Requirements**: Tool registration, validation, HTTPS requirements

### **Technical Specifications**

- **JSON-RPC 2.0 Specification**: https://www.jsonrpc.org/specification (for error handling)
- **MCP Protocol**: Core protocol messages, tool definitions, authentication

### **Supported vs Unsupported Features**

**✓ Supported:**

- Core protocol messages
- Tool definitions and calls
- Authentication (Bearer & OAuth)
- Error handling

**✗ Not Supported:**

- Videos extension
- Resources extension
- Prompts extension

## Getting Help

- **Join Puch AI Discord:** https://discord.gg/VMCnMvYx
- **Check Puch AI MCP docs:** https://puch.ai/mcp
- **Puch WhatsApp Number:** +91 99988 81729

---

**Happy Backchodi Battling! 🔥**

Use the hashtag `#BackchodiWithPuch` in your posts about your epic battles!

This Backchodi Battle server brings AI-powered Hinglish humor to Puch AI. Start roasting, get roasted, and become the ultimate backchod champion! 🏆
