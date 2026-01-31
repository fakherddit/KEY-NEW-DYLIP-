<?php
// telegram_bot.php - Enhanced Telegram Bot with Server Controls

$telegram_token = "8216359066:AAEt2GFGgTBp3hh_znnJagH3h1nN5A_XQf0";
$admin_chat_id = 7210704553; // Your Telegram user ID

if (!$telegram_token) {
    die(json_encode(['error' => 'Bot token not configured']));
}

// Get webhook update
$update = json_decode(file_get_contents('php://input'), true);

if (!$update) {
    exit();
}

$message = $update['message'] ?? null;
$callback_query = $update['callback_query'] ?? null;

// Handle callback queries (button presses)
if ($callback_query) {
    $chat_id = $callback_query['message']['chat']['id'];
    $data = $callback_query['data'];
    
    if (strpos($data, 'gen_') === 0) {
        list($action, $count, $days) = explode('_', $data);
        generateKeys($chat_id, $count, $days, $telegram_token, $conn);
    }
    
    answerCallbackQuery($callback_query['id'], $telegram_token);
    exit();
}

// Handle text messages
if ($message) {
    $chat_id = $message['chat']['id'];
    $text = $message['text'] ?? '';
    $user_id = $message['from']['id'];
    
    // Check if user is admin
    if ($user_id != $admin_chat_id) {
        sendMessage($chat_id, "⛔ Unauthorized access. This bot is for admins only.", $telegram_token);
        exit();
    }
    
    switch ($text) {
        case '/start':
            sendMainMenu($chat_id, $telegram_token);
            break;
            
        case '/generate':
            sendGenerateMenu($chat_id, $telegram_token);
            break;
            
        case '/stats':
            sendStats($chat_id, $telegram_token, $conn);
            break;
            
        case '/list':
            listActiveKeys($chat_id, $telegram_token, $conn);
            break;
            
        default:
            // Check if it's a key lookup
            if (preg_match('/^[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$/i', $text)) {
                lookupKey($chat_id, $text, $telegram_token, $conn);
            } else {
                sendMessage($chat_id, "❌ Unknown command. Use /start to see available commands.", $telegram_token);
            }
    }
}

// Functions
function sendMessage($chat_id, $text, $token, $reply_markup = null) {
    $url = "https://api.telegram.org/bot{$token}/sendMessage";
    $data = [
        'chat_id' => $chat_id,
        'text' => $text,
        'parse_mode' => 'HTML'
    ];
    if ($reply_markup) {
        $data['reply_markup'] = json_encode($reply_markup);
    }
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_exec($ch);
    curl_close($ch);
}

function sendMainMenu($chat_id, $token) {
    $text = "🎮 <b>ST FAMILY License Bot</b>\n\n";
    $text .= "Available commands:\n";
    $text .= "/generate - Generate new license keys\n";
    $text .= "/stats - View statistics\n";
    $text .= "/list - List active keys\n";
    $text .= "\nSend a key to lookup its details.";
    
    sendMessage($chat_id, $text, $token);
}

function sendGenerateMenu($chat_id, $token) {
    $text = "🔑 <b>Generate License Keys</b>\n\nSelect quantity and duration:";
    
    $keyboard = [
        'inline_keyboard' => [
            [
                ['text' => '1 Key - 7 Days', 'callback_data' => 'gen_1_7'],
                ['text' => '1 Key - 30 Days', 'callback_data' => 'gen_1_30']
            ],
            [
                ['text' => '5 Keys - 30 Days', 'callback_data' => 'gen_5_30'],
                ['text' => '10 Keys - 30 Days', 'callback_data' => 'gen_10_30']
            ],
            [
                ['text' => '1 Key - Lifetime', 'callback_data' => 'gen_1_3650'],
                ['text' => '5 Keys - Lifetime', 'callback_data' => 'gen_5_3650']
            ]
        ]
    ];
    
    sendMessage($chat_id, $text, $token, $keyboard);
}

