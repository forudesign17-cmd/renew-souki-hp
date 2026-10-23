<?php
// お問い合わせフォームの設定（.htaccess でブラウザからの直接アクセスを禁止している）
return [
    // 通知を受け取るアドレス（TODO: 決定したら書き換える）
    'to'        => 'info@renew-souki.jp',
    // 送信元アドレス。SPF/DKIM を設定したサーバーのドメインのアドレスにする
    'from'      => 'no-reply@renew-souki.jp',
    'from_name' => 'ReNEW. 車の美容院',
    'site_url'  => 'https://renew-souki.jp',
    // Cloudflare Turnstile のシークレットキー。空なら検証しない（使う場合はフォームにウィジェットも追加する）
    'turnstile_secret' => '',
];
