from flask import Flask, request, jsonify, render_template_string
import threading
import time
import json
import os
import logging
from colorama import init, Fore, Style
import fade

# Initialize colorama
init()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load configuration
try:
    config = json.load(open("config.json", encoding="utf-8"))
except FileNotFoundError:
    config = {
        "nickname": "Boosted User",
        "bio": "Boosting your server!",
        "port": 5000,
        "host": "0.0.0.0"
    }
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

# Global variables
boost_tasks = {}
task_id_counter = 0

class BoostVariables:
    def __init__(self):
        self.boosts_done = 0

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

def thread_boost(task_id, invite, amount, months, nickname, bio):
    """Mock boosting function - replace with your actual implementation"""
    try:
        boost_tasks[task_id]['status'] = 'running'
        boost_tasks[task_id]['start_time'] = time.time()
        
        # Simulate boosting process
        for i in range(amount):
            if boost_tasks[task_id]['status'] == 'cancelled':
                break
                
            boost_tasks[task_id]['progress'] = i + 1
            boost_tasks[task_id]['completed'] += 1
            
            # Simulate work
            time.sleep(2)
            
        boost_tasks[task_id]['status'] = 'completed'
        boost_tasks[task_id]['end_time'] = time.time()
        boost_tasks[task_id]['message'] = f"Successfully boosted {invite} {amount} times"
        
    except Exception as e:
        boost_tasks[task_id]['status'] = 'error'
        boost_tasks[task_id]['message'] = f"Error: {str(e)}"

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
        '3m_boosts': tokens_3m * 2
    }

# HTML Template with Slash Command Interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Discord Boosting Service - Slash Commands</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #36393f; color: #dcddde; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
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
        .task-card { background: #2f3136; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .status-running { color: #faa61a; }
        .status-completed { color: #43b581; }
        .status-error { color: #f04747; }
        .stock-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }
        .stock-item { background: #40444b; padding: 15px; border-radius: 8px; text-align: center; }
        .btn { background: #7289da; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #677bc4; }
        .btn-danger { background: #f04747; }
        .btn-danger:hover { background: #d84040; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Discord Boosting Service</h1>
            <p>Use slash commands to control the boosting service</p>
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
                <div class="suggestion" onclick="useSuggestion('help')">help - Show all commands</div>
            </div>
        </div>

        <!-- Command Output Area -->
        <div id="commandOutput"></div>

        <!-- Active Tasks -->
        <div class="task-card">
            <h3>🔄 Active Tasks</h3>
            <div id="tasksList">
                {% for task_id, task in tasks.items() %}
                <div class="command-card">
                    <strong>Task #{{ task_id }}</strong> | 
                    <span class="status-{{ task.status }}">{{ task.status.upper() }}</span>
                    <p>Server: {{ task.invite }} | Progress: {{ task.progress }}/{{ task.amount }}</p>
                    <small>{{ task.message }}</small>
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
                    showResponse('success', `🚀 Boost started! Task ID: ${data.task_id}`);
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
                        </div>
                    `;
                    showResponse('info', `📊 Stock Information${stockInfo}`);
                });
        }

        function executeTasks() {
            fetch('/api/tasks')
                .then(response => response.json())
                .then(data => {
                    let tasksHtml = '';
                    for (const [taskId, task] of Object.entries(data)) {
                        tasksHtml += `
                            <div class="command-card">
                                <strong>Task #${taskId}</strong> | 
                                <span class="status-${task.status}">${task.status.toUpperCase()}</span>
                                <p>Server: ${task.invite} | Progress: ${task.progress}/${task.amount}</p>
                                <small>${task.message}</small>
                            </div>
                        `;
                    }
                    showResponse('info', `🔄 Active Tasks${tasksHtml ? tasksHtml : '<p>No active tasks</p>'}`);
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
            responseDiv.className = `response-card`;
            responseDiv.innerHTML = content;
            commandOutput.prepend(responseDiv);
        }

        function refreshTasks() {
            // Tasks are auto-refreshed via the template
            setTimeout(() => location.reload(), 1000);
        }

        // Auto-focus command input
        commandInput.focus();
    </script>
</body>
</html>
'''

# API Routes for Slash Commands
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
            'message': 'Task created via slash command',
            'start_time': None,
            'end_time': None
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
            "message": f"Boost started for {invite_code}",
            "command_response": f"🚀 Starting {amount} boosts for {invite_code} ({months} months)"
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

@app.route('/api/cancel/<int:task_id>', methods=['POST'])
def api_cancel(task_id):
    """API endpoint for cancel command"""
    if task_id in boost_tasks:
        boost_tasks[task_id]['status'] = 'cancelled'
        boost_tasks[task_id]['message'] = 'Task cancelled via slash command'
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
        'help': 'Show this help message - /help'
    }
    return jsonify(commands_info)

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", config.get('port', 5000)))
    app.run(host=config.get('host', '0.0.0.0'), port=port, debug=False)