function generateKeys($chat_id, $count, $days, $token, $conn) {
    $keys = [];
    
    for ($i = 0; $i < $count; $i++) {
        $key = sprintf(
            "%04X-%04X-%04X-%04X",
            mt_rand(0, 0xFFFF),
            mt_rand(0, 0xFFFF),
            mt_rand(0, 0xFFFF),
            mt_rand(0, 0xFFFF)
        );
        
        $expiry = date('Y-m-d H:i:s', strtotime("+$days days"));
        
        $stmt = $conn->prepare("INSERT INTO licenses (license_key, expiry_date, created_at) VALUES (?, ?, NOW())");
        $stmt->bind_param("ss", $key, $expiry);
        
        if ($stmt->execute()) {
            $keys[] = $key;
        }
        $stmt->close();
    }
    
    if (count($keys) > 0) {
        $duration_text = $days >= 3650 ? 'Lifetime' : "$days Days";
        $text = "✅ <b>Generated {$count} Key(s) - {$duration_text}</b>\n\n";
        $text .= "<code>" . implode("\n", $keys) . "</code>\n\n";
        $text .= "Expiry: " . date('Y-m-d', strtotime("+$days days"));
    } else {
        $text = "❌ Failed to generate keys";
    }
    
    sendMessage($chat_id, $text, $token);
}

function sendStats($chat_id, $token, $conn) {
    $total = $conn->query("SELECT COUNT(*) as count FROM licenses")->fetch_assoc()['count'];
    $active = $conn->query("SELECT COUNT(*) as count FROM licenses WHERE status = 'active' AND expiry_date > NOW()")->fetch_assoc()['count'];
    $used = $conn->query("SELECT COUNT(*) as count FROM licenses WHERE hwid IS NOT NULL AND hwid != ''")->fetch_assoc()['count'];
    $expired = $conn->query("SELECT COUNT(*) as count FROM licenses WHERE expiry_date <= NOW()")->fetch_assoc()['count'];
    
    $text = "📊 <b>License Statistics</b>\n\n";
    $text .= "Total Keys: {$total}\n";
    $text .= "✅ Active: {$active}\n";
    $text .= "🔗 Used: {$used}\n";
    $text .= "⏰ Expired: {$expired}\n";
    
    sendMessage($chat_id, $text, $token);
}

function listActiveKeys($chat_id, $token, $conn) {
    $result = $conn->query("SELECT license_key, hwid, expiry_date, created_at FROM licenses WHERE status = 'active' AND expiry_date > NOW() ORDER BY created_at DESC LIMIT 20");
    
    $text = "🔑 <b>Active License Keys (Last 20)</b>\n\n";
    
    while ($row = $result->fetch_assoc()) {
        $key = $row['license_key'];
        $hwid = $row['hwid'] ? '🔗 Bound' : '⚪ Available';
        $expiry = date('Y-m-d', strtotime($row['expiry_date']));
        $text .= "<code>{$key}</code> {$hwid}\nExpires: {$expiry}\n\n";
    }
    
    sendMessage($chat_id, $text, $token);
}

function lookupKey($chat_id, $key, $token, $conn) {
    $stmt = $conn->prepare("SELECT * FROM licenses WHERE license_key = ?");
    $stmt->bind_param("s", $key);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();
        $text = "🔍 <b>Key Details</b>\n\n";
        $text .= "Key: <code>{$row['license_key']}</code>\n";
        $text .= "Status: " . ($row['status'] == 'active' ? '✅ Active' : '❌ ' . ucfirst($row['status'])) . "\n";
        $text .= "HWID: " . ($row['hwid'] ?: '⚪ Not bound') . "\n";
        $text .= "Created: " . date('Y-m-d H:i', strtotime($row['created_at'])) . "\n";
        $text .= "Expires: " . date('Y-m-d H:i', strtotime($row['expiry_date'])) . "\n";
        $text .= "Last Used: " . ($row['last_used'] ? date('Y-m-d H:i', strtotime($row['last_used'])) : 'Never') . "\n";
    } else {
        $text = "❌ Key not found in database";
    }
    
    $stmt->close();
    sendMessage($chat_id, $text, $token);
}

function answerCallbackQuery($callback_id, $token) {
    $url = "https://api.telegram.org/bot{$token}/answerCallbackQuery";
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, ['callback_query_id' => $callback_id]);
    curl_exec($ch);
    curl_close($ch);
}
?>

