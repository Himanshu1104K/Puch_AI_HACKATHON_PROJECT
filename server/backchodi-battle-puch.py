# Puch-compatible Backchodi Battle MCP Server
# This server provides AI-powered witty banter battles with proper user authentication and identification

import asyncio
from typing import Annotated, Dict, List, Optional, Literal
import uuid
import time
import random
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp.server.auth.provider import AccessToken
from mcp import ErrorData, McpError
from mcp.types import TextContent, INVALID_PARAMS, INTERNAL_ERROR
from pydantic import Field, BaseModel

from langchain_xai import ChatXAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Env ---
load_dotenv()
TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
XAI_API_KEY = os.environ.get("XAI_API_KEY")
assert TOKEN, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"
assert XAI_API_KEY is not None, "Please set XAI_API_KEY in your .env file"


# --- Auth ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(
            public_key=k.public_key, jwks_uri=None, issuer=None, audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token, client_id="backchodi-client", scopes=["*"], expires_at=None
            )
        return None


# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None


# --- MCP Server Setup ---
mcp = FastMCP(
    "Backchodi Battle MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# Initialize Grok API client
GROK_CLIENT = None


def initialize_grok_client():
    """Initialize Grok API client with X.AI configuration"""
    global GROK_CLIENT
    try:
        GROK_CLIENT = ChatXAI(model="grok-3-beta", api_key=XAI_API_KEY)
        return True
    except Exception as e:
        print(f"Failed to initialize Grok client: {e}")
        return False


# Initialize on module load
initialize_grok_client()


class GameMode(Enum):
    SOLO = "solo"
    DUEL = "duel"


class GameState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    SCORING = "scoring"
    FINISHED = "finished"


@dataclass
class Player:
    id: str
    name: str
    score: float = 0.0
    messages: List[str] = field(default_factory=list)


@dataclass
class GameSession:
    session_id: str
    mode: GameMode
    state: GameState
    created_at: float
    players: List[Player] = field(default_factory=list)
    ai_messages: List[str] = field(default_factory=list)
    current_round: int = 0
    max_rounds: int = 5
    winner: Optional[str] = None


# User-specific storage for game sessions
user_game_sessions: Dict[str, Dict[str, GameSession]] = {}


def _user_sessions(puch_user_id: str) -> Dict[str, GameSession]:
    """Get user-specific game sessions"""
    if not puch_user_id:
        raise McpError(
            ErrorData(code=INVALID_PARAMS, message="puch_user_id is required")
        )
    return user_game_sessions.setdefault(puch_user_id, {})


def _error(code, msg):
    raise McpError(ErrorData(code=code, message=msg))


async def generate_grok_backchodi(context: str = "", player_name: str = "") -> str:
    """Generate powerful, challenging backchodi using Grok AI"""
    if not GROK_CLIENT:
        # Fallback to challenging backchodi
        fallback_starters = [
            "Arre bhai, tumhara confidence dekh kar lagta hai ki main tumhe roast karne ki zaroorat hi nahi! Kya bologe ab?",
            "Yaar tumhara style dekh kar lagta hai tumne fashion advice Google se li hai - galat search results mili! Ab defend karo!",
            "Bhai tumhara sense of humor itna predictable hai ki main already jaanta hun tum kya jawab doge! Surprise me kar sakte ho?",
        ]
        return random.choice(fallback_starters)

    try:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a savage backchodi champion who creates powerful, challenging roasts that demand clever responses. Your goal is to create backchodi that puts the opponent on the spot and forces them to think of a smart comeback.",
                ),
                (
                    "user",
                    """Generate a powerful, challenging backchodi (roast) in Hindi-English mix that DEMANDS a response from the opponent.

Context: {context}
Target: {player_name}

Requirements:
- Create a CHALLENGING statement that requires a smart comeback
- Mix Hindi and English naturally (Hinglish)
- Use slang like "arre", "yaar", "bhai", "dekh", "lagta hai"
- Make it witty but not offensive
- Length: 25-100 characters
- End with a challenge or question that demands response
- Make opponent think hard for a good counter

Examples of powerful backchodi:
- "Arre bhai, tumhara confidence dekh kar lagta hai mirror se paise lete ho! Kya defense hai tumhara?"
- "Yaar tumhara style dekh kar lagta hai tumne YouTube se sikha hai 'How to be cool in 5 minutes' - fail video! Ab batao kya khaas hai tumme?"
- "Bhai tumhara attitude dekh kar lagta hai Netflix pe tumhara biopic aayega - 'How NOT to be awesome'! Counter kar sakte ho?"

Generate only the challenging backchodi, nothing else.""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke(
            {
                "context": context if context else "Challenging backchodi battle",
                "player_name": player_name if player_name else "opponent",
            }
        )
        return response

    except Exception as e:
        print(f"Grok API error: {e}")
        fallback_starters = [
            "Arre bhai, tumhara confidence dekh kar lagta hai ki main tumhe roast karne ki zaroorat hi nahi! Kya bologe ab?",
            "Yaar tumhara style dekh kar lagta hai tumne fashion advice Google se li hai - galat search results mili! Ab defend karo!",
            "Bhai tumhara sense of humor itna predictable hai ki main already jaanta hun tum kya jawab doge! Surprise me kar sakte ho?",
        ]
        return random.choice(fallback_starters)


async def score_message_with_grok(message: str, context: str = "", ai_challenge: str = "") -> tuple[float, str]:
    """Score a backchodi message using Grok AI based on how well it responds to the AI's challenge"""
    if not GROK_CLIENT:
        score = generate_score(message)
        response = await generate_grok_scoring_response(score, message)
        return score, response

    try:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a savage backchodi battle judge who evaluates how well a player responds to challenges. Judge based on the quality of the comeback to the specific AI challenge presented.",
                ),
                (
                    "user",
                    """Evaluate this backchodi response on a scale of 1-10 based on how well it counters the AI's challenge:

AI's Challenge: "{ai_challenge}"
Player's Response: "{message}"
Context: {context}

Scoring criteria:
1. RESPONSE RELEVANCE (1-3 points): How well does it address/counter the AI's specific challenge?
2. COMEBACK QUALITY (1-3 points): How witty and clever is the counter-attack?
3. HINGLISH STYLE (1-2 points): Natural use of Hindi-English mix and slang
4. CREATIVITY & IMPACT (1-2 points): Originality and punch of the response

Bonus considerations:
- Did they turn the AI's attack back on them?
- Did they cleverly deflect or counter-roast?
- Is it a smart, unexpected response?
- Does it show quick thinking?

Provide:
1. A numerical score (1.0-10.0)
2. A brief feedback in Hinglish explaining what worked/didn't work

Format: SCORE|FEEDBACK
Example: 8.5|Epic counter bhai! Tumne AI ko hi roast kar diya! 🔥
Example: 4.2|Weak response yaar, AI ka challenge properly address nahi kiya! 😅""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke(
            {
                "message": message,
                "ai_challenge": ai_challenge if ai_challenge else "General challenge",
                "context": context if context else "Backchodi battle",
            }
        )

        if "|" in response:
            score_str, feedback = response.split("|", 1)
            try:
                score = float(score_str.strip())
                score = max(1.0, min(10.0, score))
                return score, feedback.strip()
            except ValueError:
                pass

        score_match = re.search(r"(\d+\.?\d*)", response)
        if score_match:
            score = float(score_match.group(1))
            score = max(1.0, min(10.0, score))
            return score, response

        return 5.0, "Good attempt! 👍"

    except Exception as e:
        print(f"Grok scoring error: {e}")
        score = generate_score(message)
        response = await generate_grok_scoring_response(score, message)
        return score, response


def generate_score(message: str) -> float:
    """Generate a score for backchodi based on message characteristics"""
    score = 5.0
    length = len(message)
    if 20 <= length <= 100:
        score += 1.0
    elif length > 100:
        score += 0.5

    if any(
        word in message.lower()
        for word in ["lagta", "dekh", "sun", "arre", "yaar", "bhai"]
    ):
        score += 1.0

    if any(char in message for char in ["!", "😂", "🔥", "💯"]):
        score += 0.5

    score += random.uniform(-1.0, 1.0)
    return max(1.0, min(10.0, score))


async def generate_grok_scoring_response(score: float, message: str = "") -> str:
    """Generate dynamic scoring response using Grok AI"""
    if not GROK_CLIENT:
        return get_scoring_response(score)

    try:
        if score >= 8.0:
            tone = "extremely impressed and excited"
        elif score >= 6.0:
            tone = "moderately impressed but encouraging"
        else:
            tone = "constructively critical but supportive"

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a witty Hinglish judge giving feedback on backchodi battles. Be authentic and engaging.",
                ),
                (
                    "user",
                    f"""Generate a brief, enthusiastic feedback response in Hinglish style for a backchodi message that scored {score:.1f}/10.

Message that was scored: "{message}"
Tone: {tone}

Style guidelines:
- Mix Hindi and English naturally
- Use slang like "yaar", "bhai", "arre"
- Keep it 10-25 words max
- Include appropriate emojis
- Be authentic to Indian humor culture

Generate only the feedback message, nothing else.""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke({})
        return response.strip()

    except Exception as e:
        print(f"Grok scoring response error: {e}")
        return get_scoring_response(score)


def get_scoring_response(score: float) -> str:
    """Get appropriate response based on score (fallback function)"""
    if score >= 8.0:
        responses = [
            "Ekdum mast! Sach mein backchod ho tum! 👏",
            "Perfect! Ye backchodi ke liye Nobel prize milna chahiye! 🏆",
        ]
        return random.choice(responses)
    elif score >= 6.0:
        responses = [
            "Waah bhai, ekdum solid comeback! 🔥",
            "Good attempt, but thoda aur spice chahiye tha! 🌶️",
        ]
        return random.choice(responses)
    else:
        responses = [
            "Thoda weak tha yaar, but effort ke liye marks milenge! 😅",
            "Arre yaar, ye kya tha? Bachpan wali jokes mat maro! 🤨",
        ]
        return random.choice(responses)


async def generate_grok_game_verdict(final_score: float, player_name: str = "") -> str:
    """Generate dynamic game ending verdict using Grok AI"""
    if not GROK_CLIENT:
        # Fallback to hardcoded verdicts
        if final_score >= 7.0:
            return "🏆 **ULTIMATE BACKCHOD!** You're a legend! 👑"
        elif final_score >= 5.0:
            return "🔥 **DECENT BACKCHOD!** Not bad, keep practicing! 👍"
        else:
            return "😅 **BEGINNER BACKCHOD!** You need more practice! 💪"

    try:
        if final_score >= 7.0:
            performance_level = "outstanding"
        elif final_score >= 5.0:
            performance_level = "decent"
        else:
            performance_level = "beginner"

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an enthusiastic Hinglish game show host announcing final results of a backchodi battle.",
                ),
                (
                    "user",
                    f"""Generate an exciting final verdict for a player who scored {final_score:.1f}/10 in a backchodi battle.

Player name: {player_name if player_name else "Player"}
Performance level: {performance_level}

Style guidelines:
- Mix Hindi and English naturally  
- Use excitement and energy
- Include appropriate emojis
- Keep it 8-15 words
- Make it feel like a game show announcement
- Use terms like "backchod", "legend", "champion" etc.

Generate only the verdict message with emojis, nothing else.""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke({})
        return response.strip()

    except Exception as e:
        print(f"Grok verdict error: {e}")
        # Fallback to hardcoded verdicts
        if final_score >= 7.0:
            return "🏆 **ULTIMATE BACKCHOD!** You're a legend! 👑"
        elif final_score >= 5.0:
            return "🔥 **DECENT BACKCHOD!** Not bad, keep practicing! 👍"
        else:
            return "😅 **BEGINNER BACKCHOD!** You need more practice! 💪"


async def generate_grok_winner_announcement(
    player1_name: str, player1_score: float, player2_name: str, player2_score: float
) -> str:
    """Generate dynamic winner announcement for duel battles using Grok AI"""
    if not GROK_CLIENT:
        # Fallback to hardcoded announcements
        if player1_score > player2_score:
            return f"🏆 **{player1_name} WINS!**"
        elif player2_score > player1_score:
            return f"🏆 **{player2_name} WINS!**"
        else:
            return "🤝 **IT'S A TIE!**"

    try:
        if player1_score > player2_score:
            winner = player1_name
            loser = player2_name
            result_type = "clear winner"
        elif player2_score > player1_score:
            winner = player2_name
            loser = player1_name
            result_type = "clear winner"
        else:
            winner = "tie"
            loser = ""
            result_type = "tie"

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an energetic Hinglish sports commentator announcing the winner of an epic backchodi battle.",
                ),
                (
                    "user",
                    f"""Generate an exciting winner announcement for a backchodi duel battle.

Player 1: {player1_name} (Score: {player1_score:.1f}/10)
Player 2: {player2_name} (Score: {player2_score:.1f}/10)
Result: {result_type}
{"Winner: " + winner if result_type != "tie" else "It's a tie!"}

Style guidelines:
- Mix Hindi and English naturally
- Use sports commentary excitement  
- Include appropriate emojis
- Keep it 5-12 words
- Make it feel like a championship announcement
- Use terms like "champion", "winner", "epic battle" etc.

Generate only the winner announcement with emojis, nothing else.""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke({})
        return response.strip()

    except Exception as e:
        print(f"Grok winner announcement error: {e}")
        # Fallback to hardcoded announcements
        if player1_score > player2_score:
            return f"🏆 **{player1_name} WINS!**"
        elif player2_score > player1_score:
            return f"🏆 **{player2_name} WINS!**"
        else:
            return "🤝 **IT'S A TIE!**"


async def generate_grok_waiting_message(context: str = "waiting") -> str:
    """Generate dynamic waiting/status messages using Grok AI"""
    if not GROK_CLIENT:
        # Fallback messages
        fallback_messages = [
            "⏳ Waiting for the next move...",
            "🔥 Battle is heating up!",
            "🎮 Game in progress...",
            "💪 Bring your A-game!",
        ]
        return random.choice(fallback_messages)

    try:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an energetic Hinglish game host creating engaging status messages for backchodi battles.",
                ),
                (
                    "user",
                    f"""Generate a brief, energetic status message for a backchodi battle.

Context: {context}

Style guidelines:
- Mix Hindi and English naturally
- Use excitement and energy
- Include appropriate emojis
- Keep it 5-10 words max
- Make it feel encouraging and fun
- Use gaming/battle terminology

Generate only the status message with emojis, nothing else.""",
                ),
            ]
        )

        chain = prompt_template | GROK_CLIENT | StrOutputParser()
        response = await chain.ainvoke({})
        return response.strip()

    except Exception as e:
        print(f"Grok waiting message error: {e}")
        # Fallback messages
        fallback_messages = [
            "⏳ Waiting for the next move...",
            "🔥 Battle is heating up!",
            "🎮 Game in progress...",
            "💪 Bring your A-game!",
        ]
        return random.choice(fallback_messages)


# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER


# --- Tool descriptions (rich) ---
START_BATTLE_DESCRIPTION = RichToolDescription(
    description="Start a new Backchodi Battle game for a specific user.",
    use_when="User wants to start a solo or duel backchodi battle game.",
    side_effects="Creates a new game session for the user.",
)

JOIN_BATTLE_DESCRIPTION = RichToolDescription(
    description="Join an existing duel battle using session ID.",
    use_when="User wants to join a duel battle that someone else created.",
    side_effects="Adds the user to an existing game session and starts the battle.",
)

SEND_BACKCHODI_DESCRIPTION = RichToolDescription(
    description="Send a backchodi message in an active battle.",
    use_when="User wants to send their witty response in an ongoing battle.",
    side_effects="Processes the message, scores it, and continues the battle.",
)

GET_STATUS_DESCRIPTION = RichToolDescription(
    description="Get current status of a game session.",
    use_when="User wants to check the progress of their battle.",
    side_effects="None.",
)

LIST_GAMES_DESCRIPTION = RichToolDescription(
    description="List all active games for a user.",
    use_when="User wants to see their ongoing battles.",
    side_effects="None.",
)

TEST_GROK_DESCRIPTION = RichToolDescription(
    description="Test Grok API connection and generate sample content.",
    use_when="User wants to verify AI integration is working properly.",
    side_effects="None.",
)

