import streamlit as st
import streamlit.components.v1 as components
from src.games import get_all_games
from src.slots import get_available_slots
from src.bookings import create_booking, get_user_bookings, cancel_booking, reschedule_booking, generate_qr_code, update_booking_status
from src.session import logout_user_session, get_current_user
from src.reviews import add_review, get_user_reviews
from src.announcements import get_announcements_for_role
from datetime import datetime, date
import time
from src.utils import get_base64_of_bin_file, LinkedList, Stack, parse_image_urls, render_footer, validate_password
from src.auth import update_password, get_user_profile, update_user_profile


def show_user_dashboard():
    current_user = get_current_user()
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = 'All'
    if 'recent_games' not in st.session_state:
        st.session_state.recent_games = LinkedList()
    if 'undo_cancel_stack' not in st.session_state:
        st.session_state.undo_cancel_stack = Stack()
    if 'profile_menu_mode' not in st.session_state:
        st.session_state.profile_menu_mode = 'menu'
        
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title(f"Welcome, {current_user['username']}!")
    with col2:
        with st.popover(current_user['username'], use_container_width=True):
            if st.session_state.profile_menu_mode == 'menu':
                if st.button("Update Profile", key="user_profile_open"):
                    st.session_state.profile_menu_mode = 'form'
                    st.rerun()
                if st.button("Logout", key="user_menu_logout"):
                    logout_user_session()
            else:
                profile = get_user_profile(current_user['user_id']) or {}
                email_value = profile.get('email') or ""
                phone_value = profile.get('phone_number') or ""
                email = st.text_input("Email Address (optional)", value=email_value)
                phone = st.text_input("Mobile Number", value=phone_value, max_chars=10)
                new_password = st.text_input("New Password (optional)", type="password")
                confirm_password = st.text_input("Confirm New Password (optional)", type="password")
                save_clicked = st.button("Save Changes", key="user_profile_save")
                cancel_clicked = st.button("Cancel", key="user_profile_cancel")

                if save_clicked:
                    if new_password or confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif not validate_password(new_password):
                            st.error("Password does not meet complexity requirements.")
                        else:
                            success_profile, msg_profile = update_user_profile(
                                current_user['user_id'],
                                email,
                                phone,
                            )
                            if not success_profile:
                                st.error(msg_profile)
                            else:
                                success_pw, msg_pw = update_password(
                                    current_user['user_id'], new_password
                                )
                                if not success_pw:
                                    st.error(msg_pw)
                                else:
                                    st.success("Profile and password updated successfully.")
                                    st.session_state.profile_menu_mode = 'menu'
                    else:
                        success_profile, msg_profile = update_user_profile(
                            current_user['user_id'],
                            email,
                            phone,
                        )
                        if not success_profile:
                            st.error(msg_profile)
                        else:
                            st.success("Profile updated successfully.")
                            st.session_state.profile_menu_mode = 'menu'

                if cancel_clicked:
                    st.session_state.profile_menu_mode = 'menu'
            
    announcements = get_announcements_for_role('user', current_user['user_id'])
    
    if announcements:
        js_announcements = []
        for ann in announcements:
            title = ann['title'].replace("'", "\\'").replace('"', '\\"')
            content = ann['content'].replace("'", "\\'").replace('"', '\\"')
            js_announcements.append(f"{{title: '{title}', content: '{content}'}}")
            
        js_array = "[" + ",".join(js_announcements) + "]"
        
        # Carousel 
        carousel_html = f"""
        <style>
        .carousel-container {{
            width: 100%;
            background: linear-gradient(135deg, rgba(0,180,216,0.1), rgba(0,119,182,0.1));
            border-left: 5px solid #00B4D8;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-family: sans-serif;
            overflow: hidden;
            position: relative;
            height: 80px; /* Fixed height to prevent jumping */
            display: flex;
            align-items: center;
        }}
        .carousel-slide {{
            position: absolute;
            width: 100%;
            opacity: 0;
            transition: opacity 0.5s ease-in-out;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .carousel-slide.active {{
            opacity: 1;
        }}
        .ann-title {{
            font-weight: bold;
            color: #00B4D8;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .ann-content {{
            color: #e0e0e0;
            font-size: 0.9em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 95%;
        }}
        </style>
        
        <div id="carousel" class="carousel-container">
            <!-- Slides injected via JS -->
        </div>
        
        <script>
            const data = {js_array};
            const container = document.getElementById('carousel');
            
            // Create slides
            data.forEach((item, index) => {{
                const slide = document.createElement('div');
                slide.className = 'carousel-slide' + (index === 0 ? ' active' : '');
                slide.innerHTML = `
                    <div class="ann-title">📢 ${{item.title}}</div>
                    <div class="ann-content">${{item.content}}</div>
                `;
                container.appendChild(slide);
            }});
            
            let currentIndex = 0;
            const slides = document.querySelectorAll('.carousel-slide');
            
            if (slides.length > 1) {{
                setInterval(() => {{
                    slides[currentIndex].classList.remove('active');
                    currentIndex = (currentIndex + 1) % slides.length;
                    slides[currentIndex].classList.add('active');
                }}, 4000); // 2 second delay
            }}
        </script>
        """
        components.html(carousel_html, height=100)

    #  Announcement & Offers Button 
    with st.expander("📢 Announcements & Offers", expanded=False):
        if announcements:
            for ann in announcements:
                pinned_icon = "📌" if ann['is_pinned'] else ""
                st.markdown(f"### {pinned_icon} {ann['title']}")
                st.write(ann['content'])
                st.caption(f"Posted: {ann['created_at'].strftime('%Y-%m-%d')}")
                st.divider()
        else:
            st.warning("Sorry, No current offers available!")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Browse Games & Activity", "My Bookings", "My Feedback", "About Us"])
    bg_url = ""
    with tab1:
        import os
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.dirname(BASE_DIR)


        categories = [
            {"name": "All", "img":f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "all.jpg"))}"},
            {"name": "Arcade", "img": f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "arcade.jpg"))}"},
            {"name": "Bowling", "img": f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "Bowling.jpg"))}"},
            {"name": "VR", "img": f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "vr.jpg"))}"},
            {"name": "Sports", "img":f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "sports.jpg"))}" },
            {"name": "Adventure", "img": f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "adventure1.jpg"))}"},
            {"name": "Kids", "img":f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, "assets", "kids1.jpg"))}" }
        ]
        
        st.markdown("""
        <style>
        .category-label {
            font-size: 0.8em;
            text-align: center;
            margin-top: 5px;
            font-weight: bold;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(len(categories))
        for i, cat in enumerate(categories):
            with cols[i]:
                # Visual Highlight for Selected Category
                is_selected = st.session_state.selected_category == cat['name']
                border_color = "#00f2ff" if is_selected else "transparent"
                opacity = "1.0" if is_selected else "0.7"
                
                st.markdown(
                    f"""
                    <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 5px;">
                        <img src="{cat['img']}" style="
                            border-radius: 50%; 
                            width: 60px; 
                            height: 60px; 
                            object-fit: cover; 
                            border: 3px solid {border_color};
                            opacity: {opacity};
                            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                        ">
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
            
                # Using unique key for each button
                if st.button(cat['name'], key=f"btn_cat_{cat['name']}", use_container_width=True):
                    st.session_state.selected_category = cat['name']
                    st.rerun()
        
        st.markdown("---")
        
        st.header(f"Available Games: {st.session_state.selected_category}")

        all_games_for_recent = get_all_games(active_only=True)
        recent_ids = st.session_state.recent_games.to_list()
        if all_games_for_recent and recent_ids:
            st.subheader("Recently booked games & activities (LinkedList)")
            id_to_game = {g['game_id']: g for g in all_games_for_recent}
            seen_recent = set()
            for gid in recent_ids:
                if gid in seen_recent:
                    continue
                game_obj = id_to_game.get(gid)
                if not game_obj:
                    continue
                seen_recent.add(gid)
                with st.expander(f"{game_obj['name']} (ID {game_obj['game_id']})"):
                    target_date_recent = st.date_input(
                        f"Select Date for {game_obj['name']}",
                        min_value=date.today(),
                        key=f"recent_date_{game_obj['game_id']}",
                    )
                    all_slots_recent = get_available_slots(
                        game_obj['game_id'], target_date_recent, include_full=True
                    )
                    available_slots_recent = [
                        s for s in all_slots_recent if s['available_spots'] > 0
                    ]
                    if available_slots_recent:
                        slot_options_recent = {
                            f"{s['start_time']} - {s['end_time']} (Spots left: {s['available_spots']}) - ₹{s['price']}": s
                            for s in available_slots_recent
                        }
                        selected_slot_label_recent = st.selectbox(
                            "Select Time Slot",
                            list(slot_options_recent.keys()),
                            key=f"recent_slot_{game_obj['game_id']}",
                        )
                        if selected_slot_label_recent:
                            selected_slot_recent = slot_options_recent[
                                selected_slot_label_recent
                            ]
                            players_recent = st.number_input(
                                "Number of Players",
                                min_value=1,
                                max_value=selected_slot_recent['available_spots'],
                                value=1,
                                key=f"recent_players_{game_obj['game_id']}",
                            )
                            total_price_recent = selected_slot_recent['price'] * players_recent
                            st.write(
                                f"**Total Price:** ₹{total_price_recent} (Inclusive of 18% GST)"
                            )
                            if st.button(
                                "Confirm Booking",
                                key=f"recent_book_{game_obj['game_id']}",
                            ):
                                success, result = create_booking(
                                    current_user['user_id'],
                                    selected_slot_recent['slot_id'],
                                    players_recent,
                                )
                                if success:
                                    st.session_state.recent_games.insert_front(
                                        game_obj['game_id']
                                    )
                                    values = st.session_state.recent_games.to_list()
                                    seen = set()
                                    unique_values = []
                                    for v in values:
                                        if v not in seen:
                                            unique_values.append(v)
                                            seen.add(v)
                                    unique_values = unique_values[:5]
                                    new_list = LinkedList()
                                    for v in reversed(unique_values):
                                        new_list.insert_front(v)
                                    st.session_state.recent_games = new_list
                                    st.success(
                                        "Booking successful! View your QR code in 'My Bookings'."
                                    )
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"Booking failed: {result}")
                    elif all_slots_recent:
                        st.warning("All slots for this date are fully booked.")
                    else:
                        st.warning("No slots scheduled for this date.")

        games = get_all_games(active_only=True, category=st.session_state.selected_category)
        
        if not games:
            st.info(f"No games found in category: {st.session_state.selected_category}")
        
        for game in games:
            with st.container():
                st.markdown(f"### {game['name']}")
                col1, col2 = st.columns([1, 3])
                with col1:
                    image_urls = parse_image_urls(game.get('image_url'))
                    if image_urls:
                        resolved_urls = []
                        for u in image_urls:
                            if u.startswith("assets/") or u.startswith("assets\\"):
                                try:
                                    local_path = os.path.join(PROJECT_ROOT, u.replace("/", os.sep))
                                    data = get_base64_of_bin_file(local_path)
                                    resolved_urls.append(f"data:image/jpeg;base64,{data}")
                                except Exception:
                                    continue
                            else:
                                resolved_urls.append(u)
                        if resolved_urls:
                            safe_urls = []
                            for u in resolved_urls:
                                safe = u.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                                safe_urls.append(safe)
                            js_array = "[" + ",".join(f"'{u}'" for u in safe_urls) + "]"
                            first_src = safe_urls[0]
                            game_id = game['game_id']
                            html = f"""
                            <style>
                            .game-image-wrapper {{
                                position: relative;
                                width: 100%;
                                height: 220px;
                                overflow: hidden;
                                border-radius: 8px;
                            }}
                            .game-image-wrapper img {{
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                                display: block;
                            }}
                            .game-nav-btn {{
                                position: absolute;
                                top: 50%;
                                transform: translateY(-50%);
                                background: rgba(0,0,0,0.45);
                                border: none;
                                color: #ffffff;
                                font-size: 18px;
                                width: 34px;
                                height: 34px;
                                border-radius: 50%;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            }}
                            .game-nav-btn.left {{
                                left: 8px;
                            }}
                            .game-nav-btn.right {{
                                right: 8px;
                            }}
                            </style>
                            <div class="game-image-wrapper">
                                <img id="game_{game_id}_img" src="{first_src}">
                                <button class="game-nav-btn left" onclick="prevGameImg_{game_id}()">◀</button>
                                <button class="game-nav-btn right" onclick="nextGameImg_{game_id}()">▶</button>
                            </div>
                            <script>
                            (function() {{
                                const images = {js_array};
                                let idx = 0;
                                const imgEl = document.getElementById('game_{game_id}_img');
                                window.prevGameImg_{game_id} = function() {{
                                    idx = (idx - 1 + images.length) % images.length;
                                    imgEl.src = images[idx];
                                }};
                                window.nextGameImg_{game_id} = function() {{
                                    idx = (idx + 1) % images.length;
                                    imgEl.src = images[idx];
                                }};
                            }})();
                            </script>
                            """
                            components.html(html, height=230)
                        else:
                            st.write("🖼️ No Image")
                    else:
                        st.write("🖼️ No Image")
                
                with col2:
                    st.write(game['description'])
                    st.write(f"⏱️ **Duration:** {game['duration_minutes']} mins")
                    st.write(f"₹ **Price (Per Person):** ₹{game['base_price']}")
                    
                    with st.expander(f"Book {game['name']}"):
                        target_date = st.date_input(f"Select Date for {game['name']}", min_value=date.today(), key=f"date_{game['game_id']}")
                        
                        all_slots = get_available_slots(game['game_id'], target_date, include_full=True)
                        available_slots = [s for s in all_slots if s['available_spots'] > 0]
                        
                        if available_slots:
                            slot_options = {f"{s['start_time']} - {s['end_time']} (Spots left: {s['available_spots']}) - ₹{s['price']}": s for s in available_slots}
                            selected_slot_label = st.selectbox("Select Time Slot", list(slot_options.keys()), key=f"slot_{game['game_id']}")
                            
                            if selected_slot_label:
                                selected_slot = slot_options[selected_slot_label]
                                
                                players = st.number_input("Number of Players", min_value=1, max_value=selected_slot['available_spots'], value=1, key=f"players_{game['game_id']}")
                                total_price = selected_slot['price'] * players
                                st.write(f"**Total Price:** ₹{total_price} (Inclusive of 18% GST)")
                                
                                if st.button("Confirm Booking", key=f"book_{game['game_id']}"):
                                    success, result = create_booking(current_user['user_id'], selected_slot['slot_id'], players)
                                    if success:
                                        st.session_state.recent_games.insert_front(game['game_id'])
                                        values = st.session_state.recent_games.to_list()
                                        seen = set()
                                        unique_values = []
                                        for v in values:
                                            if v not in seen:
                                                unique_values.append(v)
                                                seen.add(v)
                                        unique_values = unique_values[:5]
                                        new_list = LinkedList()
                                        for v in reversed(unique_values):
                                            new_list.insert_front(v)
                                        st.session_state.recent_games = new_list
                                        st.success("Booking successful! View your QR code in 'My Bookings'.")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"Booking failed: {result}")
                        elif all_slots:
                            st.warning("All slots for this date are fully booked.")
                        else:
                            st.warning("No slots scheduled for this date.")
                st.markdown("---")

    with tab2:
        st.header("My Bookings")
        if 'undo_cancel_stack' not in st.session_state:
            st.session_state.undo_cancel_stack = Stack()
        bookings = get_user_bookings(current_user['user_id'])
        
        if bookings:
            if not st.session_state.undo_cancel_stack.is_empty():
                if st.button("Undo last cancellation"):
                    last_booking_id = st.session_state.undo_cancel_stack.pop()
                    if last_booking_id is None:
                        st.info("No cancellation to undo.")
                    else:
                        success, msg = update_booking_status(last_booking_id, 'booked')
                        if success:
                            st.success("Last cancellation undone.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
            for booking in bookings:
                with st.expander(f"{booking['game_name']} - {booking['slot_date']} @ {booking['start_time']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Status:** {booking['status'].upper()}")
                        st.write(f"**Payment Status:** {booking.get('payment_status', 'N/A').upper()}")
                        st.write(f"**Players:** {booking['number_of_players']}")
                        st.write(f"**Total Paid:** ₹{booking['amount']}")
                        st.write(f"**Booking ID:** #{booking['booking_id']}")
                        
                        if booking['status'] == 'completed':
                             st.write("✅ **Completed**")
                             
                           #Review button
                             with st.popover("⭐ Rate & Review"):
                                 st.write(f"Rate your experience for {booking['game_name']}")
                                 with st.form(key=f"review_form_{booking['booking_id']}"):
                                     rating = st.slider("Rating (1-5)", 1, 5, 5)
                                     feedback = st.text_area("Feedback (Optional if rating given)")
                                     
                                     if st.form_submit_button("Submit Review"):
                                         if not feedback and not rating:
                                              st.error("Please provide rating or feedback")
                                         else:
                                             success, msg = add_review(
                                                 current_user['user_id'], 
                                                 booking['game_id'], 
                                                 booking['booking_id'], 
                                                 rating, 
                                                 feedback
                                             )
                                             if success:
                                                 st.success(msg)
                                                 time.sleep(1)
                                                 st.rerun()
                                             else:
                                                 st.error(msg)
                                                 
                        elif booking['status'] == 'booked':
                            st.write("🗓️ **Scheduled**")
                        elif booking['status'] == 'checked_in':
                            st.write("🎟️ **Checked In**")
                        elif booking['status'] == 'cancelled':
                            st.write("❌ **Cancelled**")
                            
                        # Receipt Download
                        receipt_html = f"""
                        <html>
                        <head>
                            <style>
                                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                                .details {{ margin-bottom: 20px; }}
                                .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
                                .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #666; }}
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h1>MyFunZone Booking Receipt</h1>
                                <p>Thank you for choosing us!</p>
                            </div>
                            <div class="details">
                                <h3>Booking Details</h3>
                                <div class="row"><span>Booking ID:</span> <span>#{booking['booking_id']}</span></div>
                                <div class="row"><span>Game:</span> <span>{booking['game_name']}</span></div>
                                <div class="row"><span>Date:</span> <span>{booking['slot_date']}</span></div>
                                <div class="row"><span>Time:</span> <span>{booking['start_time']} - {booking['end_time']}</span></div>
                                <div class="row"><span>Players:</span> <span>{booking['number_of_players']}</span></div>
                            </div>
                            <div class="details">
                                <h3>Payment Information</h3>
                                <div class="row"><span>Amount :</span> <span>₹{booking['amount']}</span></div>
                                <div class="row"><span>Payment Status:</span> <span>{booking.get('payment_status', 'PAID').upper()}</span></div>
                                <div class="row"><span>Booking Status:</span> <span>{booking['status'].upper()}</span></div>
                            </div>
                            <div class="footer">
                                <p>This is a computer-generated receipt.</p>
                                <p>MyFunZone Inc.</p>
                            </div>
                        </body>
                        </html>
                        """
                        st.download_button(
                            label="Download Receipt",
                            data=receipt_html,
                            file_name=f"receipt_booking_{booking['booking_id']}.html",
                            mime="text/html",
                            key=f"receipt_{booking['booking_id']}"
                        )
                    
                    with col2:
                        # Generate QR Display
                        if booking['status'] in ['booked', 'checked_in']:
                            qr_img = generate_qr_code(booking['qr_code'])
                            st.image(f"data:image/png;base64,{qr_img}", caption="Show this QR at entrance")
                            st.write("Copy QR Code text :")
                            st.code(booking['qr_code'], language="text")
                    
                    # Actions (Cancel/Reschedule)
                    if booking['status'] == 'booked':
                        st.markdown("---")
                        ac_col1, ac_col2 = st.columns(2)
                        
                        with ac_col1:
                            if st.button("Cancel Booking", key=f"user_cancel_{booking['booking_id']}"):
                                success, msg = cancel_booking(booking['booking_id'], 'user', current_user['user_id'])
                                if success:
                                    st.session_state.undo_cancel_stack.push(booking['booking_id'])
                                    st.success(msg)
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        
                        with ac_col2:
                            with st.popover("Reschedule"):
                                st.write("Select new date and slot")
                                target_date = st.date_input("New Date", min_value=date.today(), key=f"u_resched_date_{booking['booking_id']}")
                                
                                # Need game_id. bookings query now returns it.
                                if 'game_id' in booking:
                                    available_slots = get_available_slots(booking['game_id'], target_date)
                                    if available_slots:
                                        slot_options = {f"{s['start_time']} - {s['end_time']}": s['slot_id'] for s in available_slots}
                                        selected_slot_str = st.selectbox("Slot", list(slot_options.keys()), key=f"u_resched_slot_{booking['booking_id']}")
                                        
                                        if st.button("Confirm", key=f"u_resched_btn_{booking['booking_id']}"):
                                            new_slot_id = slot_options[selected_slot_str]
                                            success, msg = reschedule_booking(booking['booking_id'], new_slot_id, 'user', current_user['user_id'])
                                            if success:
                                                st.success(msg)
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(msg)
                                    else:
                                        st.warning("No slots available")
                                else:
                                    st.error("Game info missing")
        else:
            st.info("You haven't made any bookings yet.")

    with tab3:
        st.header("My Feedback History")
        reviews = get_user_reviews(current_user['user_id'])
        
        if reviews:
            for review in reviews:
                with st.expander(f"{review['game_name']} - {review['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**Rating:** {'⭐' * review['rating'] if review['rating'] else 'N/A'}")
                    if review['feedback']:
                        st.write(f"**Feedback:** {review['feedback']}")
                    else:
                        st.write("**Feedback:** *No written feedback provided*")
        else:
            st.info("You haven't submitted any feedback yet.")

    with tab4:
        st.header("About Us")
        st.markdown("""
        <style>
        .team-card {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 15px;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .team-card:hover {
            transform: translateY(-5px);
            background-color: rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
            border-color: rgba(0, 180, 216, 0.3);
        }
        .profile-img {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background-color: #2b2b2b;
            margin: 0 auto 15px auto;
            border: 3px solid #00B4D8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: #555;
            overflow: hidden;
        }
        .team-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #00B4D8;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }
        .team-info {
            font-size: 0.9em;
            color: #e0e0e0;
            margin: 6px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .team-contact {
            font-size: 0.85em;
            color: #aaa;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .batch-badge {
            background: linear-gradient(45deg, #FF4B4B, #FF914D);
            color: white;
            padding: 8px 25px;
            border-radius: 20px;
            font-size: 1em;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 30px;
            box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
        }
        </style>
        
        <div style="text-align: center;">
            <span class="batch-badge">Batch: A3</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        
        PROJECT_ROOT = os.path.dirname(BASE_DIR)
        with col1:
            img_link = f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, 'assets', 'henish_photo.jpeg'))}"
            st.markdown(f"""
            <div class="team-card">
                <div class="profile-img">
                    <img src="{img_link}" style="width:100px;height:100px;object-fit:cover;border-radius:50%;" />
                </div>
                <div class="team-name">Bhanderi Henish Hareshbhai</div>
                <div class="team-info"><span>🆔</span> Roll No: 113</div>
                <div class="team-info"><span>🎓</span> Enr: 24002170110015</div>
                <div class="team-contact">
                    <div>📧 henishbhanderi666@gmail.com</div>
                    <div>📱 +91 79843 00079</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            img_src2 = f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(BASE_DIR[0:27], 'assets', 'yashvi_photo.jpeg'))}"
            st.markdown(f"""
            <div class="team-card">
                <div class="profile-img">
                         <img src="{img_src2}" style="width:100px;height:100px;object-fit:cover;border-radius:50%;" />
                        </div>
                <div class="team-name">Ambaliya Yashvi Bharatbhai</div>
                <div class="team-info"><span>🆔</span> Roll No: 99</div>
                <div class="team-info"><span>🎓</span> Enr: 24002170110006</div>
                <div class="team-contact">
                    <div>📧 yashviambaliya14@gmail.com</div>
                    <div>📱 +91 63546 46632</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            img_src = f"data:image/png;base64,{get_base64_of_bin_file(os.path.join(PROJECT_ROOT, 'assets', 'akash_photo.jpg'))}"
            st.markdown(f"""
            <div class="team-card">
                <div class="profile-img">
                    <img src="{img_src}" style="width:100px;height:100px;object-fit:cover;border-radius:50%;" />
                </div>
                <div class="team-name">Dobariya Akash Prafullbhai</div>
                <div class="team-info"><span>🆔</span> Roll No: 103</div>
                <div class="team-info"><span>🎓</span> Enr: 24002170110036</div>
                <div class="team-contact">
                    <div>📧 aakashdobariya99@gmail.com</div>
                    <div>📱 +91 82382 18366</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    render_footer()
