from flask import Flask, request, jsonify, render_template_string
import threading
import time
import json
import os
import logging
import random
import httpx
from colorama import init, Fore, Style
import fade
import base64

# Initialize colorama
init()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load configuration
try:
    config = json.load(open("config.json", encoding="utf-8"))
except FileNotFoundError:
    config = {
        "capsolver_key": "CAP-F07D1B94AA95CC75D97FADEA88C18299",
        "proxyless": True,
        "change_server_nick": True,
        "change_server_bio": True,
        "bio": "https://discord.gg/axo",
        "nickname": ".gg/axo",
        "license_key": "",
        "port": 5000,
        "host": "0.0.0.0"
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

# Your fingerprint data (truncated for brevity - add all your fingerprints here)
FINGERPRINTS = [
    {
        "ja3": "771,4866-4867-4865-49196-49200-49195-49199-52393-52392-159-158-52394-49327-49325-49326-49324-49188-49192-49187-49191-49162-49172-49161-49171-49315-49311-49314-49310-107-103-57-51-157-156-49313-49309-49312-49308-61-60-53-47-255,0-11-10-35-16-22-23-49-13-43-45-51-21,29-23-30-25-24,0-1-2",
        "useragent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:52.0) Gecko/20100101 Firefox/52.0",
        "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InB0LVBUIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEwNi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTA2LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOiIxNTQxODYiLCJjbGllbnRfZXZlbnRfc291cmNlIjoibnVsbCJ9"
    },
    # Add all your other fingerprints here...
]

# Global variables
boost_tasks = {}
task_id_counter = 0

class BoostVariables:
    def __init__(self):
        self.boosts_done = 0

def solve_captcha(website_url, website_key):
    """Solve captcha using Capsolver"""
    try:
        if not config.get('capsolver_key'):
            return None, "Capsolver key not configured"
        
        payload = {
            "clientKey": config['capsolver_key'],
            "task": {
                "type": "HCaptchaTask",
                "websiteURL": website_url,
                "websiteKey": website_key,
                "proxy": "" if config.get('proxyless', True) else "http://username:password@host:port"
            }
        }
        
        # Create task
        create_response = httpx.post("https://api.capsolver.com/createTask", json=payload)
        task_data = create_response.json()
        
        if task_data.get('errorId') != 0:
            return None, f"Capsolver error: {task_data.get('errorDescription')}"
        
        task_id = task_data['taskId']
        
        # Check task result
        for _ in range(30):  # 30 attempts with 5 second delays
            time.sleep(5)
            result_payload = {"clientKey": config['capsolver_key'], "taskId": task_id}
            result_response = httpx.post("https://api.capsolver.com/getTaskResult", json=result_payload)
            result_data = result_response.json()
            
            if result_data.get('status') == 'ready':
                return result_data['solution']['gRecaptchaResponse'], "Captcha solved successfully"
            elif result_data.get('status') == 'failed':
                return None, f"Captcha solving failed: {result_data.get('errorDescription')}"
        
        return None, "Captcha solving timeout"
        
    except Exception as e:
        return None, f"Captcha error: {str(e)}"

def get_random_fingerprint():
    """Get a random fingerprint from the list"""
    return random.choice(FINGERPRINTS)

def create_http_client(fingerprint):
    """Create HTTP client with specific fingerprint"""
    headers = {
        'User-Agent': fingerprint['useragent'],
        'X-Super-Properties': fingerprint['x-super-properties'],
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Authorization': '',
        'X-Debug-Options': 'bugReporterEnabled',
        'X-Discord-Locale': 'en-US',
        'X-Discord-Timezone': 'America/New_York',
    }
    
    client = httpx.Client(
        headers=headers,
        timeout=30.0,
        follow_redirects=True
    )
    
    return client

def getinviteCode(invite_input):
    """Extract invite code from various Discord invite formats"""
    if "discord.gg" not in invite_input:
        return invite_input
    if "discord.gg/" in invite_input:
        invite = invite_input.split("discord.gg/")[1]
        return invite.split('?')[0]
    if "https://discord.gg/" in invite_input:
        invite = invite_input.split("https://discord.gg/")[1]
        return invite.split('?')[0]
    if "/invite/" in invite_input:
        invite = invite_input.split("/invite/")[1]
        return invite.split('?')[0]
    return invite_input

def load_tokens(months_type):
    """Load tokens based on months type"""
    try:
        filename = f"input/{months_type}m_tokens.txt"
        with open(filename, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
        return tokens
    except:
        return []

def update_profile(client, token):
    """Update user profile with custom bio and nickname"""
    try:
        headers = client.headers.copy()
        headers['Authorization'] = token
        
        # Update bio if enabled
        if config.get('change_server_bio', True):
            bio_data = {"bio": config.get('bio', 'https://discord.gg/axo')}
            bio_response = client.patch("https://discord.com/api/v9/users/@me", json=bio_data)
            if bio_response.status_code == 200:
                logging.info("Bio updated successfully")
        
        # Note: Nickname is set per server, so we'll handle this after joining
        
    except Exception as e:
        logging.error(f"Profile update error: {str(e)}")

def boost_server(token, invite_code, fingerprint, task_id, boost_index):
    """Boost a server with a specific token and fingerprint"""
    try:
        client = create_http_client(fingerprint)
        headers = client.headers.copy()
        headers['Authorization'] = token
        
        # Update profile first
        update_profile(client, token)
        
        # Get guild ID from invite
        invite_response = client.get(f"https://discord.com/api/v9/invites/{invite_code}")
        if invite_response.status_code != 200:
            return False, f"Failed to get invite info: {invite_response.status_code}"
        
        guild_data = invite_response.json().get('guild', {})
        guild_id = guild_data.get('id')
        if not guild_id:
            return False, "No guild ID found in invite"
        
        # Join server first
        join_data = {}
        join_response = client.post(f"https://discord.com/api/v9/invites/{invite_code}", json=join_data)
        if join_response.status_code not in [200, 201, 204]:
            # Try with captcha if join fails
            captcha_sitekey = "4c672d35-0701-42b2-88c3-78380b0db560"  # Discord's hCaptcha sitekey
            captcha_token, captcha_msg = solve_captcha(f"https://discord.com/invite/{invite_code}", captcha_sitekey)
            
            if captcha_token:
                join_data['captcha_key'] = captcha_token
                join_response = client.post(f"https://discord.com/api/v9/invites/{invite_code}", json=join_data)
            
            if join_response.status_code not in [200, 201, 204]:
                return False, f"Failed to join server: {join_response.status_code}"
        
        time.sleep(2)
        
        # Update server nickname if enabled
        if config.get('change_server_nick', True) and guild_id:
            nick_data = {"nick": config.get('nickname', '.gg/axo')}
            nick_response = client.patch(f"https://discord.com/api/v9/guilds/{guild_id}/members/@me", json=nick_data)
            if nick_response.status_code == 200:
                logging.info("Server nickname updated")
        
        # Get premium subscriptions
        premium_response = client.get("https://discord.com/api/v9/users/@me/billing/subscriptions")
        if premium_response.status_code != 200:
            return False, "No premium subscription found"
        
        subscriptions = premium_response.json()
        if not subscriptions:
            return False, "No active subscriptions"
        
        # Use first subscription for boosting
        subscription_id = subscriptions[0]['id']
        
        # Boost server
        boost_data = {
            "user_premium_guild_subscription_slot_ids": [subscription_id]
        }
        
        boost_response = client.put(
            f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
            json=boost_data
        )
        
        if boost_response.status_code in [200, 201]:
            return True, "Boost successful"
        else:
            return False, f"Boost failed: {boost_response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        try:
            client.close()
        except:
            pass

def thread_boost(task_id, invite, amount, months, nickname, bio):
    """Main boosting function with fingerprint rotation"""
    try:
        boost_tasks[task_id]['status'] = 'running'
        boost_tasks[task_id]['start_time'] = time.time()
        boost_tasks[task_id]['successful_boosts'] = 0
        boost_tasks[task_id]['failed_boosts'] = 0
        
        invite_code = getinviteCode(invite)
        tokens = load_tokens(months)
        
        if not tokens:
            boost_tasks[task_id]['status'] = 'error'
            boost_tasks[task_id]['message'] = f"No {months}-month tokens available"
            return
        
        boost_tasks[task_id]['total_tokens'] = len(tokens)
        boost_tasks[task_id]['available_boosts'] = len(tokens) * 2
        
        successful_boosts = 0
        
        for i in range(min(amount, len(tokens) * 2)):
            if boost_tasks[task_id]['status'] == 'cancelled':
                break
            
            fingerprint = get_random_fingerprint()
            token_index = i // 2
            token = tokens[token_index] if token_index < len(tokens) else None
            
            if not token:
                continue
                
            boost_tasks[task_id]['current_boost'] = i + 1
            boost_tasks[task_id]['current_token'] = f"Token {token_index + 1}"
            boost_tasks[task_id]['current_fingerprint'] = fingerprint['useragent'][:30] + "..."
            
            success, message = boost_server(token, invite_code, fingerprint, task_id, i + 1)
            
            if success:
                successful_boosts += 1
                boost_tasks[task_id]['successful_boosts'] = successful_boosts
                boost_tasks[task_id]['message'] = f"Boost {i+1}/{amount} successful"
            else:
                boost_tasks[task_id]['failed_boosts'] = i + 1 - successful_boosts
                boost_tasks[task_id]['message'] = f"Boost {i+1}/{amount} failed: {message}"
            
            delay = random.uniform(3, 8)
            time.sleep(delay)
            
            boost_tasks[task_id]['progress'] = i + 1
        
        boost_tasks[task_id]['status'] = 'completed'
        boost_tasks[task_id]['end_time'] = time.time()
        boost_tasks[task_id]['message'] = f"Completed {successful_boosts}/{amount} boosts successfully"
        
    except Exception as e:
        boost_tasks[task_id]['status'] = 'error'
        boost_tasks[task_id]['message'] = f"Unexpected error: {str(e)}"

def get_stock():
    """Get token stock information"""
    try:
        tokens_1m = len(open("input/1m_tokens.txt", "r").readlines())
    except:
        tokens_1m = 0
        os.makedirs("input", exist_ok=True)
        open("input/1m_tokens.txt", "a").close()
        
    try:
        tokens_3m = len(open("input/3m_tokens.txt", "r").readlines())
    except:
        tokens_3m = 0
        open("input/3m_tokens.txt", "a").close()
    
    return {
        '1m_tokens': tokens_1m,
        '1m_boosts': tokens_1m * 2,
        '3m_tokens': tokens_3m,
        '3m_boosts': tokens_3m * 2,
        'total_fingerprints': len(FINGERPRINTS),
        'capsolver_enabled': bool(config.get('capsolver_key')),
        'auto_bio': config.get('change_server_bio', True),
        'auto_nickname': config.get('change_server_nick', True)
    }

# HTML Template (same as before, but showing Capsolver status)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Discord Boosting Service</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #36393f; color: #dcddde; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2f3136; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .command-interface { background: #2f3136; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .command-input { display: flex; align-items: center; background: #40444b; border-radius: 8px; padding: 10px; }
        .slash { color: #7289da; font-size: 20px; margin-right: 8px; }
        .command-field { flex: 1; background: transparent; border: none; color: white; font-size: 16px; outline: none; }
        .suggestions { background: #40444b; border-radius: 8px; margin-top: 10px; padding: 10px; display: none; }
        .suggestion { padding: 8px 12px; cursor: pointer; border-radius: 4px; }
        .suggestion:hover { background: #484c52; }
        .command-card { background: #2f3136; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #7289da; }
        .response-card { background: #2f3136; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #43b581; }
        .error-card { background: #2f3136; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #f04747; }
        .task-card { background: #2f3136; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .status-running { color: #faa61a; }
        .status-completed { color: #43b581; }
        .status-error { color: #f04747; }
        .status-pending { color: #7289da; }
        .stock-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin: 15px 0; }
        .stock-item { background: #40444b; padding: 15px; border-radius: 8px; text-align: center; }
        .btn { background: #7289da; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #677bc4; }
        .btn-danger { background: #f04747; }
        .btn-danger:hover { background: #d84040; }
        .progress-bar { width: 100%; background: #40444b; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 20px; background: #43b581; transition: width 0.3s; }
        .task-details { background: #40444b; padding: 10px; border-radius: 5px; margin: 5px 0; }
        .fingerprint-info { font-size: 12px; color: #b9bbbe; }
        .config-badge { background: #7289da; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin: 0 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Advanced Discord Boosting Service</h1>
            <p>Advanced fingerprint rotation • Capsolver Integration • Auto Profile Setup</p>
        </div>

        <!-- Slash Command Interface -->
        <div class="command-interface">
            <div class="command-input">
                <span class="slash">/</span>
                <input type="text" class="command-field" id="commandInput" placeholder="Type a command..." autocomplete="off">
            </div>
            <div class="suggestions" id="suggestions">
                <div class="suggestion" onclick="useSuggestion('boost')">boost - Start boosting a server</div>
                <div class="suggestion" onclick="useSuggestion('stock')">stock - Check token inventory</div>
                <div class="suggestion" onclick="useSuggestion('tasks')">tasks - View active tasks</div>
                <div class="suggestion" onclick="useSuggestion('cancel')">cancel - Cancel a task</div>
                <div class="suggestion" onclick="useSuggestion('fingerprints')">fingerprints - Show available fingerprints</div>
                <div class="suggestion" onclick="useSuggestion('config')">config - Show current configuration</div>
                <div class="suggestion" onclick="useSuggestion('help')">help - Show all commands</div>
            </div>
        </div>

        <!-- Command Output Area -->
        <div id="commandOutput"></div>

        <!-- System Status -->
        <div class="task-card">
            <h3>📊 System Status</h3>
            <div class="stock-grid">
                <div class="stock-item">
                    <h4>1 Month Nitro</h4>
                    <p>Tokens: {{ stock.1m_tokens }}</p>
                    <p>Boosts: {{ stock.1m_boosts }}</p>
                </div>
                <div class="stock-item">
                    <h4>3 Month Nitro</h4>
                    <p>Tokens: {{ stock.3m_tokens }}</p>
                    <p>Boosts: {{ stock.3m_boosts }}</p>
                </div>
                <div class="stock-item">
                    <h4>Fingerprints</h4>
                    <p>Available: {{ stock.total_fingerprints }}</p>
                    <p>Status: 🟢 Active</p>
                </div>
                <div class="stock-item">
                    <h4>Capsolver</h4>
                    <p>Status: {{ '🟢 Enabled' if stock.capsolver_enabled else '🔴 Disabled' }}</p>
                    <p>Auto-Bio: {{ '✅' if stock.auto_bio else '❌' }}</p>
                    <p>Auto-Nick: {{ '✅' if stock.auto_nickname else '❌' }}</p>
                </div>
            </div>
        </div>

        <!-- Active Tasks -->
        <div class="task-card">
            <h3>🔄 Active Tasks</h3>
            <div id="tasksList">
                {% for task_id, task in tasks.items() %}
                <div class="command-card">
                    <strong>Task #{{ task_id }}</strong> | 
                    <span class="status-{{ task.status }}">{{ task.status.upper() }}</span>
                    <div class="task-details">
                        <p>Server: {{ task.invite }} | Progress: {{ task.progress }}/{{ task.amount }}</p>
                        <p>Successful: {{ task.successful_boosts }} | Failed: {{ task.failed_boosts }}</p>
                        {% if task.status == 'running' %}
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ (task.progress / task.amount * 100) | round }}%"></div>
                        </div>
                        <p class="fingerprint-info">Using: {{ task.current_fingerprint }}</p>
                        {% endif %}
                        <small>{{ task.message }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        const commandInput = document.getElementById('commandInput');
        const suggestions = document.getElementById('suggestions');
        const commandOutput = document.getElementById('commandOutput');

        // Command definitions
        const commands = {
            'boost': {
                description: 'Start boosting a server',
                usage: '/boost <invite> <amount> <months>',
                example: '/boost discord.gg/server 10 3',
                execute: (args) => executeBoost(args)
            },
            'stock': {
                description: 'Check token inventory',
                usage: '/stock',
                execute: () => executeStock()
            },
            'tasks': {
                description: 'View active tasks',
                usage: '/tasks',
                execute: () => executeTasks()
            },
            'cancel': {
                description: 'Cancel a task',
                usage: '/cancel <task_id>',
                example: '/cancel 1',
                execute: (args) => executeCancel(args)
            },
            'fingerprints': {
                description: 'Show available fingerprints',
                usage: '/fingerprints',
                execute: () => executeFingerprints()
            },
            'config': {
                description: 'Show current configuration',
                usage: '/config',
                execute: () => executeConfig()
            },
            'help': {
                description: 'Show all commands',
                usage: '/help',
                execute: () => executeHelp()
            }
        };

        // Event listeners
        commandInput.addEventListener('input', showSuggestions);
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });

        function showSuggestions() {
            const input = commandInput.value.toLowerCase();
            if (input.startsWith('/')) {
                suggestions.style.display = 'block';
            } else {
                suggestions.style.display = 'none';
            }
        }

        function useSuggestion(command) {
            commandInput.value = '/' + command;
            suggestions.style.display = 'none';
            commandInput.focus();
        }

        function executeCommand() {
            const input = commandInput.value.trim();
            if (!input.startsWith('/')) {
                showResponse('error', 'Commands must start with /');
                return;
            }

            const parts = input.slice(1).split(' ');
            const commandName = parts[0].toLowerCase();
            const args = parts.slice(1);

            if (commands[commandName]) {
                commands[commandName].execute(args);
            } else {
                showResponse('error', `Unknown command: ${commandName}. Type /help for available commands.`);
            }

            commandInput.value = '';
        }

        function executeBoost(args) {
            if (args.length < 3) {
                showResponse('error', 'Usage: /boost <invite> <amount> <months>');
                return;
            }

            const [invite, amount, months] = args;
            
            fetch('/api/boost', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invite, amount: parseInt(amount), months: parseInt(months) })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showResponse('success', 
                        `🚀 Boost started with advanced features! 
                         Task ID: ${data.task_id}
                         Features: Capsolver • Fingerprint Rotation • Auto Profile
                         Estimated time: ${Math.ceil(amount * 5 / 60)} minutes`);
                    refreshTasks();
                } else {
                    showResponse('error', data.error || 'Failed to start boost');
                }
            })
            .catch(error => {
                showResponse('error', 'Network error: ' + error);
            });
        }

        function executeStock() {
            fetch('/api/stock')
                .then(response => response.json())
                .then(data => {
                    const stockInfo = `
                        <div class="stock-grid">
                            <div class="stock-item">
                                <h4>1 Month Nitro</h4>
                                <p>Tokens: ${data['1m_tokens']}</p>
                                <p>Boosts: ${data['1m_boosts']}</p>
                            </div>
                            <div class="stock-item">
                                <h4>3 Month Nitro</h4>
                                <p>Tokens: ${data['3m_tokens']}</p>
                                <p>Boosts: ${data['3m_boosts']}</p>
                            </div>
                            <div class="stock-item">
                                <h4>Fingerprints</h4>
                                <p>Available: ${data['total_fingerprints']}</p>
                                <p>Status: 🟢 Active</p>
                            </div>
                            <div class="stock-item">
                                <h4>Capsolver</h4>
                                <p>Status: ${data.capsolver_enabled ? '🟢 Enabled' : '🔴 Disabled'}</p>
                                <p>Auto-Bio: ${data.auto_bio ? '✅' : '❌'}</p>
                                <p>Auto-Nick: ${data.auto_nickname ? '✅' : '❌'}</p>
                            </div>
                        </div>
                    `;
                    showResponse('info', `📊 System Status${stockInfo}`);
                });
        }

        function executeConfig() {
            fetch('/api/config')
                .then(response => response.json())
                .then(data => {
                    let configHtml = '<h4>Current Configuration:</h4>';
                    for (const [key, value] of Object.entries(data.config)) {
                        if (key === 'capsolver_key' && value) {
                            configHtml += `<div class="command-card"><strong>${key}:</strong> ${value.substring(0, 10)}...${value.substring(value.length-10)}</div>`;
                        } else {
                            configHtml += `<div class="command-card"><strong>${key}:</strong> ${value}</div>`;
                        }
                    }
                    showResponse('info', configHtml);
                });
        }

        function executeTasks() {
            fetch('/api/tasks')
                .then(response => response.json())
                .then(data => {
                    let tasksHtml = '';
                    for (const [taskId, task] of Object.entries(data)) {
                        const progressPercent = Math.round((task.progress / task.amount) * 100);
                        tasksHtml += `
                            <div class="command-card">
                                <strong>Task #${taskId}</strong> | 
                                <span class="status-${task.status}">${task.status.toUpperCase()}</span>
                                <div class="task-details">
                                    <p>Server: ${task.invite} | Progress: ${task.progress}/${task.amount}</p>
                                    <p>Successful: ${task.successful_boosts || 0} | Failed: ${task.failed_boosts || 0}</p>
                                    ${task.status === 'running' ? `
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: ${progressPercent}%"></div>
                                    </div>
                                    <p class="fingerprint-info">Using: ${task.current_fingerprint || 'Rotating...'}</p>
                                    ` : ''}
                                    <small>${task.message}</small>
                                </div>
                            </div>
                        `;
                    }
                    showResponse('info', `🔄 Active Tasks${tasksHtml ? tasksHtml : '<p>No active tasks</p>'}`);
                });
        }

        function executeFingerprints() {
            fetch('/api/fingerprints')
                .then(response => response.json())
                .then(data => {
                    let fingerprintsHtml = '<h4>Available Fingerprints:</h4>';
                    data.fingerprints.forEach((fp, index) => {
                        fingerprintsHtml += `
                            <div class="command-card">
                                <strong>Fingerprint #${index + 1}</strong>
                                <p><small>User Agent: ${fp.useragent}</small></p>
                                <p><small>JA3: ${fp.ja3.substring(0, 50)}...</small></p>
                            </div>
                        `;
                    });
                    showResponse('info', fingerprintsHtml);
                });
        }

        function executeCancel(args) {
            if (args.length < 1) {
                showResponse('error', 'Usage: /cancel <task_id>');
                return;
            }

            const taskId = args[0];
            fetch(`/api/cancel/${taskId}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showResponse('success', '✅ Task cancelled successfully');
                        refreshTasks();
                    } else {
                        showResponse('error', data.error || 'Failed to cancel task');
                    }
                });
        }

        function executeHelp() {
            let helpText = '<h4>Available Commands:</h4>';
            for (const [cmd, info] of Object.entries(commands)) {
                helpText += `
                    <div class="command-card">
                        <strong>/${cmd}</strong> - ${info.description}
                        <p><small>Usage: ${info.usage}</small></p>
                        ${info.example ? `<p><small>Example: ${info.example}</small></p>` : ''}
                    </div>
                `;
            }
            showResponse('info', helpText);
        }

        function showResponse(type, content) {
            const responseDiv = document.createElement('div');
            responseDiv.className = type === 'error' ? 'error-card' : 'response-card';
            responseDiv.innerHTML = content;
            commandOutput.prepend(responseDiv);
        }

        function refreshTasks() {
            setTimeout(() => location.reload(), 2000);
        }

        // Auto-focus command input
        commandInput.focus();
        
        // Auto-refresh tasks every 5 seconds
        setInterval(() => {
            if (Object.keys({{ tasks|tojson }}).length > 0) {
                location.reload();
            }
        }, 5000);
    </script>
</body>
</html>
'''

# API Routes
@app.route('/')
def home():
    """Main web interface with slash commands"""
    stock = get_stock()
    return render_template_string(HTML_TEMPLATE, stock=stock, tasks=boost_tasks)

@app.route('/api/boost', methods=['POST'])
def api_boost():
    """API endpoint for boost command"""
    global task_id_counter
    
    try:
        data = request.get_json()
        invite = data.get('invite')
        amount = int(data.get('amount', 1))
        months = int(data.get('months', 1))
        
        if not invite:
            return jsonify({"success": False, "error": "Invite is required"}), 400
        
        invite_code = getinviteCode(invite)
        task_id = task_id_counter
        task_id_counter += 1
        
        # Create task
        boost_tasks[task_id] = {
            'invite': invite_code,
            'amount': amount,
            'months': months,
            'progress': 0,
            'completed': 0,
            'status': 'pending',
            'message': 'Task created with Capsolver integration',
            'start_time': None,
            'end_time': None,
            'successful_boosts': 0,
            'failed_boosts': 0,
            'current_fingerprint': 'Rotating...',
            'current_token': 'Loading...'
        }
        
        # Start boosting in background thread
        thread = threading.Thread(
            target=thread_boost,
            args=(task_id, invite_code, amount, months, config['nickname'], config["bio"])
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Advanced boost started for {invite_code}",
            "features": {
                "capsolver": bool(config.get('capsolver_key')),
                "fingerprints": len(FINGERPRINTS),
                "auto_bio": config.get('change_server_bio', True),
                "auto_nickname": config.get('change_server_nick', True)
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stock')
def api_stock():
    """API endpoint for stock command"""
    return jsonify(get_stock())

@app.route('/api/tasks')
def api_tasks():
    """API endpoint for tasks command"""
    return jsonify(boost_tasks)

@app.route('/api/fingerprints')
def api_fingerprints():
    """API endpoint for fingerprints command"""
    return jsonify({"fingerprints": FINGERPRINTS})

@app.route('/api/config')
def api_config():
    """API endpoint for config command"""
    return jsonify({"config": config})

@app.route('/api/cancel/<int:task_id>', methods=['POST'])
def api_cancel(task_id):
    """API endpoint for cancel command"""
    if task_id in boost_tasks:
        boost_tasks[task_id]['status'] = 'cancelled'
        boost_tasks[task_id]['message'] = 'Task cancelled by user'
        return jsonify({"success": True, "message": "Task cancelled"})
    return jsonify({"success": False, "error": "Task not found"}), 404

@app.route('/api/help')
def api_help():
    """API endpoint for help command"""
    commands_info = {
        'boost': 'Start boosting a server - /boost <invite> <amount> <months>',
        'stock': 'Check token inventory - /stock',
        'tasks': 'View active tasks - /tasks',
        'cancel': 'Cancel a task - /cancel <task_id>',
        'fingerprints': 'Show available fingerprints - /fingerprints',
        'config': 'Show current configuration - /config',
        'help': 'Show this help message - /help'
    }
    return jsonify(commands_info)

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy", 
        "timestamp": time.time(),
        "fingerprints_available": len(FINGERPRINTS),
        "capsolver_enabled": bool(config.get('capsolver_key')),
        "active_tasks": len([t for t in boost_tasks.values() if t['status'] == 'running'])
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", config.get('port', 5000)))
    app.run(host=config.get('host', '0.0.0.0'), port=port, debug=False)
