import streamlit as st
import streamlit.components.v1 as components
import os
from src.games import add_game, get_all_games, update_game, deactivate_game, activate_game
from src.slots import create_slot, create_slots_range, get_slots_by_game, delete_slot, toggle_slot_active, get_available_slots
from src.bookings import get_all_bookings, cancel_booking, reschedule_booking, get_revenue_stats, get_cancellation_stats, get_active_users_count, get_peak_hour_insights
from src.session import logout_user_session
from src.issues import get_issue_reports, update_issue_status
from src.auth import add_staff_member
from src.reviews import get_game_reviews, get_game_rating_stats
from src.announcements import create_announcement, get_all_announcements, get_announcement_read_stats
from src.utils import get_base64_of_bin_file, parse_image_urls, render_footer
from datetime import datetime, time, date, timedelta
import random
import string

def generate_temp_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    password += [random.choice(chars) for _ in range(length - 4)]
    random.shuffle(password)
    return "".join(password)

def show_admin_dashboard():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title(f"Welcome , Admin ")
    with col2:
        if st.button("Logout"):
            logout_user_session()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Manage Games", "Manage Slots", "View Bookings", "Analytics", "Issue Reports", "Manage Staff", "Announcements"])

    with tab7:
        st.header("📢 Announcements Management")
        
        # Create Announcement
        with st.expander("➕ Create New Announcement", expanded=True):
            with st.form("create_announcement_form"):
                title = st.text_input("Title", placeholder="e.g., Holiday Schedule Update")
                content = st.text_area("Content", placeholder="Enter announcement details...")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    target_role = st.selectbox("Target Audience", ["staff", "user", "all"], format_func=lambda x: x.capitalize())
                with col2:
                    is_pinned = st.checkbox("📌 Pin to Top")
                with col3:
                    expires_at = st.date_input("Expiration Date (Optional)", value=None, min_value=date.today())
                
                if st.form_submit_button("Publish Announcement"):
                    if not title or not content:
                        st.error("Title and Content are required.")
                    else:
                        success, msg = create_announcement(title, content, target_role, is_pinned, expires_at)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        
        st.divider()
        st.subheader("Existing Announcements")
        
        announcements = get_all_announcements()
        if announcements:
            for ann in announcements:
                status_icon = "🟢" if ann['is_active'] else "🔴"
                pinned_icon = "📌" if ann['is_pinned'] else ""
                
                with st.expander(f"{status_icon} {pinned_icon} {ann['title']} (Target: {ann['target_role'].upper()})"):
                    st.write(f"**Created:** {ann['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    if ann['expires_at']:
                        st.write(f"**Expires:** {ann['expires_at']}")
                    st.write(f"**Content:**")
                    st.info(ann['content'])
                    
                    
                    st.subheader("📊 Read Statistics")
                    stats = get_announcement_read_stats(ann['announcement_id'])
                    
                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        st.metric("Read Count", len(stats['read']))
                        if stats['read']:
                            with st.popover("View Readers"):
                                for reader in stats['read']:
                                    st.write(f"✅ {reader['username']} ({reader['role']}) - {reader['read_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    with s_col2:
                        st.metric("Unread Count", len(stats['unread']))
                        if stats['unread']:
                            with st.popover("View Pending"):
                                for unreader in stats['unread']:
                                    st.write(f"⏳ {unreader['username']} ({unreader['role']})")
        else:
            st.info("No announcements created yet.")

    with tab1:
        st.header("Manage Games")
        
        with st.expander("Add New Game"):
            with st.form("add_game_form"):
                name = st.text_input("Game Name")
                description = st.text_area("Description")
                image_url = st.text_area("Game Images (comma or newline separated URLs)")
                category = st.selectbox("Category", ["Arcade", "Bowling", "VR", "Sports", "Adventure", "Kids", "General"])
                duration = st.number_input("Duration (minutes)", min_value=1, step=1)
                price = st.number_input("Base Price (per person)", min_value=0.0, step=10.0)
                submitted = st.form_submit_button("Add Game")
                
                if submitted:
                    if name and duration > 0 and price >= 0:
                        success, msg = add_game(name, description, image_url, duration, price, category)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Please fill required fields.")
        
        st.subheader("Existing Games")
        games = get_all_games(active_only=False)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.dirname(BASE_DIR)
        for game in games:
            stats = get_game_rating_stats(game['game_id'])
            avg_rating = stats['average_rating']
            total_reviews = stats['total_reviews']
            stars = "⭐" * int(round(avg_rating))
            
            with st.expander(f"{game['name']} ({'Active' if game['is_active'] else 'Inactive'}) - {stars} ({avg_rating:.1f}/5)"):
                col1, col2 = st.columns([2, 3])
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
                            .admin-game-image-wrapper {{
                                position: relative;
                                width: 100%;
                                height: 180px;
                                overflow: hidden;
                                border-radius: 8px;
                            }}
                            .admin-game-image-wrapper img {{
                                width: 100%;
                                height: 100%;
                                object-fit: cover;
                                display: block;
                            }}
                            .admin-game-nav-btn {{
                                position: absolute;
                                top: 50%;
                                transform: translateY(-50%);
                                background: rgba(0,0,0,0.45);
                                border: none;
                                color: #ffffff;
                                font-size: 16px;
                                width: 30px;
                                height: 30px;
                                border-radius: 50%;
                                cursor: pointer;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            }}
                            .admin-game-nav-btn.left {{
                                left: 8px;
                            }}
                            .admin-game-nav-btn.right {{
                                right: 8px;
                            }}
                            </style>
                            <div class="admin-game-image-wrapper">
                                <img id="admin_game_{game_id}_img" src="{first_src}">
                                <button class="admin-game-nav-btn left" onclick="prevAdminGameImg_{game_id}()">◀</button>
                                <button class="admin-game-nav-btn right" onclick="nextAdminGameImg_{game_id}()">▶</button>
                            </div>
                            <script>
                            (function() {{
                                const images = {js_array};
                                let idx = 0;
                                const imgEl = document.getElementById('admin_game_{game_id}_img');
                                window.prevAdminGameImg_{game_id} = function() {{
                                    idx = (idx - 1 + images.length) % images.length;
                                    imgEl.src = images[idx];
                                }};
                                window.nextAdminGameImg_{game_id} = function() {{
                                    idx = (idx + 1) % images.length;
                                    imgEl.src = images[idx];
                                }};
                            }})();
                            </script>
                            """
                            components.html(html, height=190)
                        else:
                            st.write("🖼️ No Image")
                    else:
                        st.write("🖼️ No Image")
                with col2:
                    st.write(f"**Description:** {game['description']}")
                    st.write(f"**Duration:** {game['duration_minutes']} mins | **Price:** ₹{game['base_price']}")
                    st.write(f"**Overall Rating:** {stars} **{avg_rating:.1f}** / 5 ({total_reviews} reviews)")
                    with st.popover("Update Details"):
                        st.write("Update game information")
                        with st.form(key=f"update_game_form_{game['game_id']}"):
                            u_name = st.text_input("Name", value=game['name'])
                            u_desc = st.text_area("Description", value=game['description'])
                            u_img = st.text_area("Game Images (comma or newline separated URLs)", value=game['image_url'])
                            
                            current_cat = game.get('category', 'General')
                            cat_options = ["Arcade", "Bowling", "VR", "Sports", "Adventure", "Kids", "General"]
                            if current_cat not in cat_options:
                                cat_options.append(current_cat)
                            u_cat = st.selectbox("Category", cat_options, index=cat_options.index(current_cat) if current_cat in cat_options else 0)
                            
                            u_dur = st.number_input("Duration (min)", value=game['duration_minutes'], min_value=1, step=1)
                            u_price = st.number_input("Price (₹)", value=float(game['base_price']), step=5.0)
                            
                            if st.form_submit_button("Save Changes"):
                                success, msg = update_game(
                                    game['game_id'], 
                                    u_name, 
                                    u_desc, 
                                    u_img, 
                                    u_dur, 
                                    u_price, 
                                    game['is_active'],
                                    u_cat
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                    if game['is_active']:
                        if st.button("Deactivate", key=f"deactivate_{game['game_id']}", type="primary"):
                            deactivate_game(game['game_id'])
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"activate_{game['game_id']}"):
                            activate_game(game['game_id'])
                            st.rerun()

                st.markdown("---")
                st.subheader("User Reviews")
                
                limit_key = f"review_limit_{game['game_id']}"
                if limit_key not in st.session_state:
                    st.session_state[limit_key] = 10
                
                current_limit = st.session_state[limit_key]
                reviews = get_game_reviews(game['game_id'], limit=current_limit)
                
                if reviews:
                    for review in reviews:
                        with st.container():
                            r_col1, r_col2 = st.columns([1, 5])
                            with r_col1:
                                st.write(f"**{review['username']}**")
                                st.caption(f"{review['created_at'].strftime('%Y-%m-%d')}")
                            with r_col2:
                                r_stars = "⭐" * review['rating'] if review['rating'] else "N/A"
                                st.write(f"{r_stars}")
                                if review['feedback']:
                                    st.write(f"_{review['feedback']}_")
                            st.divider()
                    
                    if total_reviews > current_limit:
                        if st.button("Show More Reviews", key=f"more_reviews_{game['game_id']}"):
                            st.session_state[limit_key] += 10
                            st.rerun()
                else:
                    st.info("No reviews yet.")

    with tab2:
        st.header("Manage Slots")
        
        games = get_all_games(active_only=True)
        game_options = {g['name']: g['game_id'] for g in games}
        
        selected_game_name = st.selectbox("Select Game", list(game_options.keys()))
        
        if selected_game_name:
            selected_game_id = game_options[selected_game_name]
            
        # Need to fetch full game object to get price
        selected_game = next((g for g in games if g['game_id'] == selected_game_id), None)
        
        if selected_game:
            # Create Slot
            with st.form("create_slot_form"):
                st.subheader(f"Create Slots for {selected_game_name}")
                st.info(f"Using Base Price: ₹{selected_game['base_price']} (Inc. GST) from Game Details")
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    start_date = st.date_input("From Date", min_value=datetime.today(), value=datetime.today())
                with col_d2:
                    end_date = st.date_input("To Date", min_value=datetime.today(), value=datetime.today())

                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.time_input("Start Time", value=time(10, 0))
                with col2:
                    end_time = st.time_input("End Time", value=time(11, 0))
                
                max_players = st.number_input("Max Players", min_value=1, value=10)
                is_active = st.checkbox("Active (Visible to Users)", value=True)
                
                submitted = st.form_submit_button("Create Slots")
                
                if submitted:
                    if start_date > end_date:
                        st.error("End Date must be after Start Date")
                    else:
                        price = float(selected_game['base_price'])
                        success, msg = create_slots_range(selected_game_id, start_date, end_date, start_time, end_time, max_players, price, is_active)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
            
            # List Existing Slots
            st.subheader("Existing Slots")
            
            use_date_filter = st.checkbox("Filter by Date", value=False, key="use_slot_filter")
            filter_date = None
            if use_date_filter:
                filter_date = st.date_input("Select Date", value=date.today(), key="slot_filter_date")
            
            slots = get_slots_by_game(selected_game_id, filter_date)
            
            if slots:
                for slot in slots:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                    with col1:
                        st.write(f"📅 {slot['slot_date']}")
                    with col2:
                        st.write(f"⏰ {slot['start_time']} - {slot['end_time']}")
                    with col3:
                        st.write(f"💰 ₹{slot['price']}")
                    with col4:
                        is_active = slot.get('is_active', True)
                        new_active = st.checkbox("Active", value=is_active, key=f"active_{slot['slot_id']}")
                        if new_active != is_active:
                            toggle_slot_active(slot['slot_id'], new_active)
                            st.rerun()
                    with col5:
                        if st.button("🗑️", key=f"del_slot_{slot['slot_id']}", type="primary"):
                            delete_slot(slot['slot_id'])
                            st.rerun()
            else:
                st.info("No slots found.")

    with tab3:
        st.header("All Bookings")
        
        use_booking_filter = st.checkbox("Filter by Date Range", value=False, key="use_booking_filter")
        start_date_filter = None
        end_date_filter = None
        
        if use_booking_filter:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                start_date_filter = st.date_input("Start Date", value=date.today() - timedelta(days=7), key="booking_filter_start")
            with col_f2:
                end_date_filter = st.date_input("End Date", value=date.today(), key="booking_filter_end")
            
        bookings = get_all_bookings(start_date_filter, end_date_filter)
        
        if bookings:
            for booking in bookings:
                with st.expander(f"Booking #{booking['booking_id']} - {booking['username']} - {booking['game_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date:** {booking['slot_date']}")
                        st.write(f"**Time:** {booking['start_time']} - {booking['end_time']}")
                        st.write(f"**Status:** {booking['status'].upper()}")
                        st.write(f"**Payment Status:** {booking.get('payment_status', 'N/A').upper()}")
                    with col2:
                        st.write(f"**User:** {booking['username']}")
                        st.write(f"**Players:** {booking['number_of_players']}")
                        st.write(f"**Amount:** ₹{booking['amount']}")
                    
                    # Actions
                    if booking['status'] == 'booked':
                        st.markdown("---")
                        ac_col1, ac_col2 = st.columns(2)
                        with ac_col1:
                            if st.button("Cancel Booking", key=f"admin_cancel_{booking['booking_id']}"):
                                success, msg = cancel_booking(booking['booking_id'], 'admin')
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        
                        with ac_col2:
                            # Reschedule UI
                            st.write("**Reschedule**")
                            # Fetch available slots for this game
                            game_id = booking['game_id']
                            target_date = st.date_input("New Date", min_value=date.today(), key=f"resched_date_{booking['booking_id']}")
                            available_slots = get_available_slots(game_id, target_date)
                            
                            if available_slots:
                                slot_options = {f"{s['start_time']} - {s['end_time']}": s['slot_id'] for s in available_slots}
                                selected_slot_str = st.selectbox("Select New Slot", list(slot_options.keys()), key=f"resched_slot_{booking['booking_id']}")
                                
                                if st.button("Confirm Reschedule", key=f"resched_btn_{booking['booking_id']}"):
                                    new_slot_id = slot_options[selected_slot_str]
                                    success, msg = reschedule_booking(booking['booking_id'], new_slot_id, 'admin')
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            else:
                                st.warning("No slots available on this date.") 

    with tab4: 
        st.header("Analytics & Reports")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            start_date_analytics = st.date_input("Start Date", value=date.today() - timedelta(days=30), key="analytics_start")
        with col_a2:
            end_date_analytics = st.date_input("End Date", value=date.today(), key="analytics_end")
            
        if start_date_analytics > end_date_analytics:
            st.error("Start date must be before end date")
        else:
            # Fetch Data
            revenue_data = get_revenue_stats(start_date_analytics, end_date_analytics)
            cancel_data = get_cancellation_stats(start_date_analytics, end_date_analytics)
            active_users = get_active_users_count(start_date_analytics, end_date_analytics)
            peak_hours = get_peak_hour_insights(start_date_analytics, end_date_analytics)
            
            # Key Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Revenue", f"₹{revenue_data['total_revenue']:,.2f}")
            with m2:
                st.metric("Total Bookings", cancel_data['total_bookings'])
            with m3:
                st.metric("Active Users", active_users)
            with m4:
                st.metric("Cancellation Rate", f"{cancel_data['cancellation_rate']}%")
                
            st.markdown("---")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Revenue Chart
                st.subheader("Revenue Over Time")
                if revenue_data['daily_revenue']:
                    chart_data = {item['date']: item['revenue'] for item in revenue_data['daily_revenue']}
                    st.bar_chart(chart_data)
                else:
                    st.info("No revenue data for this period.")
            
            with col_chart2:
                # Peak Hours Chart
                st.subheader("Peak Booking Hours")
                if peak_hours:
                    # Format for chart: {Hour: Count}
                    peak_data = {f"{item['hour']:02d}:00": item['count'] for item in peak_hours}
                    st.bar_chart(peak_data)
                else:
                    st.info("No peak hour data available.")
                
            # Cancellation Details
            st.markdown("---")
            st.subheader("Cancellation Summary")
            st.write(f"**Cancelled Bookings:** {cancel_data['cancelled_bookings']}")
            st.write(f"**Total Bookings:** {cancel_data['total_bookings']}")

    with tab5:
        st.header("Issue Reports")
        filter_status = st.selectbox("Filter Status", ["All", "open", "in_progress", "resolved"])
        reports = get_issue_reports(None if filter_status == "All" else filter_status)
        
        if reports:
            for report in reports:
                with st.expander(f"{report['game_name']} - {report['reported_at']}"):
                    st.write(f"**Reported By:** {report['staff_name']}")
                    st.write(f"**Description:** {report['description']}")
                    st.write(f"**Current Status:** {report['status']}")
                    
                    new_status = st.selectbox("Update Status", ["open", "in_progress", "resolved"], key=f"status_{report['issue_report_id']}", index=["open", "in_progress", "resolved"].index(report['status']))
                    if new_status != report['status']:
                        if st.button("Update", key=f"update_rep_{report['issue_report_id']}"):
                            update_issue_status(report['issue_report_id'], new_status)
                            st.rerun()
        else:
            st.info("No reports found.")

    with tab6:
        st.header("Manage Staff")
        
        st.subheader("Add New Staff Member")
        with st.form("add_staff_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_phone = st.text_input("Phone Number")
            new_role = st.selectbox("Role", ["staff", "admin"])
            
            submitted = st.form_submit_button("Add Staff")
            
            if submitted:
                if new_username and new_email and new_phone:
                    temp_password = generate_temp_password()
                    success, msg = add_staff_member(new_username, new_email, new_phone, new_role, temp_password)
                    
                    if success:
                        st.success("Staff member added successfully!")
                        st.info(f"**Temporary Password:** `{temp_password}`")
                        st.warning("Please share this password securely. The user will be required to change it on first login.")
                    else:
                        st.error(msg)
                else:
                    st.error("Please fill in all fields.")

    render_footer()