CONFIGURE_GROK_DESCRIPTION = RichToolDescription(
    description="Configure Grok API key for AI-powered responses.",
    use_when="User needs to set up or update their Grok API key.",
    side_effects="Updates the global Grok client configuration.",
)

GAME_RULES_DESCRIPTION = RichToolDescription(
    description="Get comprehensive rules and instructions for Backchodi Battle.",
    use_when="User wants to understand how to play the game.",
    side_effects="None.",
)


# --- Tools ---
@mcp.tool(description=START_BATTLE_DESCRIPTION.model_dump_json())
async def start_backchodi_battle(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    mode: Annotated[Literal["solo", "duel"], Field(description="Game mode")],
    player_name: Annotated[
        str, Field(description="Name of the player starting the game")
    ],
) -> list[TextContent]:
    """Start a new Backchodi Battle game."""
    try:
        user_sessions = _user_sessions(puch_user_id)

        # Check if there's already an active session for this user
        active_sessions = [
            s
            for s in user_sessions.values()
            if s.state in [GameState.WAITING, GameState.ACTIVE]
        ]

        if active_sessions:
            return [
                TextContent(
                    type="text",
                    text=f"Game already in progress! Session ID: {active_sessions[0].session_id}",
                )
            ]

        session_id = f"{puch_user_id}_{uuid.uuid4().hex[:8]}"

        session = GameSession(
            session_id=session_id,
            mode=GameMode(mode),
            state=GameState.WAITING if mode == "duel" else GameState.ACTIVE,
            created_at=time.time(),
            players=[Player(id="player_1", name=player_name)],
        )

        user_sessions[session_id] = session

        if mode == "solo":
            ai_opener = await generate_grok_backchodi(
                context="Solo battle start", player_name=player_name
            )
            session.ai_messages.append(ai_opener)
            session.current_round = 1

            result = f"""🎮 **Backchodi Battle Started!** 
**Mode:** Solo Battle
**Session ID:** {session_id}
**Round:** {session.current_round}/{session.max_rounds}

🤖 **AI says:** {ai_opener}

Now it's your turn! Reply with your best backchodi! 🔥"""
        else:
            result = f"""🎮 **Backchodi Battle Created!** 
**Mode:** Duel Battle
**Session ID:** {session_id}
**Creator:** {player_name}

Waiting for opponent to join! Share this session ID: `{session_id}`
Opponent can join using the join_battle tool with this session ID."""

        return [TextContent(type="text", text=result)]
    except McpError:
        raise
    except Exception as e:
        _error(INTERNAL_ERROR, str(e))


