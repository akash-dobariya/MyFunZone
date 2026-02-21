import bcrypt
import re
import base64

class LinkedListNode:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node


class LinkedList:
    def __init__(self):
        self.head = None

    def insert_front(self, value):
        new_node = LinkedListNode(value, self.head)
        self.head = new_node

    def insert_back(self, value):
        new_node = LinkedListNode(value)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def delete_value(self, value):
        current = self.head
        previous = None
        while current:
            if current.value == value:
                if previous:
                    previous.next = current.next
                else:
                    self.head = current.next
                return True
            previous = current
            current = current.next
        return False

    def to_list(self):
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            return None
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)


class Queue:
    def __init__(self):
        self._items = []
        self._front_index = 0

    def enqueue(self, item):
        self._items.append(item)

    def dequeue(self):
        if self.is_empty():
            return None
        item = self._items[self._front_index]
        self._front_index += 1
        if self._front_index > 50 and self._front_index > len(self._items) // 2:
            self._items = self._items[self._front_index:]
            self._front_index = 0
        return item

    def peek(self):
        if self.is_empty():
            return None
        return self._items[self._front_index]

    def is_empty(self):
        return self._front_index >= len(self._items)

    def size(self):
        return len(self._items) - self._front_index


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def render_footer():
    import streamlit as st

    st.markdown(
        """
        <div style="
            margin-top: 1.5rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(148,163,184,0.4);
            text-align: center;
            font-size: 0.8rem;
            color: rgba(226,232,240,0.9);
        ">
            © 2026 MyFunZone. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_image_urls(image_value):
    if not image_value:
        return []
    parts = re.split(r"[\n,]", image_value)
    urls = []
    for part in parts:
        cleaned = part.strip()
        if cleaned and cleaned not in urls:
            urls.append(cleaned)
    return urls

def apply_role_style(role=None):
    import os
    import streamlit as st

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    bg_url = ""
    overlay_opacity = 0.7
    admin_style = False
    user_style = False
    staff_style = False

    if role == "user":
        user_style = True
        try:
            local_img_path = os.path.join(BASE_DIR[0:27], "assets", "User_bg1.png")

            if not os.path.exists(local_img_path):
                st.error("❌ assets/User_bg.png not found")
                return

            bin_str = get_base64_of_bin_file(local_img_path)
            bg_url = f"data:image/png;base64,{bin_str}"
            overlay_opacity = 0.75

        except Exception as e:
            st.error(f"Background load failed: {e}")
            return

    elif role == "staff":
        staff_style = True
        try:
            local_img_path = os.path.join(BASE_DIR[0:27], "assets", "User_bg1.png")

            if not os.path.exists(local_img_path):
                st.error("❌ assets/User_bg.png not found")
                return

            bin_str = get_base64_of_bin_file(local_img_path)
            bg_url = f"data:image/png;base64,{bin_str}"
            overlay_opacity = 0.75

        except Exception as e:
            st.error(f"Background load failed: {e}")
            return        
     

    elif role == "admin":
        admin_style = True
    
     

    else:
        bg_url=f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(BASE_DIR[0:27], "assets", "User_bg1.png"))}"

    if admin_style:
        st.markdown(
            """
            <style>
            .stApp {
                background: radial-gradient(circle at top left, #1b2845 0%, #050816 55%, #020617 100%);
                color: #e2e8f0;
            }
            .stMain {
                padding-top: 0.75rem;
            }
            h1, h2, h3, h4 {
                color: #f9fafb;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, label {
                color: #e5e7eb;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.25rem;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(15,23,42,0.9);
                color: #cbd5f5;
                border-radius: 999px;
                border: 1px solid rgba(148,163,184,0.5);
                padding: 0.25rem 0.9rem;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, #00b4d8, #38bdf8);
                color: #0f172a !important;
                border-color: transparent;
            }
            .stExpander {
                background-color: rgba(15,23,42,0.92);
                border-radius: 10px;
                border: 1px solid rgba(148,163,184,0.45);
            }
            .stExpander > div {
                color: #e5e7eb;
            }
            .stTextInput input, .stNumberInput input, textarea {
                background-color: rgba(15,23,42,0.95);
                color: #e5e7eb;
                border-radius: 8px;
                border: 1px solid rgba(148,163,184,0.6);
            }
            .stTextInput input:focus, .stNumberInput input:focus, textarea:focus {
                border-color: #38bdf8;
                box-shadow: 0 0 0 1px #38bdf8;
            }
            .stSelectbox div[data-baseweb="select"] > div,
            .stMultiSelect div[data-baseweb="select"] > div {
                background-color: rgba(15,23,42,0.95);
                color: #e5e7eb;
                border-radius: 8px;
                border: 1px solid rgba(148,163,184,0.6);
            }
            .stCheckbox > label {
                color: #e5e7eb;
            }
            .stButton > button {
                background-color: rgba(15,23,42,0.9);
                color: #e5e7eb;
                border-radius: 999px;
                border: 1px solid rgba(148,163,184,0.6);
                font-weight: 500;
                padding: 0.3rem 0.95rem;
                transition: background-color 0.15s ease, transform 0.08s ease, box-shadow 0.15s ease, border-color 0.15s ease;
            }
            .stButton > button:hover {
                background-color: rgba(30,64,175,0.9);
                border-color: rgba(96,165,250,0.9);
                box-shadow: 0 8px 18px rgba(15,23,42,0.75);
                transform: translateY(-1px);
                color: #f9fafb;
            }
            .stButton > button:active {
                transform: translateY(0);
                box-shadow: 0 3px 10px rgba(15,23,42,0.65);
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #e11d48, #f97373);
                border-color: #f97373;
                color: #f9fafb;
            }
            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #be123c, #fb7185);
                border-color: #fb7185;
                color: #ffffff;
            }
            .stAlert {
                border-radius: 10px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    elif staff_style:
        st.markdown(
            """
            <style>
            .stApp {
                background: linear-gradient(140deg, #020617 0%, #0b1120 35%, #1f2937 80%, #0f172a 100%);
                color: #e5e7eb;
            }
            .stMain {
                padding-top: 0.5rem;
            }
            h1, h2, h3, h4 {
                color: #f9fafb;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, label {
                color: #e5e7eb;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.3rem;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(15,23,42,0.96);
                color: #cbd5f5;
                border-radius: 8px;
                border: 1px solid rgba(148,163,184,0.6);
                padding: 0.2rem 0.8rem;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, #22c55e, #facc15);
                color: #0f172a !important;
                border-color: transparent;
            }
            .stExpander {
                background-color: rgba(15,23,42,0.96);
                border-radius: 10px;
                border: 1px solid rgba(107,114,128,0.7);
            }
            .stTextInput input, .stNumberInput input, textarea {
                background-color: rgba(15,23,42,0.97);
                color: #e5e7eb;
                border-radius: 6px;
                border: 1px solid rgba(107,114,128,0.9);
            }
            .stTextInput input:focus, .stNumberInput input:focus, textarea:focus {
                border-color: #22c55e;
                box-shadow: 0 0 0 1px #22c55e;
            }
            .stSelectbox div[data-baseweb="select"] > div,
            .stMultiSelect div[data-baseweb="select"] > div {
                background-color: rgba(15,23,42,0.97);
                color: #e5e7eb;
                border-radius: 6px;
                border: 1px solid rgba(107,114,128,0.9);
            }
            .stButton > button {
                background-color: rgba(15,23,42,0.95);
                color: #e5e7eb;
                border-radius: 999px;
                border: 1px solid rgba(148,163,184,0.9);
                font-weight: 500;
                padding: 0.25rem 0.9rem;
                transition: background-color 0.15s ease, transform 0.08s ease, box-shadow 0.15s ease, border-color 0.15s ease;
            }
            .stButton > button:hover {
                background-color: rgba(31,41,55,1);
                border-color: rgba(248,250,252,0.9);
                box-shadow: 0 7px 16px rgba(15,23,42,0.8);
                transform: translateY(-1px);
            }
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #f97316, #facc15);
                border-color: #facc15;
                color: #0b1120;
            }
            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #ea580c, #eab308);
                border-color: #fde047;
                color: #020617;
            }
            .stAlert {
                border-radius: 8px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    elif user_style:
        st.markdown(
            """
            <style>
            .stApp {
                background: radial-gradient(circle at top, #0ea5e9 0%, #1d4ed8 25%, #020617 70%);
                color: #e5e7eb;
            }
            .stMain {
                padding-top: 0.5rem;
            }
            h1, h2, h3, h4 {
                color: #f9fafb;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, label {
                color: #e5e7eb;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.3rem;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(15,23,42,0.92);
                color: #bfdbfe;
                border-radius: 999px;
                border: 1px solid rgba(59,130,246,0.8);
                padding: 0.25rem 1rem;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, #22c55e, #a855f7);
                color: #020617 !important;
                border-color: transparent;
            }
            .stExpander {
                background-color: rgba(15,23,42,0.9);
                border-radius: 14px;
                border: 1px solid rgba(96,165,250,0.85);
            }
            .stTextInput input, .stNumberInput input, textarea {
                background-color: rgba(15,23,42,0.96);
                color: #e5e7eb;
                border-radius: 999px;
                border: 1px solid rgba(59,130,246,0.9);
                padding-left: 0.9rem;
            }
            .stTextInput input:focus, .stNumberInput input:focus, textarea:focus {
                border-color: #a855f7;
                box-shadow: 0 0 0 1px #a855f7;
            }
            .stSelectbox div[data-baseweb="select"] > div,
            .stMultiSelect div[data-baseweb="select"] > div {
                background-color: rgba(15,23,42,0.96);
                color: #e5e7eb;
                border-radius: 999px;
                border: 1px solid rgba(59,130,246,0.9);
            }
            .stButton > button {
                background: linear-gradient(135deg, #0ea5e9, #22c55e);
                color: #020617;
                border-radius: 999px;
                border: none;
                font-weight: 600;
                padding: 0.35rem 1.1rem;
                box-shadow: 0 10px 18px rgba(15,23,42,0.75);
                transition: transform 0.08s ease, box-shadow 0.12s ease, filter 0.12s ease;
            }
            .stButton > button:hover {
                filter: brightness(1.05);
                transform: translateY(-1px);
                box-shadow: 0 14px 28px rgba(15,23,42,0.85);
            }
            .stButton > button:active {
                transform: translateY(0);
                box-shadow: 0 6px 14px rgba(15,23,42,0.8);
            }
            .stAlert {
                border-radius: 12px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: linear-gradient(
                    rgba(15,23,42,{overlay_opacity + 0.1}),
                    rgba(15,23,42,{overlay_opacity + 0.2})
                ), url("{bg_url}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                color: #e5e7eb;
            }}
            .stMain {{
                padding-top: 3rem;
            }}
            .block-container {{
                max-width: 480px;
                margin: 0 auto 3rem auto;
                padding: 2rem 2.5rem 2.2rem 2.5rem;
                background: rgba(15,23,42,0.96);
                border-radius: 18px;
                border: 1px solid rgba(148,163,184,0.55);
                box-shadow: 0 18px 40px rgba(15,23,42,0.9);
            }}
            h1 {{
                text-align: center;
                color: #f9fafb;
                margin-bottom: 1.5rem;
            }}
            .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, label {{
                color: #e5e7eb;
            }}
            .stTextInput input {{
                background-color: rgba(15,23,42,0.98);
                color: #e5e7eb;
                border-radius: 999px;
                border: 1px solid rgba(148,163,184,0.85);
                padding-left: 0.9rem;
            }}
            .stTextInput input:focus {{
                border-color: #38bdf8;
                box-shadow: 0 0 0 1px #38bdf8;
            }}
            .stButton > button {{
                background: linear-gradient(135deg, #0ea5e9, #22c55e);
                color: #020617;
                border-radius: 999px;
                border: none;
                font-weight: 600;
                padding: 0.4rem 1.4rem;
                width: 100%;
                box-shadow: 0 10px 22px rgba(15,23,42,0.85);
                transition: transform 0.08s ease, box-shadow 0.12s ease, filter 0.12s ease;
            }}
            .stButton > button:hover {{
                filter: brightness(1.06);
                transform: translateY(-1px);
                box-shadow: 0 14px 30px rgba(15,23,42,0.9);
            }}
            .stButton > button:active {{
                transform: translateY(0);
                box-shadow: 0 7px 18px rgba(15,23,42,0.85);
            }}
            .stAlert {{
                border-radius: 10px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )




def hash_password(password):
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    """Checks a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_password(password):
    """
    Validates password complexity:
    - Min 6 chars
    - At least 1 number
    - At least 1 char (letter)
    - At least 1 special char
    """
    if len(password) < 6:
        return False
    if not re.search(r"[a-zA-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def validate_phone(phone):
    if not phone:
        return False
        
    #  Remove everything that is NOT a digit or a plus sign
    clean_phone = re.sub(r'[^\d+]', '', phone)

    # Validate Length
    return re.match(r"^\+?\d{10,15}$", clean_phone) is not None
