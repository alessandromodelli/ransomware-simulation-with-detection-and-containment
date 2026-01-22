from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route('/status', methods=['POST'])
def upload_file():
    agent_id = request.form.get("id")
    
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Organize files per agent
    agent_dir = os.path.join(UPLOAD_DIR, agent_id or "unknown")
    os.makedirs(agent_dir, exist_ok=True)

    filepath = os.path.join(agent_dir, file.filename)
    file.save(filepath)

    print(f"[+] Received file from {agent_id}: {filepath}")

    return jsonify({"status": "file saved", "path": filepath}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)