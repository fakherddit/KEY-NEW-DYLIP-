<?php
// telegram_bot_enhanced.php - Full Featured Bot with Server Controls
// Rename this to telegram_bot.php after reviewing

$telegram_token = "8216359066:AAEt2GFGgTBp3hh_znnJagH3h1nN5A_XQf0";
$admin_chat_id = 7210704553;

$update = json_decode(file_get_contents('php://input'), true);
if (!$update) exit();

$message = $update['message'] ?? null;
$callback_query = $update['callback_query'] ?? null;

// Handle callbacks
if ($callback_query) {
    $chat_id = $callback_query['message']['chat']['id'];
    $data = $callback_query['data'];
    
    if (strpos($data, 'gen_') === 0) {
        list($action, $count, $days) = explode('_', $data);
        generateKeys($chat_id, $count, $days, 'standard', $telegram_token, $pdo);
    } elseif (strpos($data, 'global_') === 0) {
        list($action, $type) = explode('_', $data);
        generateGlobalKey($chat_id, $type, $telegram_token, $pdo);
    } elseif ($data === 'server_toggle') {
        toggleServer($chat_id, $telegram_token, $pdo);
    } elseif ($data === 'validation_toggle') {
        toggleValidation($chat_id, $telegram_token, $pdo);
    } elseif ($data === 'creation_toggle') {
        toggleCreation($chat_id, $telegram_token, $pdo);
    } elseif ($data === 'delete_expired') {
        deleteExpiredKeys($chat_id, $telegram_token, $pdo);
    }
    
    answerCallbackQuery($callback_query['id'], $telegram_token);
    exit();
}

// Handle messages
if ($message) {
    $chat_id = $message['chat']['id'];
    $text = $message['text'] ?? '';
    $user_id = $message['from']['id'];
    
    if ($user_id != $admin_chat_id) {
        sendMessage($chat_id, "⛔ Unauthorized", $telegram_token);
        exit();
    }
    
    switch ($text) {
        case '/start': sendMainMenu($chat_id, $telegram_token); break;
        case '/generate': sendGenerateMenu($chat_id, $telegram_token); break;
        case '/global': sendGlobalKeyMenu($chat_id, $telegram_token); break;
        case '/control': sendControlMenu($chat_id, $telegram_token, $pdo); break;
        case '/stats': sendStats($chat_id, $telegram_token, $pdo); break;
        case '/list': listActiveKeys($chat_id, $telegram_token, $pdo); break;
        default:
            if (preg_match('/^[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$/i', $text)) {
                lookupKey($chat_id, $text, $telegram_token, $pdo);
            }
    }
}

function sendMessage($chat_id, $text, $token, $reply_markup = null) {
    $url = "https://api.telegram.org/bot{$token}/sendMessage";
    $data = ['chat_id' => $chat_id, 'text' => $text, 'parse_mode' => 'HTML'];
    if ($reply_markup) $data['reply_markup'] = json_encode($reply_markup);
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_exec($ch);
    curl_close($ch);
}

function sendMainMenu($chat_id, $token) {
    $text = "🎮 <b>ST FAMILY License Bot</b>\n\n";
    $text .= "/generate - Standard keys\n";
    $text .= "/global - Global keys (unlimited users)\n";
    $text .= "/control - Server controls\n";
    $text .= "/stats - Statistics\n";
    $text .= "/list - List keys";
    sendMessage($chat_id, $text, $token);
}

function sendGenerateMenu($chat_id, $token) {
    $keyboard = ['inline_keyboard' => [
        [['text' => '1 Key - 7 Days', 'callback_data' => 'gen_1_7'], ['text' => '1 Key - 30 Days', 'callback_data' => 'gen_1_30']],
        [['text' => '5 Keys - 30 Days', 'callback_data' => 'gen_5_30'], ['text' => '10 Keys - 30 Days', 'callback_data' => 'gen_10_30']],
        [['text' => '1 Key - Lifetime', 'callback_data' => 'gen_1_3650'], ['text' => '5 Keys - Lifetime', 'callback_data' => 'gen_5_3650']]
    ]];
    sendMessage($chat_id, "🔑 Generate Standard Keys", $token, $keyboard);
}

