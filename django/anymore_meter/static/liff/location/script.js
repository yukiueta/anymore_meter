document.addEventListener('DOMContentLoaded', () => {
    // --- 設定 ---
    // Django側で定義したLIFF IDとAPIエンドポイントURLを取得
    // (HTML内に埋め込むか、別途設定ファイルから読み込む想定)
    // Djangoテンプレートから渡す場合は {{ settings.LIFF_ID }} のようにする
    const LIFF_ID = 'YOUR_LIFF_ID'; // ★ settings.py と同じLIFF IDに置き換える
    const API_ENDPOINT = '/api/line/record_action_location/'; // ★ Djangoで作成するAPIエンドポイントのパス

    // --- 要素取得 ---
    const sendLocationBtn = document.getElementById('sendLocationBtn');
    const statusMessage = document.getElementById('statusMessage');
    const errorMessage = document.getElementById('errorMessage');
    const debugInfo = document.getElementById('debugInfo'); // デバッグ用
    const actionDescription = document.getElementById('action-description');

    // --- グローバル変数 ---
    let urlParams = {}; // URLパラメータ保持用

    // --- 関数 ---
    /**
     * メッセージを表示する
     * @param {string} msg 表示するメッセージ
     * @param {string} type 'status', 'error', 'debug'
     */
    function showMessage(msg, type = 'status') {
        if (type === 'status') {
            statusMessage.textContent = msg;
            errorMessage.textContent = ''; // エラーメッセージはクリア
        } else if (type === 'error') {
            errorMessage.textContent = msg;
            // statusMessage.textContent = ''; // ステータスメッセージは維持しても良いかも
        } else if (type === 'debug') {
            debugInfo.innerHTML += `<br>${msg}`;
        }
    }

    /**
     * LIFF初期化処理
     */
    async function initializeLiff() {
        showMessage('LIFFを初期化中...');
        try {
            await liff.init({ liffId: LIFF_ID });
            showMessage('LIFFの初期化完了');
            if (!liff.isLoggedIn()) {
                showMessage('LINEにログインしていません。ログインしてください。', 'error');
                // 必要であれば liff.login() を呼び出す
                return;
            }
            // URLパラメータを取得
            const queryString = window.location.search;
            const params = new URLSearchParams(queryString);
            urlParams = {
                action_type: params.get('action_type'),
                customer_id: params.get('customer_id'),
                schedule_id: params.get('schedule_id'),
                token: params.get('token') // Djangoから渡されたトークン
            };

            // デバッグ用にパラメータ表示
            showMessage(`Params: ${JSON.stringify(urlParams)}`, 'debug');

            // アクションタイプに応じて説明文を変更
            const actionText = urlParams.action_type === 'entry' ? '入場' : '退場';
            actionDescription.textContent = `${actionText}記録のために現在地を送信します。`;
            sendLocationBtn.textContent = `現在地を取得して${actionText}記録`;


            // パラメータが不足している場合はエラー
            if (!urlParams.action_type || !urlParams.customer_id || !urlParams.schedule_id || !urlParams.token) {
                 showMessage('必要な情報が不足しています。前の画面からやり直してください。', 'error');
                 sendLocationBtn.disabled = true;
                 return;
            }

            sendLocationBtn.disabled = false; // 初期化成功したらボタンを有効化

        } catch (err) {
            showMessage(`LIFF初期化エラー: ${err}`, 'error');
            sendLocationBtn.disabled = true;
        }
    }

    /**
     * 位置情報を取得してサーバーに送信
     */
    function getLocationAndSend() {
        sendLocationBtn.disabled = true; // 連続クリック防止
        showMessage('現在地を取得しています...');
        errorMessage.textContent = ''; // 前のエラーをクリア

        if (!navigator.geolocation) {
            showMessage('お使いのブラウザまたはデバイスは位置情報取得に対応していません。', 'error');
            sendLocationBtn.disabled = false;
            return;
        }

        navigator.geolocation.getCurrentPosition(
            // 取得成功時のコールバック
            async (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                const accuracy = position.coords.accuracy; // 精度(m)

                showMessage(`位置情報取得成功: 緯度 ${latitude}, 経度 ${longitude}, 精度 ${accuracy}m`);
                showMessage('サーバーに送信中...');

                // Django APIに送信するデータ
                const postData = {
                    ...urlParams, // action_type, customer_id, schedule_id, token
                    latitude: latitude,
                    longitude: longitude,
                    accuracy: accuracy
                };

                try {
                    // fetch APIでDjangoエンドポイントにPOST
                    const response = await fetch(API_ENDPOINT, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            // Django側でCSRF保護を使っている場合は 'X-CSRFToken' ヘッダーも必要
                            // 'X-CSRFToken': '{{ csrf_token }}' // Djangoテンプレートから渡す場合
                        },
                        body: JSON.stringify(postData)
                    });

                    const responseData = await response.json();

                    if (response.ok && responseData.status === 'success') {
                        showMessage(`記録成功: ${responseData.message}`);
                        // 成功したらLIFFウィンドウを閉じる
                        setTimeout(() => {
                            liff.closeWindow();
                        }, 2000); // 2秒後に閉じる
                    } else {
                        throw new Error(responseData.message || `サーバーエラー (Status: ${response.status})`);
                    }

                } catch (err) {
                    showMessage(`送信エラー: ${err.message}`, 'error');
                    sendLocationBtn.disabled = false; // エラー時はボタンを再度有効化
                }
            },
            // 取得失敗時のコールバック
            (error) => {
                let errorMsg = '位置情報の取得に失敗しました。';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMsg += ' 位置情報の利用が許可されていません。設定を確認してください。';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMsg += ' 位置情報を取得できませんでした。';
                        break;
                    case error.TIMEOUT:
                        errorMsg += ' 位置情報の取得がタイムアウトしました。';
                        break;
                    default:
                        errorMsg += ` (エラーコード: ${error.code})`;
                        break;
                }
                showMessage(errorMsg, 'error');
                sendLocationBtn.disabled = false; // エラー時はボタンを再度有効化
            },
            // オプション
            {
                enableHighAccuracy: true, // 高精度な測位を試みる (GPSなど)
                timeout: 10000, // 10秒でタイムアウト
                maximumAge: 0 // キャッシュされた位置情報を使わない
            }
        );
    }

    // --- イベントリスナー ---
    sendLocationBtn.addEventListener('click', getLocationAndSend);

    // --- 初期化実行 ---
    initializeLiff();
});