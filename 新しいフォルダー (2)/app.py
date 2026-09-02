from flask import Flask, render_template_string, jsonify, request
import google.generativeai as genai
import os

app = Flask(__name__)

# ★ここにあなたのGemini APIキーを貼り付け直してください
GOOGLE_API_KEY = "AQ.Ab8RN6KwFTv7eg1mrN9BhKBAdDiN9hVnLRTIBXkf_6vKuHmoMw"
genai.configure(api_key=GOOGLE_API_KEY)

# 固定のハッキングデータベース（野崎・佐野・黒須など）
HACK_DB = {
    "野崎": {"location": "東京都千代田区霞が関２丁目１−１（警視庁本部・公安部）", "lat": 35.6761, "lng": 139.7503},
    "佐野": {"location": "東京都千代田区霞が関２丁目１−２（警察庁）", "lat": 35.6765, "lng": 139.7508},
    "黒須": {"location": "東京都港区赤坂９丁目７−１（防衛省・別班ダミー拠点付近）", "lat": 35.6664, "lng": 139.7314}
}

# ザクラの頭脳（Gemini API連携）
def ask_zakura(text):
    if any(k in text for k in ["ハッキング", "調べ", "場所", "どこ"]):
        for name, data in HACK_DB.items():
            if name in text:
                return f"HACK:{name}:{data['location']}:{data['lat']}:{data['lng']}"
        return "HACK:UNKNOWN:不明な通信エリア:35.6586:139.7454"
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="あなたはVIVANTの別班最高機密AIザクラです。クールで優秀なAIとして、1〜2文で短く回答してください。漢字を多くせず聞き取りやすい文章にしてください。"
        )
        return model.generate_content(text).text
    except:
        return "スタンドアローンモード稼働中。指示をどうぞ。"