@mcp.tool(description=JOIN_BATTLE_DESCRIPTION.model_dump_json())
async def join_battle(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    session_id: Annotated[str, Field(description="The session ID to join")],
    player_name: Annotated[str, Field(description="Name of the joining player")],
) -> list[TextContent]:
    """Join an existing duel battle."""
    try:
        user_sessions = _user_sessions(puch_user_id)

        if session_id not in user_sessions:
            return [
                TextContent(type="text", text="Invalid session ID! Game not found.")
            ]

        session = user_sessions[session_id]

        if session.mode != GameMode.DUEL:
            return [TextContent(type="text", text="This is not a duel battle!")]

        if session.state != GameState.WAITING:
            return [TextContent(type="text", text="Game is not accepting new players!")]

        if len(session.players) >= 2:
            return [TextContent(type="text", text="Battle is already full!")]

        session.players.append(Player(id="player_2", name=player_name))
        session.state = GameState.ACTIVE
        session.current_round = 1

        ai_opener = await generate_grok_backchodi(
            context="Duel battle topic",
            player_name=f"{session.players[0].name} vs {player_name}",
        )
        session.ai_messages.append(ai_opener)

        result = f"""🎮 **Battle Joined Successfully!** 
**Players:** {session.players[0].name} vs {session.players[1].name}
**Round:** {session.current_round}/{session.max_rounds}

🤖 **AI starts the topic:** {ai_opener}

Now both players can start their backchodi battle! 🔥🔥"""

        return [TextContent(type="text", text=result)]
    except McpError:
        raise
    except Exception as e:
        _error(INTERNAL_ERROR, str(e))


