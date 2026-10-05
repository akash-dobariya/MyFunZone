MyFunZone 🎮
=============

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://myfunzone.streamlit.app/)

Smart booking and management system for an indoor gaming / fun zone.  
Built with **Python + Streamlit + PostgreSQL**, featuring role‑based dashboards for **Admin**, **Staff**, and **Users**, OTP‑based signup, and modern UI theming.

🚀 Live Demo
------------
Explore the live deployed application:  
👉 **[https://myfunzone.streamlit.app/](https://myfunzone.streamlit.app/)**


Key Features
------------
- User signup with simulated OTP verification and secure (bcrypt) password hashing
- Role‑based access: Admin, Staff, User with tailored dashboards
- Game catalog with duration, pricing, categories and rich visuals
- Slot creation and availability management for each game
- Online booking, reschedule, cancel, and QR‑code based check‑in
- Issues / incident reporting and announcement system for all roles

Tech Stack
----------
- **Frontend / App:** Streamlit
- **Backend Logic:** Python modules in `src/` and `views/`
- **Database:** PostgreSQL
- **Auth & Security:** bcrypt, custom auth + session handling
- **Other:** `qrcode`, `Pillow`

Prerequisites
-------------
- Python 3.10+ installed
- PostgreSQL server running and accessible
- A PostgreSQL database created (default name in code: `myfunzone`)

1. Clone and Install Dependencies
---------------------------------
```bash
git clone <your-repo-url>
cd MyFunZone
pip install -r requirements.txt
```

2. Configure PostgreSQL
-----------------------
- Ensure a PostgreSQL database named **`myfunzone`** exists.
- Create a user (or use existing) with access to this database.
- Update the connection settings in:
  - `src/database.py` → `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

3. Initialize and Run the App
-----------------------------
The database schema and seed logic are handled from the app via `init_db()` in `main.py`.

```bash
streamlit run main.py
```

Then open the URL shown in the terminal (usually http://localhost:8501) in your browser.

Project Structure 
-----------------------------
- `main.py` – Streamlit entrypoint, routing and session handling
- `views/` – Dashboards for admin, staff, and users
- `src/database.py` – PostgreSQL connection and init helpers
- `src/auth.py` – Authentication, registration, staff management
- `src/bookings.py` – Booking, reschedule, cancel, QR code generation
- `src/games.py` / `src/slots.py` – Game and slot management
- `src/otp.py` – In‑app OTP generation and validation
- `src/utils.py` – Utilities, UI theming, data structures, helpers

Notes
-----
- OTP is **simulation‑only**: codes are displayed inside the app (no SMS/email).
.