function sendGlobalKeyMenu($chat_id, $token) {
    $keyboard = ['inline_keyboard' => [
        [['text' => '🌍 Global Day', 'callback_data' => 'global_day']],
        [['text' => '🌍 Global Week', 'callback_data' => 'global_week']],
        [['text' => '🌍 Global Month', 'callback_data' => 'global_month']]
    ]];
    sendMessage($chat_id, "🌐 Global Keys (Unlimited Users)", $token, $keyboard);
}

function sendControlMenu($chat_id, $token, $pdo) {
    $server = getStatus($pdo, 'server_enabled');
    $validation = getStatus($pdo, 'key_validation_enabled');
    $creation = getStatus($pdo, 'key_creation_enabled');
    
    $text = "⚙️ <b>Control Panel</b>\n\n";
    $text .= ($server ? '🟢' : '🔴') . " Server\n";
    $text .= ($validation ? '🟢' : '🔴') . " Validation\n";
    $text .= ($creation ? '🟢' : '🔴') . " Creation";
    
    $keyboard = ['inline_keyboard' => [
        [['text' => ($server ? '🔴 Stop Server' : '🟢 Start Server'), 'callback_data' => 'server_toggle']],
        [['text' => ($validation ? '🔴 Disable Validation' : '🟢 Enable Validation'), 'callback_data' => 'validation_toggle']],
        [['text' => ($creation ? '🔴 Disable Creation' : '🟢 Enable Creation'), 'callback_data' => 'creation_toggle']],
        [['text' => '🗑️ Delete Expired', 'callback_data' => 'delete_expired']]
    ]];
    
    sendMessage($chat_id, $text, $token, $keyboard);
}

function generateKeys($chat_id, $count, $days, $type, $token, $pdo) {
    if (!getStatus($pdo, 'key_creation_enabled')) {
        sendMessage($chat_id, "❌ Creation disabled", $token);
        return;
    }
    
    $keys = [];
    for ($i = 0; $i < $count; $i++) {
        $key = sprintf("%04X-%04X-%04X-%04X", mt_rand(0, 0xFFFF), mt_rand(0, 0xFFFF), mt_rand(0, 0xFFFF), mt_rand(0, 0xFFFF));
        $expiry = date('Y-m-d H:i:s', strtotime("+$days days"));
        $stmt = $pdo->prepare("INSERT INTO licenses (license_key, expiry_date, key_type) VALUES (?, ?, ?)");
        if ($stmt->execute([$key, $expiry, $type])) $keys[] = $key;
    }
    
    $duration = $days >= 3650 ? 'Lifetime' : "$days Days";
    $text = "✅ Generated {$count} Key(s) - {$duration}\n\n<code>" . implode("\n", $keys) . "</code>";
    sendMessage($chat_id, $text, $token);
}

function generateGlobalKey($chat_id, $type, $token, $pdo) {
    if (!getStatus($pdo, 'key_creation_enabled')) {
        sendMessage($chat_id, "❌ Creation disabled", $token);
        return;
    }
    
    $days = ['day' => 1, 'week' => 7, 'month' => 30][$type];
    $key = sprintf("GLB-%04X-%04X-%04X", mt_rand(0, 0xFFFF), mt_rand(0, 0xFFFF), mt_rand(0, 0xFFFF));
    $expiry = date('Y-m-d H:i:s', strtotime("+$days days"));
    
    $stmt = $pdo->prepare("INSERT INTO licenses (license_key, expiry_date, key_type) VALUES (?, ?, ?)");
    if ($stmt->execute([$key, $expiry, "global_$type"])) {
        $text = "🌐 Global {$type} Key\n\n<code>{$key}</code>\n\n✅ Unlimited users\n⏰ {$days} day(s)";
        sendMessage($chat_id, $text, $token);
    }
}

