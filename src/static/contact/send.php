<?php
/**
 * ReNEW. お問い合わせフォーム送信処理
 * 通知メール（ReNEW.宛）と自動返信メール（お客様宛）を送り、送信完了ページへ移動する。
 */
declare(strict_types=1);

mb_language('Japanese');
mb_internal_encoding('UTF-8');

$config = require __DIR__ . '/config.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: ./', true, 303);
    exit;
}

/** 入力値を取り出し、前後の空白と制御文字を取り除く */
function field(string $key, int $max, bool $multiline = false): string
{
    $v = isset($_POST[$key]) && is_string($_POST[$key]) ? $_POST[$key] : '';
    $v = $multiline
        ? preg_replace('/[^\P{C}\n\t]/u', '', str_replace(["\r\n", "\r"], "\n", $v))
        : preg_replace('/\p{C}/u', '', $v);
    return mb_substr(trim((string)$v), 0, $max);
}

function fail(string $message): void
{
    http_response_code(400);
    $m = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');
    echo <<<HTML
<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>送信できませんでした｜ReNEW.</title>
<link rel="stylesheet" href="../assets/css/style.css"></head>
<body><main class="sec message"><div class="container">
<h1 class="label">送信できませんでした</h1><p>{$m}</p>
<p><a href="javascript:history.back()">入力画面に戻る</a></p>
</div></main></body></html>
HTML;
    exit;
}

// スパム対策：ハニーポット・送信までの時間
if (field('website', 200) !== '') {
    header('Location: thanks/', true, 303); // ボットには成功したように見せる
    exit;
}
$ts = (int)field('ts', 20);
if ($ts > 0 && time() - $ts < 3) {
    fail('送信までの時間が短すぎます。お手数ですが、もう一度お試しください。');
}

// Cloudflare Turnstile（設定時のみ）
if ($config['turnstile_secret'] !== '') {
    $ctx = stream_context_create(['http' => [
        'method'  => 'POST',
        'header'  => 'Content-Type: application/x-www-form-urlencoded',
        'content' => http_build_query([
            'secret'   => $config['turnstile_secret'],
            'response' => field('cf-turnstile-response', 2048),
            'remoteip' => $_SERVER['REMOTE_ADDR'] ?? '',
        ]),
        'timeout' => 10,
    ]]);
    $res = json_decode((string)@file_get_contents('https://challenges.cloudflare.com/turnstile/v0/siteverify', false, $ctx), true);
    if (empty($res['success'])) {
        fail('送信の確認ができませんでした。お手数ですが、もう一度お試しください。');
    }
}

$types = ['サブスク', 'フル施工', '個別メニュー', '施工事例を見て', 'その他'];
$data = [
    'type'  => field('type', 20),
    'name'  => field('name', 50),
    'kana'  => field('kana', 50),
    'tel'   => field('tel', 20),
    'email' => field('email', 100),
    'car'   => field('car', 100),
    'when'  => field('when', 100),
    'area'  => field('area', 50),
    'body'  => field('body', 3000, true),
];

$errors = [];
if (!in_array($data['type'], $types, true)) $errors[] = 'お問い合わせ項目を選択してください。';
if ($data['name'] === '') $errors[] = 'お名前を入力してください。';
if ($data['kana'] === '') $errors[] = 'フリガナを入力してください。';
if (!preg_match('/^[0-9０-９\-－ ]{10,20}$/u', $data['tel'])) $errors[] = '電話番号を正しく入力してください。';
if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL)) $errors[] = 'メールアドレスを正しく入力してください。';
if ($data['body'] === '') $errors[] = 'お問い合わせ内容を入力してください。';
if (($_POST['agree'] ?? '') !== '1') $errors[] = 'プライバシーポリシーへの同意が必要です。';
if ($errors) {
    fail(implode(' ', $errors));
}

$labels = [
    'type' => 'お問い合わせ項目', 'name' => 'お名前', 'kana' => 'フリガナ', 'tel' => '電話番号',
    'email' => 'メールアドレス', 'car' => '車種・年式・色', 'when' => 'ご希望の時期', 'area' => 'お住まいの地域',
    'body' => 'お問い合わせ内容',
];
$summary = '';
foreach ($labels as $k => $label) {
    $summary .= "■{$label}\n" . ($data[$k] !== '' ? $data[$k] : '（未入力）') . "\n\n";
}

$from = mb_encode_mimeheader($config['from_name']) . " <{$config['from']}>";
$sent = date('Y-m-d H:i');

// 通知メール（ReNEW.宛）。返信するとお客様に届くよう Reply-To を設定
$notifyBody = "ホームページからお問い合わせがありました。\n\n{$summary}"
    . "----\n送信日時：{$sent}\n送信元IP：" . ($_SERVER['REMOTE_ADDR'] ?? '') . "\n";
$ok = mb_send_mail(
    $config['to'],
    "【HP】お問い合わせ（{$data['type']}）{$data['name']} 様",
    $notifyBody,
    "From: {$from}\r\nReply-To: {$data['email']}",
    "-f{$config['from']}"
);
if (!$ok) {
    fail('システムの都合で送信できませんでした。お手数ですが、LINEまたはInstagramのDMからご連絡ください。');
}

// 自動返信メール（お客様宛）
$replyBody = "{$data['name']} 様\n\n"
    . "このたびは ReNEW. にお問い合わせいただき、ありがとうございます。\n"
    . "以下の内容で受け付けました。内容を確認のうえ、ReNEW.よりご連絡いたします。\n\n"
    . $summary
    . "※このメールは送信専用アドレスから自動でお送りしています。\n"
    . "※お心当たりのない場合は、お手数ですが本メールを破棄してください。\n\n"
    . "────────────────\n"
    . "ReNEW.（SOUKI -創綺- 車の美容院）\n"
    . "岡山県和気町\n"
    . "{$config['site_url']}/\n"
    . "────────────────\n";
mb_send_mail(
    $data['email'],
    '【ReNEW.】お問い合わせを受け付けました',
    $replyBody,
    "From: {$from}",
    "-f{$config['from']}"
);

header('Location: thanks/', true, 303);
exit;