@mcp.tool(description=SEND_BACKCHODI_DESCRIPTION.model_dump_json())
async def send_backchodi(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    session_id: Annotated[str, Field(description="The session ID")],
    player_name: Annotated[
        str, Field(description="Name of the player sending message")
    ],
    message: Annotated[str, Field(description="The backchodi message")],
) -> list[TextContent]:
    """Send a backchodi message in the battle."""
    try:
        user_sessions = _user_sessions(puch_user_id)

        if session_id not in user_sessions:
            return [
                TextContent(type="text", text="Invalid session ID! Game not found.")
            ]

        session = user_sessions[session_id]

        if session.state not in [GameState.ACTIVE, GameState.SCORING]:
            return [TextContent(type="text", text="Game is not active!")]

        # Find player
        player = None
        for p in session.players:
            if p.name == player_name:
                player = p
                break

        if not player:
            return [TextContent(type="text", text="Player not found in this game!")]

        player.messages.append(message)

        if session.mode == GameMode.SOLO:
            # Score the current round based on AI's challenge
            current_round_num = session.current_round
            # Get the latest AI challenge (the one player is responding to)
            ai_challenge = session.ai_messages[-1] if session.ai_messages else "General challenge"
            
            score, response_text = await score_message_with_grok(
                message, 
                context=f"Solo battle round {current_round_num}",
                ai_challenge=ai_challenge
            )
            player.score += score
            session.current_round += 1

            if session.current_round <= session.max_rounds:
                ai_response = await generate_grok_backchodi(
                    context=f"Counter-attack round {session.current_round}",
                    player_name=player.name,
                )
                session.ai_messages.append(ai_response)

                result = f"""🎯 **Round {current_round_num}/{session.max_rounds} Score:** {score:.1f}/10 - {response_text}
**Total Score:** {player.score:.1f}
**Next Round:** {session.current_round}/{session.max_rounds}

🤖 **AI counter-attacks:** {ai_response}

Your turn again! 🔥"""
            else:
                session.state = GameState.FINISHED
                final_score = player.score / session.max_rounds

                verdict = await generate_grok_game_verdict(final_score, player.name)

                result = f"""🎯 **Round {current_round_num}/{session.max_rounds} Final Score:** {score:.1f}/10 - {response_text}

🎮 **GAME FINISHED!**
**Total Score:** {player.score:.1f}/{session.max_rounds * 10}
**Average:** {final_score:.1f}/10

{verdict}

Thanks for playing! Start a new game anytime! 🎉"""

        else:  # Duel mode
            other_player = None
            for p in session.players:
                if p.name != player_name:
                    other_player = p
                    break

            current_round_messages = len(
                [msg for p in session.players for msg in p.messages]
            )

            if current_round_messages % 2 == 0:
                session.current_round += 1

                if session.current_round > session.max_rounds:
                    session.state = GameState.FINISHED

                    # Score all messages with AI context
                    ai_topic = session.ai_messages[0] if session.ai_messages else "General duel topic"
                    
                    player1_scores = []
                    for msg in session.players[0].messages:
                        score, _ = await score_message_with_grok(
                            msg, 
                            context=f"Duel evaluation - {session.players[0].name}",
                            ai_challenge=f"Duel topic: {ai_topic}"
                        )
                        player1_scores.append(score)

                    player2_scores = []
                    for msg in session.players[1].messages:
                        score, _ = await score_message_with_grok(
                            msg, 
                            context=f"Duel evaluation - {session.players[1].name}",
                            ai_challenge=f"Duel topic: {ai_topic}"
                        )
                        player2_scores.append(score)

                    player1_avg = (
                        sum(player1_scores) / len(player1_scores)
                        if player1_scores
                        else 0
                    )
                    player2_avg = (
                        sum(player2_scores) / len(player2_scores)
                        if player2_scores
                        else 0
                    )

                    session.players[0].score = player1_avg
                    session.players[1].score = player2_avg

                    if player1_avg > player2_avg:
                        session.winner = session.players[0].name
                    elif player2_avg > player1_avg:
                        session.winner = session.players[1].name
                    else:
                        session.winner = None

                    winner_text = await generate_grok_winner_announcement(
                        session.players[0].name,
                        player1_avg,
                        session.players[1].name,
                        player2_avg,
                    )

                    result = f"""🎮 **DUEL FINISHED!**
**Final Scores:**
• {session.players[0].name}: {player1_avg:.1f}/10
• {session.players[1].name}: {player2_avg:.1f}/10

{winner_text}

Epic battle! 🔥🔥 Start a new game anytime! 🎉"""
                else:
                    waiting_msg = await generate_grok_waiting_message(
                        "duel battle waiting"
                    )
                    result = f"""✅ **Round {session.current_round}/{session.max_rounds} Message sent!** 
**Messages this round:** {current_round_messages}/2

{waiting_msg} Waiting for {other_player.name if other_player and current_round_messages % 2 == 1 else 'next round'}!"""
            else:
                waiting_msg = await generate_grok_waiting_message("duel battle waiting")
                result = f"""✅ **Round {session.current_round}/{session.max_rounds} Message sent!** 
**Messages this round:** {current_round_messages}/2

{waiting_msg} Waiting for {other_player.name if other_player and current_round_messages % 2 == 1 else 'next round'}!"""

        return [TextContent(type="text", text=result)]
    except McpError:
        raise
    except Exception as e:
        _error(INTERNAL_ERROR, str(e))


