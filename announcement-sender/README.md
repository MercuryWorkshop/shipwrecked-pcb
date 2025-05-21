# Setup
1. Create a venv in this folder:
    Mac/Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    Windows:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Grab `signing_key.txt` from the Slack (in #shipwrecked-pcb's pinned messages) and put it in this folder.
4. Plug a badge into your computer.
5. Run it:
    ```bash
    python main.py
    ```