# --- クラウドでも100%エラーが出ない軽量サイバーUI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZAKURA MAINFRAME</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #050505; color: #fff; text-align: center; margin:0; padding:0; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; overflow:hidden; }
        h1 { color: #ff1a1a; font-size: 22px; letter-spacing: 6px; margin: 10px 0; font-weight: bold; }
        .zakura-character { width: 140px; height: 140px; border-radius: 50%; background: radial-gradient(circle, #330000 0%, #110000 100%); border: 4px solid #ff1a1a; box-shadow: 0 0 25px #ff1a1a; display: flex; justify-content:center; align-items:center; cursor: pointer; transition: all 0.5s; animation: breathe 3s infinite ease-in-out; }
        .zakura-eye { width: 30px; height: 30px; background-color: #ff1a1a; border-radius: 50%; box-shadow: 0 0 15px #ff1a1a; transition: all 0.2s; }
        .zakura-character.listening { border-color: #00ff00; box-shadow: 0 0 35px #00ff00; }
        .zakura-character.listening .zakura-eye { background-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
        .zakura-character.thinking { border-color: #ffaa00; box-shadow: 0 0 35px #ffaa00; animation: rotateCore 1s infinite linear; }
        .zakura-character.speaking { border-color: #00ffff; box-shadow: 0 0 35px #00ffff; animation: none; }
        .zakura-character.speaking .zakura-eye { background-color: #00ffff; box-shadow: 0 0 20px #00ffff; }
        .hack-panel { width: 90%; max-width: 500px; background: #111; border: 1px solid #ff1a1a; border-radius: 5px; margin-top: 15px; padding: 10px; display: none; text-align: left; font-family: monospace; font-size: 11px; }
        .hack-log { color: #00ff00; height: 60px; overflow-y: auto; margin-bottom: 5px; border-bottom: 1px solid #222; }
        .map-box { width: 100%; height: 90px; background: #222; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: #ff1a1a; font-weight: bold; text-align: center; }
        .status { font-size: 12px; color: #444; font-family: monospace; margin-top: 10px; }
        @keyframes breathe { 0% { transform: scale(1); } 50% { transform: scale(1.04); } 100% { transform: scale(1); } }
        @keyframes rotateCore { 0% { transform: rotate(0deg); border-style: dashed; } 100% { transform: rotate(360deg); border-style: dashed; } }
    </style>
    <script>
        let rec; let isSpeaking = false;
        function initZakura() {
            if (rec) return;
            rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = 'ja-JP'; rec.continuous = true;
            const core = document.getElementById('zakura-core'); const statusText = document.getElementById('status-text');
            rec.onstart = () => { core.className = "zakura-character listening"; statusText.innerText = "STATUS: LISTENING..."; };
            rec.onresult = (event) => {
                if (isSpeaking) return;
                const speech = event.results[event.results.length - 1].transcript.trim();
                if (speech.includes("ザクラ")) {
                    core.className = "zakura-character thinking"; statusText.innerText = "STATUS: THINKING..."; rec.stop();
                    fetch('/voice_command', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: speech })
                    }).then(res => res.json()).then(data => {
                        if (data.action === "HACK") {
                            triggerHacking(data.name, data.location, data.lat, data.lng);
                        } else {
                            speakZakura(data.response);
                        }
                    });
                }
            };
            rec.onerror = () => { restartRec(); }; rec.onend = () => { restartRec(); }; rec.start();
        }
        function restartRec() { if (!isSpeaking && rec) { try { rec.start(); } catch(e) {} } }
        function triggerHacking(name, loc, lat, lng) {
            document.getElementById('hack-panel').style.display = "block";
            const logBox = document.getElementById('hack-log'); logBox.innerHTML = "📡 シグナルスキャン開始...<br>🔑 暗号ネットワーク突破中...<br>📍 位置情報ロック完了。";
            speakZakura(`対象、${name}の逆探知に成功。現在地は、${loc}。周辺地図をロックオンしました。`);
            document.getElementById('map-box').innerHTML = `<div>[LIVE TARGET: ${name}]<br><span style='color:#00ff00;'>${loc}</span><br><span style='color:#666;'>LAT: ${lat} / LNG: ${lng}</span></div>`;
        }
        function speakZakura(text) {
            isSpeaking = true; const core = document.getElementById('zakura-core'); const eye = document.getElementById('zakura-eye');
            core.className = "zakura-character speaking";
            const uttr = new SpeechSynthesisUtterance(text); uttr.lang = 'ja-JP'; uttr.pitch = 0.5; uttr.rate = 1.15;
            let timer = setInterval(() => {
                if (!isSpeaking) { clearInterval(timer); return; }
                core.style.transform = `scale(${Math.random() * 0.3 + 0.9})`;
                eye.style.width = `${Math.random() * 15 + 25}px`; eye.style.height = eye.style.width;
            }, 70);
            uttr.onend = () => {
                isSpeaking = false; clearInterval(timer); core.style.transform = "scale(1)"; eye.style.width = "30px"; eye.style.height = "30px";
                core.className = "zakura-character listening"; initZakura();
            };
            window.speechSynthesis.speak(uttr);
        }
    </script>
</head>
<body>
    <h1>ZAKURA MAINFRAME</h1>
    <div id="zakura-core" class="zakura-character" onclick="initZakura()"><div id="zakura-eye" class="zakura-eye"></div></div>
    <div id="status-text" class="status">TAP CORE TO LINK</div>
    <div id="hack-panel" class="hack-panel"><div id="hack-log" class="hack-log"></div><div id="map-box" class="map-box">🗺️ WAITING...</div></div>
</body>
</html>
"""

@app.route('/voice_command', methods=['POST'])
def voice_command():
    user_msg = request.json.get("message", "")
    res = ask_zakura(user_msg)
    if res.startswith("HACK:"):
        _, name, loc, lat, lng = res.split(":")
        return jsonify({"action": "HACK", "name": name, "location": loc, "lat": lat, "lng": lng})
    return jsonify({"action": "TALK", "response": res})

@app.route('/')
def home():
    return HTML_TEMPLATE

if __name__ == '__main__':
    # クラウドサーバーが指定するポートで起動
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