@mcp.tool(description=GET_STATUS_DESCRIPTION.model_dump_json())
async def get_game_status(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    session_id: Annotated[str, Field(description="The session ID to check")],
) -> list[TextContent]:
    """Get current status of a game session."""
    try:
        user_sessions = _user_sessions(puch_user_id)

        if session_id not in user_sessions:
            return [
                TextContent(type="text", text="Invalid session ID! Game not found.")
            ]

        session = user_sessions[session_id]

        status = f"""🎮 **Game Status**
**Session ID:** {session_id}
**Mode:** {session.mode.value.title()}
**State:** {session.state.value.title()}
**Round:** {session.current_round}/{session.max_rounds}

**Players:**"""

        for i, player in enumerate(session.players, 1):
            status += f"\n• Player {i}: {player.name}"
            if session.mode == GameMode.SOLO or session.state == GameState.FINISHED:
                status += f" (Score: {player.score:.1f})"

        if session.state == GameState.WAITING:
            status += f"\n\n⏳ Waiting for opponent to join..."
        elif session.state == GameState.ACTIVE:
            status += f"\n\n🔥 Battle in progress!"
        elif session.state == GameState.FINISHED:
            status += f"\n\n🏁 Game finished!"
            if session.winner:
                status += f" Winner: {session.winner}"

        return [TextContent(type="text", text=status)]
    except Exception as e:
        _error(INTERNAL_ERROR, str(e))