function toggleServer($chat_id, $token, $pdo) {
    toggleStatus($pdo, 'server_enabled', $chat_id, $token, 'Server');
}

function toggleValidation($chat_id, $token, $pdo) {
    toggleStatus($pdo, 'key_validation_enabled', $chat_id, $token, 'Validation');
}

function toggleCreation($chat_id, $token, $pdo) {
    toggleStatus($pdo, 'key_creation_enabled', $chat_id, $token, 'Creation');
}

function toggleStatus($pdo, $key, $chat_id, $token, $name) {
    $current = getStatus($pdo, $key);
    $new = $current ? '0' : '1';
    $pdo->prepare("UPDATE server_settings SET value = ? WHERE key = ?")->execute([$new, $key]);
    sendMessage($chat_id, ($new === '1' ? '🟢' : '🔴') . " $name " . ($new === '1' ? 'enabled' : 'disabled'), $token);
}

function deleteExpiredKeys($chat_id, $token, $pdo) {
    $stmt = $pdo->prepare("DELETE FROM licenses WHERE expiry_date < NOW()");
    $stmt->execute();
    sendMessage($chat_id, "🗑️ Deleted " . $stmt->rowCount() . " expired keys", $token);
}

function sendStats($chat_id, $token, $pdo) {
    $total = $pdo->query("SELECT COUNT(*) FROM licenses")->fetchColumn();
    $active = $pdo->query("SELECT COUNT(*) FROM licenses WHERE status = 'active' AND expiry_date > NOW()")->fetchColumn();
    $used = $pdo->query("SELECT COUNT(*) FROM licenses WHERE hwid IS NOT NULL")->fetchColumn();
    $global = $pdo->query("SELECT COUNT(*) FROM licenses WHERE key_type LIKE 'global_%'")->fetchColumn();
    
    $text = "📊 <b>Statistics</b>\n\n📦 Total: {$total}\n✅ Active: {$active}\n🔗 Used: {$used}\n🌐 Global: {$global}";
    sendMessage($chat_id, $text, $token);
}

function listActiveKeys($chat_id, $token, $pdo) {
    $stmt = $pdo->query("SELECT license_key, hwid, expiry_date, key_type FROM licenses WHERE status = 'active' AND expiry_date > NOW() ORDER BY created_at DESC LIMIT 20");
    $text = "🔑 Active Keys (Last 20)\n\n";
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $is_global = strpos($row['key_type'], 'global_') === 0;
        $status = $is_global ? '🌐 Global' : ($row['hwid'] ? '🔗 Bound' : '⚪ Available');
        $text .= "<code>{$row['license_key']}</code> {$status}\n";
    }
    sendMessage($chat_id, $text, $token);
}

function lookupKey($chat_id, $key, $token, $pdo) {
    $stmt = $pdo->prepare("SELECT * FROM licenses WHERE license_key = ?");
    $stmt->execute([$key]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($row) {
        $is_global = strpos($row['key_type'], 'global_') === 0;
        $text = "🔍 Key: <code>{$key}</code>\n";
        $text .= "Type: " . ($is_global ? "🌐 Global" : "Standard") . "\n";
        $text .= "Status: " . ($row['status'] == 'active' ? '✅' : '❌') . " {$row['status']}\n";
        $text .= "Expires: " . date('Y-m-d H:i', strtotime($row['expiry_date']));
        sendMessage($chat_id, $text, $token);
    }
}

function getStatus($pdo, $key) {
    $stmt = $pdo->query("SELECT value FROM server_settings WHERE key = '$key'");
    return $stmt ? $stmt->fetchColumn() === '1' : true;
}

function answerCallbackQuery($callback_id, $token) {
    $ch = curl_init("https://api.telegram.org/bot{$token}/answerCallbackQuery");
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, ['callback_query_id' => $callback_id]);
    curl_exec($ch);
    curl_close($ch);
}
?>
