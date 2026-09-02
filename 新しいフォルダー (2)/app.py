from flask import Flask, render_template_string, jsonify, request
import google.generativeai as genai
import re
import os

app = Flask(__name__)

# =====================================================================
# ★ここにあなたのGemini APIキーを入力します
# =====================================================================
GOOGLE_API_KEY = "AQ.Ab8RN6KwFTv7eg1mrN9BhKBAdDiN9hVnLRTIBXkf_6vKuHmoMw"
genai.configure(api_key=GOOGLE_API_KEY)

# --- [ターゲット別・機密情報データベース] ---
DEFAULT_HACK_DATA = {
    "野崎": {"location": "東京都千代田区霞が関２丁目１−１（警視庁本部・公安部）", "lat": 35.6761, "lng": 139.7503, "ip": "192.168.55.21"},
    "佐野": {"location": "東京都千代田区霞が関２丁目１−２（警察庁）", "lat": 35.6765, "lng": 139.7508, "ip": "192.168.55.10"},
    "黒須": {"location": "東京都港区赤坂９丁目７−１（防衛省・別班ダミー拠点付近）", "lat": 35.6664, "lng": 139.7314, "ip": "10.0.12.44"},
    "新シー": {"location": "バルカ共和国・首都ウランバートル郊外（セーフハウス）", "lat": 47.9188, "lng": 106.9176, "ip": "185.220.101.5"}
}

def ask_zakura_ai(user_text):
    match = re.search(r"(.+?)(を調べて|の場所|の現在地|をハッキング)", user_text)
    if match:
        target_name = match.group(1).strip()
        target_name = target_name.replace("ザクラ", "").replace("、", "").replace(" ", "")
        return f"ZAKURA_HACK_TRIGGER:{target_name}"
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="あなたはVIVANTの別班統合AIザクラです。優秀なAIとして、1〜2文で短くエージェントに返答してください。"
        )
        response = model.generate_content(user_text)
        return response.text
    except Exception:
        return "スタンドアローンモード稼働中。指示をどうぞ。"