@mcp.tool(description=LIST_GAMES_DESCRIPTION.model_dump_json())
async def list_active_games(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
) -> list[TextContent]:
    """List all active games for a user."""
    try:
        user_sessions = _user_sessions(puch_user_id)

        active_games = [
            s
            for s in user_sessions.values()
            if s.state in [GameState.WAITING, GameState.ACTIVE]
        ]

        if not active_games:
            return [
                TextContent(
                    type="text",
                    text="No active games found! Start a new battle with the start_backchodi_battle tool.",
                )
            ]

        result = "🎮 **Active Games:**\n\n"
        for game in active_games:
            result += f"**{game.session_id}**\n"
            result += f"• Mode: {game.mode.value.title()}\n"
            result += f"• State: {game.state.value.title()}\n"
            result += f"• Players: {', '.join([p.name for p in game.players])}\n"
            result += f"• Round: {game.current_round}/{game.max_rounds}\n\n"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        _error(INTERNAL_ERROR, str(e))


@mcp.tool(description=TEST_GROK_DESCRIPTION.model_dump_json())
async def test_grok_connection(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
) -> list[TextContent]:
    """Test the Grok API connection and generate a sample backchodi"""
    try:
        if not GROK_CLIENT:
            return [
                TextContent(
                    type="text",
                    text="❌ Grok client not initialized! Please set XAI_API_KEY environment variable.",
                )
            ]

        test_response = await generate_grok_backchodi(
            context="Connection test", player_name="Test User"
        )

        test_score, test_feedback = await score_message_with_grok(
            "Arre yaar, tumhara style dekh kar lagta hai fashion week se ban kar aaye ho!",
            context="Test scoring",
            ai_challenge=test_response
        )

        result = f"""✅ **Grok Integration Working!**

**Test Backchodi Generated:**
{test_response}

**Test Scoring:**
Score: {test_score:.1f}/10
Feedback: {test_feedback}

🔥 Ready for epic battles!"""

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Grok API Error: {str(e)}\n\nPlease check your XAI_API_KEY and internet connection.",
            )
        ]


