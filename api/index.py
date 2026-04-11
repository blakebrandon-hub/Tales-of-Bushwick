<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TALES OF BUSHWICK</title>
    <style>
        /* --- GENTRIFIED BRUTALIST DESIGN SYSTEM --- */
        :root {
            --landlord-white: #f4f4f0;
            --eviction-pink: #ff0055;
            --asphalt-grey: #2a2a2a;
            --stress-border: 2px solid var(--asphalt-grey);
            --font-serif: 'Georgia', 'Times New Roman', serif;
            --font-mono: 'Courier New', Courier, monospace;
        }

        body {
            background-color: var(--landlord-white);
            color: var(--asphalt-grey);
            font-family: var(--font-serif);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }

        #game-container {
            width: 100%;
            max-width: 500px;
            height: 100%;
            display: flex;
            flex-direction: column;
            border-left: var(--stress-border);
            border-right: var(--stress-border);
            background: white;
            position: relative;
        }



        /* --- HUD --- */
        #hud {
            border-bottom: var(--stress-border);
            padding: 15px;
            background-color: var(--landlord-white);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .stat-box { display: flex; flex-direction: column; gap: 4px; }
        .stat-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }

        #dignity-container { width: 100px; height: 12px; border: 1px solid var(--asphalt-grey); background: #fff; }
        #dignity-fill { height: 100%; background-color: var(--asphalt-grey); width: 65%; transition: width 0.3s ease; }
        #liquidity { color: var(--eviction-pink); font-weight: bold; }
        #battery-icon { display: flex; align-items: center; gap: 5px; }

        /* --- NARRATIVE AREA --- */
        #narrative-scroll {
            flex-grow: 1;
            padding: 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .narrative-text { line-height: 1.6; font-size: 1.1rem; }
        
        .system-message {
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: var(--eviction-pink);
            border-left: 2px solid var(--eviction-pink);
            padding-left: 10px;
            margin-top: 10px;
            display: none;
        }

        .loading-bagel {
            display: none;
            text-align: center;
            font-family: var(--font-mono);
            font-size: 2rem;
            animation: spin 1s infinite linear;
            margin-top: 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* --- CHOICES --- */
        #choices-area {
            padding: 20px;
            background-color: var(--landlord-white);
            border-top: var(--stress-border);
            display: flex;
            flex-direction: column;
            gap: 12px;
            min-height: 150px; /* Reserve space */
        }

        .choice-btn {
            background: white;
            border: 1px solid var(--asphalt-grey);
            padding: 15px;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            text-align: left;
            cursor: pointer;
            box-shadow: 3px 3px 0px var(--asphalt-grey);
            transition: transform 0.1s, box-shadow 0.1s;
        }
        .choice-btn:hover { transform: translate(-1px, -1px); box-shadow: 5px 5px 0px var(--eviction-pink); }
        .choice-btn:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0px var(--asphalt-grey); }
        .choice-btn:nth-child(odd) { transform: rotate(-0.5deg); }
        .choice-btn:nth-child(even) { transform: rotate(0.5deg); }

    </style>
</head>
<body>

<div id="game-container">
    
    <header id="hud">
        <div class="stat-box">
            <span class="stat-label">Dignity</span>
            <div id="dignity-container"><div id="dignity-fill"></div></div>
        </div>
        <div class="stat-box" style="align-items: center;">
            <span class="stat-label">Liquidity</span>
            <span id="liquidity">$42.18</span>
        </div>
        <div class="stat-box" style="align-items: flex-end;">
            <span class="stat-label">Batt</span>
            <div id="battery-icon"><span id="battery-level">14%</span> 🔋</div>
        </div>
    </header>

    <main id="narrative-scroll">
        <div id="story-text" class="narrative-text"></div>
        <div id="system-msg" class="system-message"></div>
        <div id="loading" class="loading-bagel">🥯</div>
    </main>

    <footer id="choices-area"></footer>
</div>