# --- Web画面（ターゲット名連動型ハッキングUI） ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZAKURA - Mainframe System</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #050505; color: #fff; text-align: center; margin:0; padding:0; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; overflow:hidden; }
        h1 { color: #ff1a1a; font-size: 22px; letter-spacing: 6px; margin: 10px 0 5px 0; font-weight: bold; }
        .zakura-character {
            width: 140px; height: 140px; border-radius: 50%;
            background: radial-gradient(circle, #330000 0%, #110000 100%); border: 4px solid #ff1a1a;
            box-shadow: 0 0 25px #ff1a1a; display: flex; justify-content:center; align-items:center; cursor: pointer; transition: all 0.5s; animation: breathe 3s infinite ease-in-out;
        }
        .zakura-eye { width: 30px; height: 30px; background-color: #ff1a1a; border-radius: 50%; box-shadow: 0 0 15px #ff1a1a; transition: all 0.2s; }
        .zakura-character.listening { border-color: #00ff00; box-shadow: 0 0 35px #00ff00; }
        .zakura-character.listening .zakura-eye { background-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
        .zakura-character.thinking { border-color: #ffaa00; box-shadow: 0 0 35px #ffaa00; animation: rotateCore 1s infinite linear; }
        .zakura-character.thinking .zakura-eye { background-color: #ffaa00; box-shadow: 0 0 15px #ffaa00; }
        .zakura-character.speaking { border-color: #00ffff; box-shadow: 0 0 35px #00ffff; animation: none; }
        .zakura-character.speaking .zakura-eye { background-color: #00ffff; box-shadow: 0 0 20px #00ffff; }
        .hack-panel { width: 90%; max-width: 500px; background: #111; border: 1px solid #ff1a1a; border-radius: 5px; margin-top: 15px; padding: 10px; display: none; text-align: left; font-family: monospace; font-size: 12px; box-shadow: 0 0 15px rgba(255,26,26,0.2); }
        .hack-log { color: #00ff00; height: 80px; overflow-y: auto; margin-bottom: 10px; border-bottom: 1px solid #222; }
        .map-box { width: 100%; height: 120px; background: #222; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: #ff1a1a; font-weight: bold; text-align: center; }
        .status { font-size: 12px; color: #444; font-family: monospace; margin-top: 10px; }
        @keyframes breathe { 0% { transform: scale(1); } 50% { transform: scale(1.04); } 100% { transform: scale(1); } }
        @keyframes rotateCore { 0% { transform: rotate(0deg); border-style: dashed; } 100% { transform: rotate(360deg); border-style: dashed; } }
    </style>
    <script>
        let recognition; let isSpeaking = false;
        function initZakura() {
            if (recognition) return;
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'ja-JP'; recognition.continuous = true; recognition.interimResults = false;
            const core = document.getElementById('zakura-core'); const statusText = document.getElementById('status-text');
            recognition.onstart = () => { core.className = "zakura-character listening"; statusText.innerText = "STATUS: LISTENING..."; };
            recognition.onresult = (event) => {
                if (isSpeaking) return;
                const speech = event.results[event.results.length - 1].transcript.trim();
                if (speech.includes("ザクラ")) {
                    core.className = "zakura-character thinking"; statusText.innerText = "STATUS: THINKING...";
                    recognition.stop();
                    fetch('/voice_command', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: speech })
                    }).then(res => res.json()).then(data => {
                        if (data.action === "HACK") {
                            triggerHackingVisuals(data.name, data.data);
                        } else {
                            speakZakura(data.response);
                        }
                    });
                }
            };
            recognition.onerror = () => { restartRecognition(); }; recognition.onend = () => { restartRecognition(); };
            recognition.start();
        }
        function restartRecognition() { if (!isSpeaking && recognition) { try { recognition.start(); } catch(e) {} } }
        function triggerHackingVisuals(name, data) {
            document.getElementById('hack-panel').style.display = "block";
            const logBox = document.getElementById('hack-log'); logBox.innerHTML = "";
            const logs = [
                `📡 [INFO] ターゲット名『${name}』のシグナルスキャンを開始...`,
                `🔑 [BYPASS] 暗号化ネットワークから『${name}』の通信端末を抽出中...`,
                `⚡ [HACK] 割り当てIP: ${data.ip} のプロキシを強制解除。`,
                `📍 [SUCCESS] 位置情報補足完了。住所データをザクラ・メインフレームに転送。`
            ];
            let i = 0;
            let logTimer = setInterval(() => {
                if (i < logs.length) {
                    logBox.innerHTML += `<div>${logs[i]}</div>`; logBox.scrollTop = logBox.scrollHeight; i++;
                } else {
                    clearInterval(logTimer);
                    speakZakura(`対象、${name}の逆探知に成功。現在地は、${data.location}。周辺地図をロックオンしました。`);
                    document.getElementById('map-box').innerHTML = `<div>[LIVE TARGET: ${name}]<br><span style='color:#00ff00; font-size:11px;'>${data.location}</span><br><span style='font-size:10px; color:#666;'>LAT: ${data.lat} / LNG: ${data.lng}</span></div>`;
                }
            }, 800);
        }
        function speakZakura(text) {
            isSpeaking = true; const core = document.getElementById('zakura-core'); const eye = document.getElementById('zakura-eye'); const statusText = document.getElementById('status-text');
            core.className = "zakura-character speaking"; statusText.innerText = "STATUS: TRANSMITTING...";
            const uttr = new SpeechSynthesisUtterance(text); uttr.lang = 'ja-JP'; uttr.pitch = 0.5; uttr.rate = 1.15;
            let speechTimer = setInterval(() => {
                if (!isSpeaking) { clearInterval(speechTimer); return; }
                let volumeFactor = Math.random() * 0.3 + 0.9; let eyeFactor = Math.random() * 15 + 25;       
                core.style.transform = `scale(${volumeFactor})`; eye.style.width = `${eyeFactor}px`; eye.style.height = `${eyeFactor}px`;
            }, 70);
            uttr.onend = () => {
                isSpeaking = false; clearInterval(speechTimer); core.style.transform = "scale(1)"; eye.style.width = "30px"; eye.style.height = "30px";
                core.className = "zakura-character listening"; statusText.innerText = "STATUS: LISTENING...";
                initZakura();
            };
            window.speechSynthesis.speak(uttr);
        }
    </script>
</head>
<body>
    <h1>ZAKURA MAINFRAME</h1>
    <div id="zakura-core" class="zakura-character" onclick="initZakura()"><div id="zakura-eye" class="zakura-eye"></div></div>
    <div id="status-text" class="status">TAP CORE TO LINK</div>
    <div id="hack-panel" class="hack-panel">
        <div id="hack-log" class="hack-log"></div>
        <div id="map-box" class="map-box">🗺️ WAITING FOR TARGET LOCK...</div>
    </div>
</body>
</html>
"""

@app.route('/voice_command', methods=['POST'])
def voice_command():
    user_msg = request.json.get("message", "")
    ai_response = ask_zakura_ai(user_msg)
    if ai_response.startswith("ZAKURA_HACK_TRIGGER:"):
        target_name = ai_response.split(":")[1]
        if target_name in DEFAULT_HACK_DATA:
            target_data = DEFAULT_HACK_DATA[target_name]
        else:
            target_data = {"location": f"不明な通信エリア（{target_name}の拠点）", "lat": 35.6586, "lng": 139.7454, "ip": "172.16.89.25"}
        return jsonify({"action": "HACK", "name": target_name, "data": target_data})
    return jsonify({"action": "TALK", "response": ai_response})

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Render専用のポートを強制認識させる設定
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