@mcp.tool(description=CONFIGURE_GROK_DESCRIPTION.model_dump_json())
async def configure_grok_api(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
    api_key: Annotated[str, Field(description="Your X.AI API key from https://x.ai/")],
) -> list[TextContent]:
    """Configure Grok API key for AI-powered responses and scoring."""
    global GROK_CLIENT

    if not api_key or api_key.strip() == "":
        return [TextContent(type="text", text="❌ Invalid API key provided!")]

    try:
        os.environ["XAI_API_KEY"] = api_key.strip()
        GROK_CLIENT = ChatXAI(model="grok-3-beta", api_key=api_key.strip())

        test_result = await test_grok_connection(puch_user_id)
        test_text = test_result[0].text if test_result else "Test failed"

        if "✅" in test_text:
            return [
                TextContent(
                    type="text",
                    text=f"✅ **Grok API Configured Successfully!**\n\n{test_text}",
                )
            ]
        else:
            return [
                TextContent(
                    type="text", text=f"❌ **Configuration Failed!**\n\n{test_text}"
                )
            ]

    except Exception as e:
        return [
            TextContent(
                type="text", text=f"❌ **Error configuring Grok API:** {str(e)}"
            )
        ]


@mcp.tool(description=GAME_RULES_DESCRIPTION.model_dump_json())
async def get_game_rules(
    puch_user_id: Annotated[str, Field(description="Puch User Unique Identifier")],
) -> list[TextContent]:
    """Get the rules and instructions for Backchodi Battle."""
    rules = """🎮 **BACKCHODI BATTLE RULES**

**🎯 OBJECTIVE:** Show off your witty banter and roasting skills!

**🎮 GAME MODES:**

**1. SOLO MODE:**
• Battle against AI powered by Grok
• AI creates CHALLENGING backchodi that demands response
• You must cleverly counter the AI's specific challenge
• AI judges how well you responded to its challenge (1-10)
• 5 intense rounds total
• Goal: Average 7+ for "Ultimate Backchod" status

**2. DUEL MODE:**
• Battle against a friend
• AI provides challenging topic/starter
• Both players exchange clever responses
• AI judges responses based on challenge context
• Highest average score wins after 5 rounds

**🎯 NEW SCORING CRITERIA (Challenge-Based):**
• RESPONSE RELEVANCE (1-3 points): How well you address AI's challenge
• COMEBACK QUALITY (1-3 points): Wit and cleverness of counter-attack  
• HINGLISH STYLE (1-2 points): Natural Hindi-English mix usage
• CREATIVITY & IMPACT (1-2 points): Originality and punch

**💡 BONUS POINTS FOR:**
• Turning AI's challenge back on them
• Clever deflection or counter-roast
• Unexpected, smart responses
• Quick-thinking comebacks

**📱 AVAILABLE TOOLS:**
• `configure_grok_api` - Setup Grok API
• `test_grok_connection` - Test AI integration
• `start_backchodi_battle` - Start game
• `join_battle` - Join duel
• `send_backchodi` - Send message
• `get_game_status` - Check status
• `list_active_games` - List active games

**🔥 PRO TIPS:**
• Use Hindi/English mix for authenticity
• Reference popular culture
• Keep it light and fun
• Timing matters - don't overthink!
• AI provides contextual, intelligent responses!

Ready to prove you're the ultimate backchod? 🏆"""

    return [TextContent(type="text", text=rules)]


# --- Run MCP Server ---
async def main():
    print("🔥 Starting Backchodi Battle MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)


if __name__ == "__main__":
    asyncio.run(main())