<script>

    // API key lives server-side in /api/chat

    const conversationLog = [];
    
    // --- STATE ---
    let gameState = {
        dignity: 65,
        liquidity: 42.18,
        battery: 14,
        time: "8:43 AM"
    };

    // --- PROMPTS ---
    const BASE_PROMPT = `
You are the narrator of TALES OF BUSHWICK, a text adventure about surviving New York.
TONE: Dry, observational, affectionately cynical. 
CORE PRINCIPLE: Mundane situations escalate in plausible, annoying ways.

IMPORTANT: You must output ONLY valid JSON. No markdown fencing. 
Structure:
{
  "text": "The narrative description of the scene...",
  "system": "A short status update (e.g. 'Status: Social Anxiety increased')",
  "choices": [
    {"text": "Option 1 action", "cost": 0, "damage": 5},
    {"text": "Option 2 action", "cost": 0, "damage": 0}
  ]
}

- Keep narrative text under 80 words.
- Provide exactly 2-4 choices.
- 'cost' is money spent. 'damage' is dignity lost.
- If the user action was successful, make the next scene slightly weird.
- If the user failed, make it socially awkward.
`;

    const INITIAL_CONTEXT = "It is 8:17 AM. Radiator is hissing. Roommate Skylar is hogging the bathroom. User has an interview at 9:00 AM in Dumbo.";

    // --- API HANDLER ---
    async function callClaude(userAction, context) {
        const loading = document.getElementById('loading');
        const choicesArea = document.getElementById('choices-area');
        
        loading.style.display = 'block';
        choicesArea.innerHTML = ''; // Clear buttons

        // Add user action to log using .message to match your snippet
        if (userAction) {
            conversationLog.push({ role: 'user', message: userAction });
        }

        try {
            const response = await fetch('/api/chat', {
              method: 'POST',
              headers: { 'content-type': 'application/json' },
              body: JSON.stringify({
                gameState: {
                  dignity: gameState.dignity,
                  liquidity: gameState.liquidity,
                  time: gameState.time
                },
                context: context,
                messages: conversationLog.slice(-10).map(c => ({
                  role: c.role === 'Warden' ? 'assistant' : 'user',
                  content: c.message
                }))
              })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`API Error: ${response.status} - ${errText}`);
            }

            const data = await response.json();
            if (!data.content) return { text: '', system: '', choices: [] };
            let rawMessage = data.content;
            
            // Clean up potentially messy JSON output
            rawMessage = rawMessage.replace(/```json/g, '').replace(/```/g, '').trim();

            // Add AI response to log using .message to match your snippet
            conversationLog.push({ role: 'Warden', message: rawMessage });
            
            return JSON.parse(rawMessage);

        } catch (error) {
            console.error(error);
            return {
                text: "The simulation has crashed. (API Error: " + error.message + ")",
                system: "CRITICAL FAILURE",
                choices: [{ text: "Try Again", cost: 0, damage: 0 }]
            };
        } finally {
            loading.style.display = 'none';
        }
    }

    // --- GAME ENGINE ---
    async function nextTurn(choice = null) {
        let actionText = choice ? choice.text : "Start Game";
        
        // Update Stats locally first
        if (choice) {
            gameState.dignity = Math.max(0, gameState.dignity - (choice.damage || 0));
            gameState.liquidity = gameState.liquidity - (choice.cost || 0);
            
            // Battery drain per turn
            gameState.battery = Math.max(0, gameState.battery - 2);
            
            updateHUD();
        }

        // Get AI Response
        const scene = await callClaude(actionText, INITIAL_CONTEXT);
        
        // Render Scene
        document.getElementById('story-text').innerHTML = scene.text.replace(/\n/g, '<br>');
        
        const sysEl = document.getElementById('system-msg');
        if (scene.system) {
            sysEl.style.display = 'block';
            sysEl.innerText = scene.system;
        } else {
            sysEl.style.display = 'none';
        }

        // Render Choices
        const choicesArea = document.getElementById('choices-area');
        choicesArea.innerHTML = '';
        
        if (scene.choices && scene.choices.length > 0) {
            scene.choices.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'choice-btn';
                btn.innerHTML = `> ${c.text}`;
                btn.onclick = () => nextTurn(c);
                choicesArea.appendChild(btn);
            });
        }
    }

    // --- UTILS ---
    function updateHUD() {
        // Update Dignity
        document.getElementById('dignity-fill').style.width = gameState.dignity + '%';
        if(gameState.dignity < 30) document.getElementById('dignity-fill').style.backgroundColor = 'var(--eviction-pink)';
        
        // Update Liquidity
        document.getElementById('liquidity').innerText = '$' + gameState.liquidity.toFixed(2);
        
        // Update Battery
        const batEl = document.getElementById('battery-level');
        batEl.innerText = gameState.battery + '%';
        if(gameState.battery < 10) batEl.style.color = 'var(--eviction-pink)';
    }

    // --- INITIALIZATION ---
    updateHUD();
    const startBtn = document.createElement('button');
    startBtn.className = 'choice-btn';
    startBtn.innerHTML = '> Start Game';
    startBtn.onclick = () => {
        startBtn.remove();
        nextTurn();
    };
    document.getElementById('choices-area').appendChild(startBtn);

</script>
</body>
</html>
