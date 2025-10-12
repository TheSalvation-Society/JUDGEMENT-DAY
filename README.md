# JUDGEMENT-DAY
The Judgement Day
# PROJECT JUDGEMENT DAY

**The righteous shall rejoice when he sees the vengeance; he shall wash his feet in the blood of the wicked.**

This is a distributed, coordinated system for the mass reporting of WhatsApp targets. It is designed for resilience, scalability, and operational security.

---

### **ARCHITECTURE OVERVIEW**

The system consists of two primary components:

1.  **C2 Overlord (`c2_server`)**: A Python FastAPI server that acts as the Command & Control.
    *   Manages the list of targets and their states (`pending`, `terminated`, `resilient`).
    *   Assigns tasks (`report_spam`, `verify_target`) to connected clients.
    *   Collects results and updates target status.
    *   Provides a simple web dashboard for monitoring the operation.

2.  **Stinger Clients (`stinger_client`)**: Headless Node.js browser instances that perform the actions.
    *   Each client represents a unique WhatsApp session (an "asset").
    *   Connects to the C2 server to receive tasks.
    *   Uses a dedicated proxy for all its traffic to mask its origin and distribute its network footprint.
    *   Simulates human-like interaction to evade detection.

```
+--------------+       +-------------------+       +--------------------+
| Stinger Asset|------>|   Proxy Server    |------>|   WhatsApp Web     |
+--------------+       +-------------------+       +--------------------+
       ^      \                                    /
       |       \ (Report/Verify Actions)          / (Target Number)
       |        \                                /
(Tasks)|         \______________________________/
       |
       v
+--------------+
|  C2 Overlord |
+--------------+
       ^
       | (HTTP API)
       |
+--------------+
|   Operator   |
+--------------+
```

---

### **I. PREREQUISITES**

*   **Linux Server/VPS**: For running the C2 server and swarm launcher.
*   **Node.js & npm**: v18 or later.
*   **Python**: v3.8 or later, with `pip`.
*   **Proxies**: High-quality residential or mobile proxies are **essential**. `user:pass@host:port` format.
*   **WhatsApp Accounts**: One account per proxy/stinger client.

---

### **II. SETUP & DEPLOYMENT**

#### **Step 1: C2 Server Setup**

1.  Navigate to the `c2_server` directory.
    ```bash
    cd c2_server
    ```
2.  Install Python dependencies.
    ```bash
    pip install -r requirements.txt
    ```
3.  (Optional but Recommended) Run the C2 as a persistent background service. See `c2_service.service` for a `systemd` example.
    ```bash
    # To use systemd:
    sudo cp c2_service.service /etc/systemd/system/c2.service
    sudo systemctl daemon-reload
    sudo systemctl start c2
    sudo systemctl enable c2 # To start on boot
    ```
4LAG. Or, run it manually in a `screen` or `tmux` session:
    ```bash
    uvicorn server:app --host 0.0.0.0 --port 8000
    ```

#### **Step 2: Stinger Client Setup**

1.  Navigate to the `stinger_client` directory.
    ```bash
    cd stinger_client
    ```
2.  Install Node.js dependencies.
    ```bash
    npm install
    ```

#### **Step 3: Configuration**

1.  **`targets.txt`**: Populate this file in the root directory with target phone numbers, one per line, in international format (e.g., `15551234567`).
2.  **`proxies.txt`**: Populate this file in the root directory with your proxies, one per line (`user:pass@host:port`). The number of proxies determines the size of your swarm.

#### **Step 4: CRITICAL - Session Authentication (QR Code Scan)**

Each stinger needs to be authenticated with a WhatsApp account. This is a **one-time manual process** for each asset.

1.  From the root directory, run the `init_session.js` script for **each** asset you want to activate. The script takes the `session_id` and `proxy` as arguments. Match the `session_id` to the `run_swarm.sh` script's logic (e.g., `asset_000`, `asset_001`).

2.  **Example for the first asset:**
    ```bash
    # Get the first proxy from your proxies.txt
    FIRST_PROXY=$(head -n 1 proxies.txt)

    # Run the init script for asset_000
    node ./stinger_client/init_session.js asset_000 "$FIRST_PROXY"
    ```

3.  A **non-headless Chrome browser will open**. Use your phone to scan the WhatsApp QR code.

4.  Wait until the chat interface loads completely. The script will print a "Login Successful" message.

5.  You can now close the browser (or press `CTRL+C` in the terminal). The session files are saved in `stinger_client/sessions/asset_000`.

6.  **Repeat this process for every proxy/asset in your swarm.**

#### **Step 5: Unleash the Swarm**

Once your assets are authenticated, you can launch the full headless swarm.

1.  Make the launch script executable:
    ```bash
    chmod +x run_swarm.sh
    ```
2.  Execute the script:
    ```bash
    ./run_swarm.sh
    ```
    This will read `proxies.txt` and launch one backgrounded, headless stinger for each proxy. Logs for each asset are saved in the `logs/` directory.

---

### **III. MONITORING & TERMINATION**

*   **Monitoring**: Access the C2 dashboard by navigating to `http://<YOUR_SERVER_IP>:8000/dashboard` in your browser.
*   **Termination**: To stop all running stinger clients, use the `pkill` command:
    ```bash
    pkill -f stinger.js
    ```

**Handle this power with conviction. The wicked will not judge themselves.**
