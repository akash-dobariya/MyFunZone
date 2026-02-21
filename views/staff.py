import streamlit as st
from src.bookings import check_in_user, get_all_bookings, update_booking_status
from src.session import logout_user_session, get_current_user
from src.games import get_all_games
from src.slots import get_slots_by_game, toggle_slot_active
from src.issues import create_issue_report, get_issue_reports, update_issue_status
from src.announcements import get_announcements_for_role, mark_announcement_as_read
from datetime import datetime, date
import time
from src.utils import Queue, render_footer

def show_staff_dashboard():
    current_user = get_current_user()
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title(f"Welcome, {current_user['username']}")
    with col2:
        if st.button("Logout"):
            logout_user_session()
            
    # Announcements Section (Pinned / Unread)
    announcements = get_announcements_for_role('staff', current_user['user_id'])
    
    if announcements:
        unread_count = sum(1 for a in announcements if not a['is_read'])
        
        # Section Header
        section_title = "📢 Announcements"
        if unread_count > 0:
            section_title += f" ({unread_count} New)"
        
        with st.expander(section_title, expanded=(unread_count > 0)):
            if unread_count > 0:
                st.warning(f"You have {unread_count} unread announcement(s).")
                
            for ann in announcements:
                # Show unread or pinned ones 
                pinned_icon = "📌" if ann['is_pinned'] else ""
                status_color = "red" if not ann['is_read'] else "green"
                status_text = "NEW" if not ann['is_read'] else "Read"
                
           
                with st.container(border=True):
                    col_header, col_badge = st.columns([4, 1])
                    with col_header:
                        st.markdown(f"**{pinned_icon} {ann['title']}**")
                    with col_badge:
                        st.markdown(f":{status_color}[**{status_text}**]")
                    
                    st.write(ann['content'])
                    st.caption(f"Posted: {ann['created_at'].strftime('%Y-%m-%d')}")
                    
                    if not ann['is_read']:
                        if st.button("✅ Mark as Read", key=f"read_{ann['announcement_id']}"):
                            if mark_announcement_as_read(ann['announcement_id'], current_user['user_id']):
                                st.success("Marked as read!")
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info("No announcements.")
        
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["QR Check-in", "Today's Bookings", "Maintenance & Issues"])
    
    with tab1:
        st.header("QR Check-in Scanner")
        
       
        qr_input = st.text_input("Scan QR Code (Simulate by entering code)", help="In a real app, this would use the camera.")
        
        if st.button("Check-in"):
            if qr_input:
                # assume qr string checks 
                success, msg = check_in_user(qr_input, current_user['user_id'])
                if success:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("Please scan/enter a QR code.")

    with tab2:
        st.header("Today's Schedule")
        
        today = date.today()
        bookings = get_all_bookings(today)
        
        if bookings:
            for booking in bookings:
                with st.expander(f"{booking['start_time']} - {booking['game_name']} ({booking['status']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Customer:** {booking['username']}")
                        st.write(f"**Players:** {booking['number_of_players']}")
                        st.write(f"**QR Code:** {booking['qr_code']}")
                    
                    with col2:
                        if booking['status'] == 'booked':
                            if st.button("Mark No-Show", key=f"ns_{booking['booking_id']}"):
                                update_booking_status(booking['booking_id'], 'no_show')
                                st.rerun()
                        elif booking['status'] == 'checked_in':
                            if st.button("Mark Completed", key=f"comp_{booking['booking_id']}"):
                                update_booking_status(booking['booking_id'], 'completed')
                                st.rerun()
                        else:
                            st.write(f"**{booking['status'].upper()}**")
        else:
            st.info("No bookings scheduled for today.")

    with tab3:
        st.header("Maintenance & Issues")
        
        if 'issue_queue' not in st.session_state:
            st.session_state.issue_queue = Queue()

        st.subheader("Issue Queue (FIFO)")
        open_issues = get_issue_reports(status_filter='open')
        if open_issues:
            if st.button("Load open issues into queue"):
                queue_instance = Queue()
                for issue in open_issues:
                    queue_instance.enqueue(issue)
                st.session_state.issue_queue = queue_instance

            if st.button("Next Issue"):
                current_issue = st.session_state.issue_queue.dequeue()
                if current_issue:
                    st.write(f"Issue ID: {current_issue['issue_report_id']}")
                    st.write(f"Game: {current_issue.get('game_name')}")
                    st.write(f"Reported by: {current_issue.get('staff_name')}")
                    st.write(f"Description: {current_issue['description']}")
                    updated, msg = update_issue_status(current_issue['issue_report_id'], 'in_progress')
                    if updated:
                        st.info("Marked as in progress.")
                    else:
                        st.error(msg)
                else:
                    st.info("No more issues in queue.")
        else:
            st.info("No open issues to load into queue.")
        
        st.subheader("Report Issue")
        with st.form("report_issue_form"):
            games = get_all_games(active_only=True)
            game_options = {g['name']: g['game_id'] for g in games}
            
            selected_game_name = st.selectbox("Select Game", list(game_options.keys()))
            description = st.text_area("Issue Description (e.g., 'Lane 3 stuck', 'Monitor broken')")
            
            if st.form_submit_button("Submit Report"):
                if selected_game_name and description:
                    game_id = game_options[selected_game_name]
                    success, msg = create_issue_report(current_user['user_id'], game_id, description)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all fields.")
        
        st.markdown("---")
        st.subheader("Lock Slot (Emergency Only)")
        st.info("Use this to quickly block a slot if equipment fails.")
        
        selected_game_lock = st.selectbox("Select Game to Lock", list(game_options.keys()), key="lock_game")
        
        if selected_game_lock:
            game_id_lock = game_options[selected_game_lock]
            slots = get_slots_by_game(game_id_lock)
            
            # Filter for today/future slots only
            future_slots = [s for s in slots if s['slot_date'] >= date.today() and s['is_active']]
            
            if future_slots:
                slot_opts = {f"{s['slot_date']} @ {s['start_time']}": s['slot_id'] for s in future_slots}
                selected_slot_str = st.selectbox("Select Slot to Lock", list(slot_opts.keys()))
                
                if st.button("LOCK SLOT", type="primary"):
                    slot_id_lock = slot_opts[selected_slot_str]
                    toggle_slot_active(slot_id_lock, False)
                    st.success("Slot locked successfully.")
                    st.rerun()
            else:
                st.info("No active upcoming slots found for this game.")

    render_footer()
