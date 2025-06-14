// home/static/assets/js/portal_script.js
document.addEventListener('DOMContentLoaded', function() {
    const pageContent = document.getElementById('pageContent');
    const pageTitle = document.getElementById('pageTitle');
    
    const communicationTemplates = {
        sms: `
             <div class="chat-area">
                 <div class="card-header">
                    <div class="client-info">
                        <div class="client-avatar">JS</div>
                        <div>
                            <div class="client-name">John Smith</div>
                            <div class="client-email">+1 (555) 123-4567</div>
                        </div>
                    </div>
                </div>
                <div class="chat-window">
                    <div class="chat-message incoming">This is an SMS reminder for your appointment.</div>
                    <div class="chat-message outgoing">Great, thank you!</div>
                </div>
                <div class="message-input-area">
                    <textarea placeholder="Type an SMS..."></textarea>
                    <button class="primary-button icon-button" title="Send SMS">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </button>
                </div>
            </div>
        `,
        appMessage: `
            <div class="chat-area">
                 <div class="card-header">
                    <div class="client-info">
                        <div class="client-avatar">JS</div>
                        <div>
                            <div class="client-name">John Smith</div>
                            <div class="client-email">In-App Message</div>
                        </div>
                    </div>
                </div>
                <div class="chat-window">
                    <div class="chat-message incoming">Hi John, this is a reminder for your appointment tomorrow at 10 AM.</div>
                    <div class="chat-message outgoing">Thanks for the reminder!</div>
                    <div class="chat-message incoming">You're welcome. Please let us know if you have any questions.</div>
                    <div class="chat-message outgoing">Sounds good! See you then.</div>
                </div>
                <div class="message-input-area">
                    <button class="icon-button" title="Attach File">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
                    </button>
                    <textarea placeholder="Type a message..."></textarea>
                    <button class="primary-button icon-button" title="Send Message">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </button>
                </div>
            </div>
        `,
        videoCall: `
            <div class="video-call-layout">
                <div class="main-video-area">
                    <div class="video-placeholder">
                        <div class="client-avatar-large">JS</div>
                        <span>Connecting to John Smith...</span>
                    </div>
                    <div class="self-view-placeholder"></div>
                </div>
                <div class="video-controls">
                    <button class="icon-button" title="Mute/Unmute"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5z"></path><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg></button>
                    <button class="icon-button danger-button" title="End Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.68 13.31a16 16 0 0 0 3.41 2.34l3.1-3.1a2 2 0 0 1 2.83 0l2.17 2.17a2 2 0 0 1 0 2.83l-3.44 3.44a16 16 0 0 1-13.19-2.28 16 16 0 0 1-5.64-13.19A16 16 0 0 1 4.9 2.18a2 2 0 0 1 2.83 0l2.17 2.17a2 2 0 0 1 0 2.83L8.68 8.41"></path></svg></button>
                    <button class="icon-button" title="Turn Camera Off/On"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1,1l22,22"></path><path d="M21,21H3a2,2,0,0,1-2-2V8a2,2,0,0,1,2-2H8"></path><path d="M12.78,10.78a2,2,0,0,0-2.56-2.56"></path><path d="M12,18a6,6,0,0,1-6-6"></path><path d="M18,12a6,6,0,0,0-1.07-3.39"></path></svg></button>
                </div>
            </div>
        `
    };

    const contentTemplates = {
        Dashboards: `
            <p class="page-description">Manage your appointments and clients</p>
            <div class="grid grid-cols-4">
                <div class="summary-card card"><div class="label">Total Clients</div><div class="value">10</div><div class="change">+1 This Month</div></div>
                <div class="summary-card card"><div class="label">Total Appointments</div><div class="value">29</div><div class="change">+1 Booked This Month</div></div>
                <div class="summary-card card"><div class="label">Monthly Revenue</div><div class="value">$0</div><div class="change">$0.0/day This Month</div></div>
                <div class="summary-card card"><div class="label">Client Growth</div><div class="value">10%</div><div class="change">+1 This Month</div></div>
            </div>
            <div class="grid grid-cols-2" style="margin-top: 1.5rem;">
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">Appointment Activity</h3><select class="button" style="background:var(--background-card); color:var(--text-primary); border:1px solid var(--border-color); height:38px; border-radius:0.5rem;"><option>Last 7 days</option><option>Last 30 days</option></select></div>
                     <div class="chart-placeholder"><svg width="100%" height="100%" viewBox="0 0 300 150" preserveAspectRatio="none"><path d="M 0,130 C 50,10, 100,20, 150,80 S 250,140, 300,120" stroke="#4f46e5" fill="none" stroke-width="2"/></svg></div>
                 </div>
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">Revenue Breakdown</h3></div>
                     <ul class="revenue-list">
                         <li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-1);"></span> Session</div><div class="amount">$0</div></li>
                         <li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-2);"></span> Group</div><div class="amount">$0</div></li>
                          <li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-3);"></span> Individual</div><div class="amount">$0</div></li>
                     </ul>
                 </div>
            </div>
            <div class="grid grid-cols-2" style="margin-top: 1.5rem;">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Upcoming Appointments</h3><a href="#" style="font-size: 0.9rem; color: var(--primary-accent); text-decoration: none; font-weight: 600;">View All</a></div>
                    <div style="text-align: center; padding: 3rem 0; color: var(--text-secondary);">No upcoming appointments</div>
                </div>
                <div class="card">
                    <div class="card-header"><div class="dash-calendar-nav"><button class="dash-cal-nav-btn">&lt;</button><h3 class="card-title">June 2025</h3><button class="dash-cal-nav-btn">&gt;</button></div></div>
                    <div class="dash-calendar"><div class="dash-calendar-header"><div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div></div><div class="dash-calendar-body"><div>1</div><div>2</div><div>3</div><div>4</div><div>5</div><div>6</div><div>7</div><div>8</div><div>9</div><div>10</div><div class="today">11</div><div>12</div><div>13</div><div>14</div><div>15</div><div>16</div><div>17</div><div>18</div><div>19</div><div>20</div><div>21</div><div>22</div><div>23</div><div>24</div><div>25</div><div>26</div><div>27</div><div>28</div><div>29</div><div>30</div></div></div>
                </div>
            </div>
            <div class="card" style="margin-top: 1.5rem;">
                 <div class="card-header"><h3 class="card-title">Recent Clients</h3></div>
                 <table class="client-table"><thead><tr><th>Client</th><th>Status</th><th>Last Session</th><th>Next Session</th></tr></thead><tbody><tr><td><div class="client-info"><div class="client-avatar">JJ</div><div><div class="client-name">Jagsharan Jagsharan</div><div class="client-email">to@jagshrn.com</div></div></div></td><td><span class="status-badge active">Active</span></td><td>Jun 03, 2025</td><td>Not Scheduled</td></tr><tr><td><div class="client-info"><div class="client-avatar" style="background-color: #fee2e2; color: #b91c1c;">XL</div><div><div class="client-name">xiu lan</div><div class="client-email">xiulan@jpsk.me</div></div></div></td><td><span class="status-badge active">Active</span></td><td>May 31, 2025</td><td>Not Scheduled</td></tr><tr><td><div class="client-info"><div class="client-avatar" style="background-color: #ffedd5; color: #9a3412;">KJ</div><div><div class="client-name">kanee joy</div><div class="client-email">kennie@gmail.com</div></div></div></td><td><span class="status-badge active">Active</span></td><td>Mar 07, 2025</td><td>Not Scheduled</td></tr></tbody></table>
            </div>
        `,
        Communications: `
             <div class="communications-layout">
                <div class="conversation-sidebar">
                    <div class="card-header" style="padding: 1.5rem; border-bottom-width: 1px; margin-bottom: 0;">
                        <div class="search-bar" style="width: 100%;">
                           <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                           <input type="text" placeholder="Search conversations..." style="width: 100%;">
                        </div>
                    </div>
                    <div class="conversation-list">
                        <div class="conversation-item active">
                            <div class="conversation-item-header">
                                <div class="name">John Smith</div>
                                <div class="conversation-actions">
                                    <button class="icon-button" data-action="appMessage" title="In-App Message"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></button>
                                    <button class="icon-button active" data-action="sms" title="SMS"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3h-4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></button>
                                    <button class="icon-button" data-action="videoCall" title="Video Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></button>
                                </div>
                            </div>
                            <div class="snippet">Sounds good! See you then.</div>
                        </div>
                        <div class="conversation-item">
                            <div class="conversation-item-header">
                                <div class="name">Jane Doe</div>
                                <div class="conversation-actions">
                                    <button class="icon-button" data-action="appMessage" title="In-App Message"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></button>
                                    <button class="icon-button" data-action="sms" title="SMS"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3h-4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></button>
                                    <button class="icon-button" data-action="videoCall" title="Video Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></button>
                                </div>
                            </div>
                            <div class="snippet">Can I reschedule for next week?</div>
                        </div>
                    </div>
                </div>
                <div id="communication-content-area">
                   <!-- Dynamic content will be loaded here -->
                </div>
            </div>
        `,
        Calendar: `
            <div class="card">
                <div class="calendar-toolbar">
                    <div class="staff-filters">
                        <button class="button active" data-staff-filter="all"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg><span>All Staff</span></button>
                        <button class="button" data-staff-filter="smith"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"></circle><path d="M12 14c-2.21 0-4 1.79-4 4v2h8v-2c0-2.21-1.79-4-4-4z"></path></svg><span>Dr. Smith</span></button>
                        <button class="button" data-staff-filter="doe"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"></circle><path d="M12 14c-2.21 0-4 1.79-4 4v2h8v-2c0-2.21-1.79-4-4-4z"></path></svg><span>Jane Doe</span></button>
                    </div>
                    <div class="calendar-nav-controls">
                       <button class="icon-button" id="cal-prev-month" title="Previous Month"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg></button>
                       <h3 class="calendar-title" id="calendar-month-year"></h3>
                       <button class="icon-button" id="cal-next-month" title="Next Month"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg></button>
                       <button class="button" id="cal-today">Today</button>
                    </div>
                     <div class="calendar-legend">
                        <div class="legend-item"><span class="dot" style="background-color: var(--event-color-1);"></span> Session</div>
                        <div class="legend-item"><span class="dot" style="background-color: var(--event-color-2);"></span> Group</div>
                        <div class="legend-item"><span class="dot" style="background-color: var(--event-color-3);"></span> Individual</div>
                     </div>
                </div>
                <div class="calendar-container">
                    <div class="calendar-grid">
                        <div class="calendar-day-header">Sun</div><div class="calendar-day-header">Mon</div><div class="calendar-day-header">Tue</div><div class="calendar-day-header">Wed</div><div class="calendar-day-header">Thu</div><div class="calendar-day-header">Fri</div><div class="calendar-day-header">Sat</div>
                    </div>
                    <div class="calendar-grid" id="calendar-body"></div>
                </div>
            </div>
        `,
        Appointments: `
            <div class="page-toolbar">
                <div class="page-tabs">
                   <button class="button active" data-tab="appointments">Appointments</button>
                   <button class="button" data-tab="services">Services</button>
                </div>
                <div class="search-bar">
                   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                   <input type="text" placeholder="Search appointments...">
                </div>
            </div>

            <div id="appointments" class="tab-content active">
                <div class="card">
                   <div class="card-header"><h3 class="card-title">All Appointments</h3></div>
                   <table class="client-table">
                       <thead><tr><th>Date & Time</th><th>Client</th><th>Type</th><th>Status</th></tr></thead>
                       <tbody>
                           <tr>
                               <td>June 13, 2025, 3:00 PM</td>
                               <td><div class="client-info"><div class="client-avatar" style="background-color: #fee2e2; color: #b91c1c;">JD</div><div><div class="client-name">Jane Doe</div></div></div></td>
                               <td>Workshop</td>
                               <td><span class="status-badge upcoming">Upcoming</span></td>
                           </tr>
                           <tr>
                               <td>June 11, 2025, 9:00 AM</td>
                               <td><div class="client-info"><div class="client-avatar" style="background-color: #e0e7ff; color: #4338ca;">JS</div><div><div class="client-name">John Smith</div></div></div></td>
                               <td>Check-in</td>
                               <td><span class="status-badge active">Completed</span></td>
                           </tr>
                       </tbody>
                   </table>
                </div>
            </div>

            <div id="services" class="tab-content">
                <div class="card">
                   <div class="card-header">
                       <h3 class="card-title">Manage Services</h3>
                       <button class="primary-button" id="addNewServiceBtn"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>Add New Service</button>
                   </div>
                   <table class="client-table">
                        <thead><tr><th>Service Name</th><th>Duration</th><th>Practitioner</th></tr></thead>
                        <tbody>
                            <tr><td>Initial Consultation</td><td>60 min</td><td>Dr. Smith</td></tr>
                            <tr><td>Follow-up</td><td>30 min</td><td>Any</td></tr>
                        </tbody>
                   </table>
                </div>
            </div>
        `,
        Clients: `
            <div class="page-toolbar">
                <div class="page-tabs">
                   <button class="button active" data-tab="clientList">All Clients</button>
                   <button class="button" data-tab="addClient">Add New Client</button>
                </div>
                <div class="search-bar">
                   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                   <input type="text" placeholder="Search clients...">
                </div>
            </div>
            <div id="clientList" class="tab-content active">
                <div class="client-grid">
                    <div class="card client-card-item">
                        <div class="client-info">
                            <div class="client-avatar">JJ</div>
                            <div>
                                <div class="client-name">Jagsharan Jagsharan</div>
                                <div class="client-email">to@jagshrn.com</div>
                            </div>
                        </div>
                        <div class="client-card-actions">
                            <button class="icon-button" data-action="view-info" title="View Information"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></button>
                            <button class="icon-button" data-action="video-call" title="Video Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></button>
                            <button class="icon-button" data-action="sms" title="SMS"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3h-4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></button>
                            <button class="icon-button" data-action="app-message" title="In-App Message"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></button>
                        </div>
                    </div>
                     <div class="card client-card-item">
                        <div class="client-info">
                            <div class="client-avatar" style="background-color: #fee2e2; color: #b91c1c;">XL</div>
                            <div>
                                <div class="client-name">Xiu Lan</div>
                                <div class="client-email">xiulan@jpsk.me</div>
                            </div>
                        </div>
                        <div class="client-card-actions">
                            <button class="icon-button" data-action="view-info" title="View Information"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></button>
                            <button class="icon-button" data-action="video-call" title="Video Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></button>
                            <button class="icon-button" data-action="sms" title="SMS"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3h-4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></button>
                            <button class="icon-button" data-action="app-message" title="In-App Message"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></button>
                        </div>
                    </div>
                     <div class="card client-card-item">
                        <div class="client-info">
                            <div class="client-avatar" style="background-color: #ffedd5; color: #9a3412;">KJ</div>
                            <div>
                                <div class="client-name">Kanee Joy</div>
                                <div class="client-email">kennie@gmail.com</div>
                            </div>
                        </div>
                        <div class="client-card-actions">
                            <button class="icon-button" data-action="view-info" title="View Information"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></button>
                            <button class="icon-button" data-action="video-call" title="Video Call"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></button>
                            <button class="icon-button" data-action="sms" title="SMS"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3h-4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></button>
                            <button class="icon-button" data-action="app-message" title="In-App Message"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg></button>
                        </div>
                    </div>
                </div>
            </div>
            <div id="addClient" class="tab-content">
                <div class="card">
                   <div class="card-header"><h3 class="card-title">Add New Client</h3></div>
                   <h4 style="margin-top: 1rem; margin-bottom: 1rem; font-size: 1.1rem;">Personal Information</h4>
                   <div class="form-grid">
                       <div class="form-group"><label for="client-name">Full Name</label><input type="text" id="client-name"></div>
                       <div class="form-group"><label for="client-dob">Date of Birth</label><input type="date" id="client-dob"></div>
                       <div class="form-group"><label for="client-phone">Phone Number</label><input type="tel" id="client-phone"></div>
                       <div class="form-group"><label for="client-email">Email Address</label><input type="email" id="client-email"></div>
                   </div>
                   <div class="form-group" style="margin-top: 1.5rem;"><label for="client-address">Address</label><input type="text" id="client-address"></div>
                   <h4 style="margin-top: 2rem; margin-bottom: 1rem; font-size: 1.1rem;">Emergency Contact</h4>
                   <div class="form-grid">
                       <div class="form-group"><label for="e-contact-name">Contact Name</label><input type="text" id="e-contact-name"></div>
                       <div class="form-group"><label for="e-contact-phone">Contact Phone</label><input type="tel" id="e-contact-phone"></div>
                   </div>
                   <h4 style="margin-top: 2rem; margin-bottom: 1rem; font-size: 1.1rem;">Medical History & Records</h4>
                   <div class="form-grid">
                        <div class="form-group"><label for="med-allergies">Allergies</label><textarea id="med-allergies"></textarea></div>
                        <div class="form-group"><label for="med-medications">Current Medications</label><textarea id="med-medications"></textarea></div>
                   </div>
                   <div class="form-group" style="margin-top: 1.5rem;"><label for="med-conditions">Existing Conditions</label><textarea id="med-conditions"></textarea></div>
                   <div class="form-group" style="margin-top: 1.5rem;"><label for="med-notes">Session Notes / Records</label><textarea id="med-notes" placeholder="Add new session notes here..."></textarea></div>
                   <div class="form-actions"><button class="primary-button">Add Client</button></div>
                </div>
            </div>
        `,
        'AI Voice Assistant': `
            <div class="page-toolbar">
                <div class="page-tabs">
                   <button class="button active" data-tab="ai-overview">Overview</button>
                   <button class="button" data-tab="ai-numbers">Phone Numbers</button>
                   <button class="button" data-tab="ai-knowledge">Knowledge Base</button>
                   <button class="button" data-tab="ai-logs">Call Logs</button>
                   <button class="button" data-tab="ai-settings">Settings</button>
                </div>
            </div>
            <div id="ai-overview" class="tab-content active">
                <div class="grid grid-cols-4">
                    <div class="summary-card card">
                        <div class="label">Agent Status</div>
                        <div class="toggle-switch" style="margin-top: 0.5rem;"><label class="switch"><input type="checkbox" checked> <span class="slider"></span></label> <span>Active</span></div>
                    </div>
                    <div class="summary-card card"><div class="label">Active Phone Number</div><div class="value">+1 (555) 123-4567</div></div>
                    <div class="summary-card card"><div class="label">Calls Today</div><div class="value">24</div></div>
                    <div class="summary-card card"><div class="label">Avg. Call Duration</div><div class="value">1m 45s</div></div>
                </div>
            </div>
             <div id="ai-numbers" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Manage Phone Numbers</h3><button class="primary-button" id="buyNewNumberBtn"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>Buy New Number</button></div>
                    <table class="client-table"><thead><tr><th>Number</th><th>Assigned Agent</th><th>Status</th></tr></thead>
                        <tbody><tr><td>+1 (555) 123-4567</td><td>Default AI Agent</td><td><span class="status-badge active">Active</span></td></tr></tbody>
                    </table>
                </div>
            </div>
            <div id="ai-knowledge" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">AI Knowledge Base</h3>
                        <div class="form-group file-upload-wrapper" style="margin-bottom: 0; width: auto;">
                            <label for="ai-doc-upload" class="primary-button">Upload Document</label>
                            <input type="file" id="ai-doc-upload" />
                        </div>
                    </div>
                    <p class="page-description">Upload documents (PDF, TXT, DOCX) to provide the AI with information to answer client questions.</p>
                    <table class="client-table"><thead><tr><th>File Name</th><th>Type</th><th>Date Uploaded</th><th>Actions</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>Service_Pricing.pdf</td>
                                <td>PDF</td>
                                <td>June 10, 2025</td>
                                <td><button class="icon-button danger-button" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button></td>
                            </tr>
                            <tr>
                                <td>FAQ.docx</td>
                                <td>DOCX</td>
                                <td>June 1, 2025</td>
                                <td><button class="icon-button danger-button" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="ai-logs" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Call History</h3></div>
                    <table class="client-table"><thead><tr><th>Timestamp</th><th>To/From</th><th>Duration</th><th>Status</th><th></th></tr></thead>
                        <tbody>
                            <tr><td>June 11, 2025, 3:15 PM</td><td>+1 (555) 987-6543</td><td>2m 10s</td><td><span class="status-badge active">Completed</span></td><td><button class="button">View Transcript</button></td></tr>
                            <tr><td>June 11, 2025, 2:40 PM</td><td>+1 (555) 246-8135</td><td>0m 45s</td><td><span class="status-badge failed">Failed</span></td><td><button class="button">View Transcript</button></td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="ai-settings" class="tab-content">
                <div class="card">
                   <div class="card-header"><h3 class="card-title">AI Agent Settings</h3></div>
                   <div class="form-group"><label for="ai-voice">Voice</label><select id="ai-voice"><option>Default (Female)</option><option>Alternative (Male)</option></select></div>
                   <div class="form-group" style="margin-top: 1.5rem;"><label for="ai-personality">Personality Prompt</label><textarea id="ai-personality" placeholder="e.g., You are a friendly and helpful receptionist. Always be polite and professional.">You are a friendly and helpful receptionist. Always be polite and professional.</textarea></div>
                   <div class="form-actions"><button class="primary-button">Save Settings</button></div>
                </div>
            </div>
        `,
        Reports: `
            <div class="page-toolbar">
                <div class="page-tabs">
                    <button class="button active" data-tab="report-overview">Overview</button>
                    <button class="button" data-tab="report-financial">Financials</button>
                    <button class="button" data-tab="report-appointments">Appointments</button>
                    <button class="button" data-tab="report-clients">Clients</button>
                    <button class="button" data-tab="report-forecasting">Demand Forecasting</button>
                </div>
                <div class="header-actions">
                    <select class="button" style="background:var(--background-card); color:var(--text-primary); border:1px solid var(--border-color); height:44px; border-radius:9999px;">
                        <option>Last 30 Days</option>
                        <option>Last 90 Days</option>
                        <option>This Year</option>
                        <option>All Time</option>
                    </select>
                    <button class="primary-button">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                        <span>Export</span>
                    </button>
                </div>
            </div>

            <div id="report-overview" class="tab-content active">
                <div class="grid grid-cols-4" style="margin-bottom: 1.5rem;">
                    <div class="summary-card card"><div class="label">Total Revenue</div><div class="value">$1,250</div><div class="change">+15% vs prior period</div></div>
                    <div class="summary-card card"><div class="label">Total Appointments</div><div class="value">42</div><div class="change">+5 vs prior period</div></div>
                    <div class="summary-card card"><div class="label">New Clients</div><div class="value">4</div><div class="change">-2 vs prior period</div></div>
                    <div class="summary-card card"><div class="label">Avg. Revenue/Appt</div><div class="value">$29.76</div><div class="change">+8% vs prior period</div></div>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Revenue Over Time</h3></div>
                    <div class="chart-placeholder"><svg width="100%" height="100%" viewBox="0 0 400 150" preserveAspectRatio="none"><path d="M 0,130 C 50,110, 100,60, 150,80 S 250,40, 300,60 S 350,100, 400,90" stroke="#4f46e5" fill="none" stroke-width="2"/></svg></div>
                </div>
            </div>

            <div id="report-financial" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Payments & Invoices</h3></div>
                    <table class="client-table">
                        <thead><tr><th>Date</th><th>Client</th><th>Description</th><th>Amount</th><th>Status</th><th></th></tr></thead>
                        <tbody>
                            <tr>
                                <td>June 11, 2025</td>
                                <td>John Smith</td>
                                <td>Check-in</td>
                                <td>$50.00</td>
                                <td><span class="status-badge active">Paid</span></td>
                                <td><button class="icon-button" title="Download Invoice"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg></button></td>
                            </tr>
                            <tr>
                                <td>June 10, 2025</td>
                                <td>Jane Doe</td>
                                <td>New Patient</td>
                                <td>$150.00</td>
                                <td><span class="status-badge active">Paid</span></td>
                                <td><button class="icon-button" title="Download Invoice"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg></button></td>
                            </tr>
                            <tr>
                                <td>June 05, 2025</td>
                                <td>John Smith</td>
                                <td>Group Therapy</td>
                                <td>$75.00</td>
                                <td><span class="status-badge upcoming">Pending</span></td>
                                <td><button class="icon-button" title="Download Invoice"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg></button></td>
                            </tr>
                            <tr>
                                <td>June 03, 2025</td>
                                <td>xiu lan</td>
                                <td>Consultation</td>
                                <td>$150.00</td>
                                <td><span class="status-badge failed">Failed</span></td>
                                <td><button class="icon-button" title="Download Invoice"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg></button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="report-appointments" class="tab-content">
                 <div class="grid grid-cols-2">
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Appointments by Service</h3></div>
                        <div class="chart-placeholder" style="flex-direction: row; gap: 2rem;">
                             <svg width="120" height="120" viewBox="0 0 32 32"><circle r="16" cx="16" cy="16" fill="var(--event-color-1)" /><circle r="16" cx="16" cy="16" fill="var(--event-color-2)" stroke="var(--background-card)" stroke-width="32" stroke-dasharray="45 100" transform="rotate(-90 16 16)" /><circle r="16" cx="16" cy="16" fill="var(--event-color-3)" stroke="var(--background-card)" stroke-width="32" stroke-dasharray="15 100" transform="rotate(72 16 16)" /></svg>
                             <ul class="revenue-list" style="width: 100%;"><li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-1);"></span>Initial Consultation</div><div class="amount">10</div></li><li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-2);"></span>Follow-up</div><div class="amount">25</div></li><li class="revenue-item"><div class="source"><span class="dot" style="background-color: var(--event-color-3);"></span>Workshop</div><div class="amount">7</div></li></ul>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Cancellation Rate</h3></div>
                        <div class="summary-card" style="text-align:center;"><div class="value">8%</div><div class="label">5 Cancellations</div></div>
                    </div>
                </div>
            </div>

            <div id="report-clients" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Client Growth</h3></div>
                    <div class="chart-placeholder"><svg width="100%" height="100%" viewBox="0 0 400 150" preserveAspectRatio="none"><path d="M 0,130 C 50,120, 100,100, 150,90 S 250,70, 300,50 S 350,30, 400,20" stroke="#4f46e5" fill="none" stroke-width="2"/></svg></div>
                </div>
            </div>
            
            <div id="report-forecasting" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Demand Forecasting (Next 90 Days)</h3></div>
                    <p class="page-description">Predictive analytics based on historical data, seasonality, and client growth trends.</p>
                     <div class="grid grid-cols-3" style="margin-bottom: 1.5rem;">
                        <div class="summary-card card"><div class="label">Predicted Revenue</div><div class="value">~$4,800</div><div class="change">Based on booking trends</div></div>
                        <div class="summary-card card"><div class="label">Expected Appointments</div><div class="value">~135</div><div class="change">Includes seasonal increase</div></div>
                        <div class="summary-card card"><div class="label">Projected Client Growth</div><div class="value">+12 New Clients</div><div class="change">Based on marketing data</div></div>
                    </div>
                    <div class="chart-placeholder">
                        <svg width="100%" height="100%" viewBox="0 0 400 150" preserveAspectRatio="none">
                            <path d="M 0,80 C 50,70, 100,50, 150,60 S 250,80, 300,60" stroke="#4f46e5" fill="none" stroke-width="2"/>
                            <path d="M 300,60 C 325,50, 350,45, 400,30" stroke="#818cf8" stroke-dasharray="4 4" fill="none" stroke-width="2"/>
                        </svg>
                    </div>
                </div>
            </div>
        `,
         'Web Services': `
            <div class="grid grid-cols-2">
                <div class="card">
                   <div class="card-header"><h3 class="card-title">Your Practitioner ID</h3></div>
                    <div class="form-group">
                        <input type="text" readonly value="practitioner-12345-abcde-67890" style="background-color: var(--background-body); cursor: default;">
                    </div>
                </div>
                 <div class="card">
                   <div class="card-header"><h3 class="card-title">Direct Booking Link</h3></div>
                    <div class="form-group">
                        <input type="text" readonly value="https://yourportal.com/book/practitioner-12345" style="background-color: var(--background-body); cursor: default;">
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top: 1.5rem;">
                <div class="card-header"><h3 class="card-title">Website Plugins</h3></div>
                <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Your website plugins will appear here.</div>
            </div>

            <div class="grid grid-cols-2" style="margin-top: 1.5rem;">
                 <div class="card">
                   <div class="card-header"><h3 class="card-title">Domains</h3> <a href="#" class="primary-button">Buy Domain</a></div>
                   <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Your connected domains will appear here.</div>
                </div>
                 <div class="card">
                   <div class="card-header"><h3 class="card-title">Website Builder</h3><a href="#" class="primary-button">Manage Website</a></div>
                   <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Manage your website pages and content.</div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 1.5rem;">
                <div class="card-header"><h3 class="card-title">Email Accounts</h3>
                    <div class="header-actions">
                        <button class="button">Add New Email</button>
                        <button class="primary-button">Email Portal</button>
                    </div>
                </div>
                <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Your email accounts will appear here.</div>
            </div>
        `,
        Profile: `
            <div class="card">
               <div class="card-header"><h3 class="card-title">My Profile</h3></div>
               <div class="form-grid">
                   <div class="form-group"><label for="profile-name">Full Name</label><input type="text" id="profile-name" value="John Doe"></div>
                   <div class="form-group"><label for="profile-email">Email Address</label><input type="email" id="profile-email" value="user@example.com" readonly></div>
               </div>
               <div class="form-group" style="margin-top: 1.5rem;">
                    <label for="profile-pic">Profile Picture</label>
                    <div class="file-upload-wrapper" style="width: auto; display: inline-block;">
                         <label for="profile-pic-upload" class="button">Choose File</label>
                        <input type="file" id="profile-pic-upload">
                    </div>
               </div>
               <div class="form-actions"><button class="primary-button">Save Changes</button></div>
            </div>
        `,
        'My Payments': `
            <div class="page-toolbar">
                <h2 style="font-size: 1.25rem; font-weight: 600;">Payments Dashboard</h2>
                <div class="header-actions">
                    <button class="button">Create Payment Link</button>
                    <button class="primary-button">Withdraw Funds</button>
                </div>
            </div>
            <div class="grid grid-cols-4" style="margin-bottom: 1.5rem;">
                <div class="summary-card card"><div class="label">Available Balance</div><div class="value">$1,250.00</div><div class="change">Available for payout</div></div>
                <div class="summary-card card"><div class="label">Pending Balance</div><div class="value">$450.00</div><div class="change">Clearing soon</div></div>
                <div class="summary-card card"><div class="label">Next Payout</div><div class="value">$1,250.00</div><div class="change">Scheduled for June 15, 2025</div></div>
                <div class="summary-card card"><div class="label">Volume (Last 30d)</div><div class="value">$3,800.00</div><div class="change">+20% vs prior 30d</div></div>
            </div>

            <div class="grid grid-cols-3" style="margin-bottom: 1.5rem;">
                <div class="card" style="grid-column: span 2 / span 2;">
                    <div class="card-header">
                        <h3 class="card-title">Payouts</h3>
                    </div>
                    <table class="client-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Bank Account</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>June 1, 2025</td>
                                <td>$2,500.00</td>
                                <td><span class="status-badge active">Paid</span></td>
                                <td>TD Bank ending in 1234</td>
                            </tr>
                            <tr>
                                <td>May 15, 2025</td>
                                <td>$1,800.00</td>
                                <td><span class="status-badge active">Paid</span></td>
                                <td>TD Bank ending in 1234</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                 <div class="card">
                     <div class="card-header"><h3 class="card-title">Payout Settings</h3></div>
                     <p class="page-description" style="margin-bottom: 0.5rem">Manage your connected bank accounts and payout schedule.</p>
                     <div style="font-weight: 600;">TD Bank ******1234</div>
                     <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem;">Default Account</div>
                     <button class="button">Manage Account</button>
                     <div class="dropdown-divider" style="margin: 1.5rem 0;"></div>
                     <h4 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;">Accounting Integrations</h4>
                      <div class="integration-item">
                        <img src="https://www.vectorlogo.zone/logos/xero/xero-icon.svg" alt="Xero Logo">
                        <div><div class="client-name">Xero</div></div>
                        <button class="button">Connect</button>
                     </div>
                     <div class="integration-item">
                        <img src="https://www.vectorlogo.zone/logos/quickbooks/quickbooks-icon.svg" alt="QuickBooks Logo">
                        <div><div class="client-name">QuickBooks</div></div>
                        <button class="button">Connect</button>
                     </div>
                </div>
            </div>
             <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Recent Transactions</h3>
                    <div class="search-bar">
                       <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                       <input type="text" placeholder="Search transactions...">
                    </div>
                </div>
                <table class="client-table">
                    <thead>
                        <tr>
                            <th>Date & Time</th>
                            <th>Client / Description</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>June 12, 2025, 2:10 PM</td>
                            <td><div class="client-info"><div><div class="client-name">Jane Doe</div><div class="client-email">Payment for Invoice #1234</div></div></div></td>
                            <td>$150.00</td>
                            <td><span class="status-badge active">Succeeded</span></td>
                            <td><button class="button">Refund</button></td>
                        </tr>
                        <tr>
                            <td>June 11, 2025, 10:05 AM</td>
                             <td><div class="client-info"><div><div class="client-name">John Smith</div><div class="client-email">Payment for Follow-up</div></div></div></td>
                            <td>$75.00</td>
                            <td><span class="status-badge active">Succeeded</span></td>
                            <td><button class="button">Refund</button></td>
                         </tr>
                         <tr>
                            <td>June 10, 2025, 4:30 PM</td>
                            <td><div class="client-info"><div><div class="client-name">xiu lan</div><div class="client-email">Payment for Initial Consultation</div></div></div></td>
                            <td>$250.00</td>
                            <td><span class="status-badge failed">Failed</span></td>
                            <td><button class="button" disabled>N/A</button></td>
                         </tr>
                        <tr>
                            <td>June 9, 2025, 11:00 AM</td>
                             <td><div class="client-info"><div><div class="client-name">Jagsharan Jagsharan</div><div class="client-email">Payment for Invoice #1232</div></div></div></td>
                            <td>$150.00</td>
                            <td><span class="status-badge" style="background-color: #f3f4f6; color: var(--text-secondary);">Refunded</span></td>
                            <td><button class="button" disabled>Done</button></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `,
        Settings: `
            <div class="page-toolbar">
                <div class="page-tabs" style="flex-wrap: nowrap; overflow-x: auto; padding-bottom: 10px; margin-bottom: -10px;">
                   <button class="button active" data-tab="settings-profile">Business Profile</button>
                   <button class="button" data-tab="settings-business-hours">Business Hours</button>
                   <button class="button" data-tab="settings-booking">Booking Rules</button>
                   <button class="button" data-tab="settings-staff">Staff</button>
                   <button class="button" data-tab="settings-forms">Forms</button>
                   <button class="button" data-tab="settings-client-subscriptions">Client Subscriptions</button>
                   <button class="button" data-tab="settings-notifications">Notifications</button>
                   <button class="button" data-tab="settings-payments">Payments</button>
                   <button class="button" data-tab="settings-subscription">My Subscription</button>
                   <button class="button" data-tab="settings-integrations">Integrations</button>
                   <button class="button" data-tab="settings-security">Account</button>
                </div>
            </div>

            <div id="settings-profile" class="tab-content active">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Business Profile</h3></div>
                    <div class="form-grid">
                       <div class="form-group"><label for="biz-name">Business Name</label><input type="text" id="biz-name" value="My Clinic"></div>
                       <div class="form-group"><label for="biz-logo">Business Logo</label>
                            <div class="file-upload-wrapper" style="width: auto; display: inline-block;">
                                <label for="biz-logo-upload" class="button">Choose File</label>
                                <input type="file" id="biz-logo-upload">
                            </div>
                       </div>
                       <div class="form-group"><label for="biz-phone">Business Phone</label><input type="tel" id="biz-phone" value="+1 (555) 987-6543"></div>
                       <div class="form-group"><label for="biz-email">Business Email</label><input type="email" id="biz-email" value="contact@myclinic.com"></div>
                       <div class="form-group"><label for="biz-website">Website</label><input type="url" id="biz-website" value="https://myclinic.com"></div>
                       <div class="form-group"><label for="biz-address">Address</label><input type="text" id="biz-address" value="123 Health St, Wellness City"></div>
                       <div class="form-group full-width"><label for="biz-description">Business Description</label><textarea id="biz-description" placeholder="Describe your business, services, and mission. This will be shown on your public booking page."></textarea></div>
                   </div>
                   <div class="form-actions"><button class="primary-button">Save Profile</button></div>
                </div>
            </div>
            
            <div id="settings-business-hours" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Business Hours</h3></div>
                    <p class="page-description">Set the default weekly hours for your business. Staff can have their own availability which will override these hours.</p>
                    <div class="availability-row"><div class="availability-day">Sunday</div><div class="availability-times">Unavailable</div><label class="switch"><input type="checkbox"><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Monday</div><div class="availability-times"><input type="time" value="09:00"><span>to</span><input type="time" value="17:00"></div><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Tuesday</div><div class="availability-times"><input type="time" value="09:00"><span>to</span><input type="time" value="17:00"></div><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Wednesday</div><div class="availability-times"><input type="time" value="09:00"><span>to</span><input type="time" value="17:00"></div><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Thursday</div><div class="availability-times"><input type="time" value="09:00"><span>to</span><input type="time" value="17:00"></div><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Friday</div><div class="availability-times"><input type="time" value="09:00"><span>to</span><input type="time" value="17:00"></div><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div>
                    <div class="availability-row"><div class="availability-day">Saturday</div><div class="availability-times">Unavailable</div><label class="switch"><input type="checkbox"><span class="slider"></span></label></div>
                    <div class="form-actions"><button class="primary-button">Save Business Hours</button></div>
                </div>
            </div>

            <div id="settings-booking" class="tab-content">
                <div class="card">
                     <div class="card-header"><h3 class="card-title">Booking Policies</h3></div>
                     <div class="form-group"><label for="lead-time">Minimum Lead Time for Booking</label><select id="lead-time"><option>1 hour</option><option>2 hours</option><option selected>24 hours</option></select></div>
                     <div class="form-group" style="margin-top:1.5rem;"><label for="cancellation-policy">Cancellation Policy</label><textarea id="cancellation-policy">Cancellations must be made at least 24 hours in advance.</textarea></div>
                     <div class="form-actions"><button class="primary-button">Save Policies</button></div>
                </div>
            </div>
             <div id="settings-staff" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Staff Management</h3><button class="primary-button" id="addStaffBtn">Add Staff Member</button></div>
                     <p class="page-description">Manage your practitioners, their services, and schedules.</p>
                     <table class="client-table">
                        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>Dr. Smith</td>
                                <td>dr.smith@example.com</td>
                                <td>Practitioner</td>
                                <td><button class="button" data-action="edit-staff">Edit</button></td>
                            </tr>
                            <tr>
                                <td>Jane Doe</td>
                                <td>jane.doe@example.com</td>
                                <td>Assistant</td>
                                <td><button class="button" data-action="edit-staff">Edit</button></td>
                            </tr>
                        </tbody>
                     </table>
                </div>
            </div>
            <div id="settings-forms" class="tab-content">
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">Client Forms</h3><button class="primary-button">Upload Form</button></div>
                    <p class="page-description">Manage intake forms and other documents. Forms can be sent automatically to new clients upon booking.</p>
                    <div class="form-list-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        <div><div class="client-name">New Client Intake Form</div><div class="client-email">PDF - 245 KB</div></div>
                        <div style="display: flex; align-items: center; gap: 1rem;"><div class="toggle-switch"><span>Auto-send</span><label class="switch"><input type="checkbox" checked><span class="slider"></span></label></div><button class="icon-button danger-button" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button></div>
                    </div>
                    <div class="form-list-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                        <div><div class="client-name">Consent for Treatment</div><div class="client-email">PDF - 110 KB</div></div>
                        <div style="display: flex; align-items: center; gap: 1rem;"><div class="toggle-switch"><span>Auto-send</span><label class="switch"><input type="checkbox"><span class="slider"></span></label></div><button class="icon-button danger-button" title="Delete"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button></div>
                    </div>
                </div>
            </div>
             <div id="settings-client-subscriptions" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Client Subscription Plans</h3><button class="primary-button" id="addPlanBtn">Add New Plan</button></div>
                    <p class="page-description">Create recurring membership plans for your clients. Plans can include discounts on services.</p>
                    <div class="subscription-plans">
                        <div class="card plan-card">
                            <div class="card-header"><h4 class="plan-name">Wellness Basic</h4></div>
                            <div class="plan-price">$50 <span class="plan-price-note">/ month</span></div>
                            <ul class="plan-features">
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>1 Included Session per Month</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>10% Discount on Additional Services</li>
                            </ul>
                            <button class="button select-plan-btn" data-action="edit-plan">Edit Plan</button>
                        </div>
                         <div class="card plan-card">
                            <div class="card-header"><h4 class="plan-name">Wellness Plus</h4></div>
                            <div class="plan-price">$90 <span class="plan-price-note">/ month</span></div>
                            <ul class="plan-features">
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>2 Included Sessions per Month</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>15% Discount on Additional Services</li>
                                 <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>Priority Booking</li>
                            </ul>
                            <button class="button select-plan-btn" data-action="edit-plan">Edit Plan</button>
                        </div>
                    </div>
                </div>
            </div>
            <div id="settings-notifications" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Notification Settings</h3></div>
                     <div class="toggle-switch" style="justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid var(--border-color);"><span>Client Appointment Reminders (SMS)</span><label class="switch"><input type="checkbox" checked> <span class="slider"></span></label></div>
                     <div class="toggle-switch" style="justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid var(--border-color);"><span>New Booking Alerts (Email)</span><label class="switch"><input type="checkbox" checked> <span class="slider"></span></label></div>
                </div>
            </div>
            <div id="settings-payments" class="tab-content">
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">Payment Settings</h3></div>
                     <p class="page-description">Manage your payment processing and view your financial dashboard, powered by Stripe.</p>
                     <div class="form-actions"><a href="#" class="primary-button" data-page="My Payments">Go to Payments Dashboard</a></div>
                </div>
            </div>
            <div id="settings-subscription" class="tab-content">
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">My Subscription Plan</h3></div>
                    <p class="page-description">This is your subscription to the portal software. To manage subscription plans for your clients, see the "Client Subscriptions" tab.</p>
                    <div class="subscription-plans">
                        <!-- Pay As You Go Plan -->
                        <div class="card plan-card">
                            <div class="card-header">
                                <h4 class="plan-name">Pay As You Go</h4>
                                <div class="plan-price">$0.90</div>
                                <div class="plan-price-note">per completed appointment + Stripe fees</div>
                            </div>
                            <ul class="plan-features">
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> 1 Staff User Included</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Basic Calendar & Appointments</li>
                                <li class="disabled"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Website Booking Plugin</li>
                            </ul>
                            <button class="button select-plan-btn" disabled>Current Plan</button>
                        </div>
                        <!-- Growth Plan -->
                        <div class="card plan-card">
                            <div class="card-header">
                                <h4 class="plan-name">Growth Plan</h4>
                                <div class="plan-price">$79</div>
                                <div class="plan-price-note">CAD per month (or $690/year)</div>
                            </div>
                            <ul class="plan-features">
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Up to 5 Staff Users</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Full Client Management</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Website Booking Plugin</li>
                            </ul>
                            <button class="primary-button select-plan-btn">Select Plan</button>
                        </div>
                         <!-- Scale Plan -->
                        <div class="card plan-card">
                            <div class="card-header">
                                <h4 class="plan-name">Scale Plan</h4>
                                <div class="plan-price">$129</div>
                                <div class="plan-price-note">CAD per month (or $1290/year)</div>
                            </div>
                            <ul class="plan-features">
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Up to 10 Staff Users</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> AI Voice Call Reminders & Booking</li>
                                <li><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Advanced AI Demand Forecasting</li>
                            </ul>
                            <button class="primary-button select-plan-btn">Select Plan</button>
                        </div>
                    </div>
                </div>
            </div>
             <div id="settings-integrations" class="tab-content">
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Integrations</h3></div>
                    <div class="toggle-switch" style="justify-content: space-between; padding: 1rem 0;"><span>Google Calendar Sync</span><button class="primary-button">Connect</button></div>
                </div>
            </div>
            <div id="settings-security" class="tab-content">
                 <div class="card">
                    <div class="card-header"><h3 class="card-title">Account Security</h3></div>
                    <div class="form-group" style="margin-bottom: 1rem;"><label for="current-password">Current Password</label><input type="password" id="current-password"></div>
                    <div class="form-group" style="margin-bottom: 1rem;"><label for="new-password">New Password</label><input type="password" id="new-password"></div>
                    <div class="form-group"><label for="confirm-password">Confirm New Password</label><input type="password" id="confirm-password"></div>
                    <div class="form-actions"><button class="primary-button">Update Password</button></div>
                </div>
                <div class="card" style="margin-top: 1.5rem; border-color: var(--text-danger);">
                    <div class="card-header" style="border-bottom-color: var(--text-danger);"><h3 class="card-title" style="color: var(--text-danger);">Delete Account</h3></div>
                    <p class="page-description">Permanently delete your account and all associated data. This action is irreversible.</p>
                    <div class="form-actions"><button class="danger-button">Delete My Account</button></div>
                </div>
            </div>
        `,
        Default: `<div class="card"><div class="card-header"><h2 class="card-title"></h2></div><p>Content for this section is under development.</p></div>`
    };

    function setupCalendarPage() {
        const monthYearEl = document.getElementById('calendar-month-year');
        const calendarBody = document.getElementById('calendar-body');
        const prevBtn = document.getElementById('cal-prev-month');
        const nextBtn = document.getElementById('cal-next-month');
        const todayBtn = document.getElementById('cal-today');

        if (!calendarBody) return; 

        let currentDate = new Date();

        let events = [
            { id: 1, date: '2025-06-02', time: '10am', title: 'Consultation', type: 'event-session', staff: 'smith' },
            { id: 2, date: '2025-06-03', time: '2pm', title: 'Follow-up', type: 'event-individual', staff: 'doe' },
            { id: 3, date: '2025-06-05', time: '4pm', title: 'Group Therapy', type: 'event-group', staff: 'smith' },
            { id: 4, date: '2025-06-10', time: '11am', title: 'New Patient', type: 'event-session', staff: 'doe' },
            { id: 5, date: '2025-06-11', time: '9am', title: 'Check-in', type: 'event-individual', staff: 'smith' },
            { id: 6, date: '2025-06-13', time: '3pm', title: 'Workshop', type: 'event-group', staff: 'doe' },
        ];

        function renderCalendar(date) {
            if(!monthYearEl || !calendarBody) return;
            calendarBody.innerHTML = '';
            const year = date.getFullYear();
            const month = date.getMonth();
            monthYearEl.textContent = `${date.toLocaleString('default', { month: 'long' })} ${year}`;
            const firstDayOfMonth = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            
            for (let i = 0; i < firstDayOfMonth; i++) {
                calendarBody.innerHTML += '<div class="calendar-cell other-month"></div>';
            }

            for (let day = 1; day <= daysInMonth; day++) {
                const cell = document.createElement('div');
                cell.classList.add('calendar-cell');
                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                cell.dataset.date = dateStr;
                cell.innerHTML = `<div class="day-number">${day}</div>`;
                const today = new Date();
                if (year === today.getFullYear() && month === today.getMonth() && day === today.getDate()) {
                    cell.classList.add('today');
                }
                
                const eventContainer = document.createElement('div');
                eventContainer.classList.add('event-container');
                events.filter(e => e.date === dateStr).forEach(event => {
                     const eventEl = document.createElement('div');
                     eventEl.classList.add('calendar-event', event.type);
                     eventEl.dataset.staff = event.staff;
                     eventEl.dataset.eventId = event.id;
                     eventEl.textContent = `${event.time} - ${event.title}`;
                     eventContainer.appendChild(eventEl);
                });
                cell.appendChild(eventContainer);
                calendarBody.appendChild(cell);
            }
            setupDragAndDrop();
        }

        function setupDragAndDrop() {
            const eventContainers = calendarBody.querySelectorAll('.event-container');
            const calendarCells = calendarBody.querySelectorAll('.calendar-cell');

            const containers = [...eventContainers, ...calendarCells];

            containers.forEach(container => {
                 new Sortable(container, {
                    group: 'calendar-events',
                    animation: 150,
                    onEnd: function (evt) {
                        const eventEl = evt.item;
                        const eventId = parseInt(eventEl.dataset.eventId);
                        const newDate = evt.to.closest('.calendar-cell').dataset.date;

                        // Update the event's date in the events array
                        const eventIndex = events.findIndex(e => e.id === eventId);
                        if (eventIndex > -1) {
                            events[eventIndex].date = newDate;
                        }
                        
                        // Re-render the calendar to reflect the change
                        renderCalendar(currentDate);
                    },
                });
            });
        }
        
        function setupStaffFilterListeners() {
            const staffFilters = pageContent.querySelector('.staff-filters');
            if (!staffFilters) return;
            
            staffFilters.addEventListener('click', (e) => {
                const filterButton = e.target.closest('.button');
                if (!filterButton) return;
                const filter = filterButton.dataset.staffFilter;
                staffFilters.querySelectorAll('.button').forEach(btn => btn.classList.remove('active'));
                filterButton.classList.add('active');
                const allEvents = pageContent.querySelectorAll('.calendar-event');
                allEvents.forEach(eventEl => {
                    if (filter === 'all' || eventEl.dataset.staff === filter) {
                        eventEl.style.display = '';
                    } else {
                        eventEl.style.display = 'none';
                    }
                });
            });
        }
        
        if(prevBtn) {
            prevBtn.addEventListener('click', () => {
                currentDate.setMonth(currentDate.getMonth() - 1);
                renderCalendar(currentDate);
                setupStaffFilterListeners();
            });
        }
        if(nextBtn) {
            nextBtn.addEventListener('click', () => {
                currentDate.setMonth(currentDate.getMonth() + 1);
                renderCalendar(currentDate);
                setupStaffFilterListeners();
            });
        }
        if(todayBtn) {
            todayBtn.addEventListener('click', () => {
                currentDate = new Date();
                renderCalendar(currentDate);
                setupStaffFilterListeners();
            });
        }

        renderCalendar(currentDate);
        setupStaffFilterListeners();
    }

     function setupCommunicationsPage() {
        const commsContainer = document.querySelector('.communications-layout');
        if (!commsContainer) return;
        
        const conversationList = commsContainer.querySelector('.conversation-list');
        const contentArea = commsContainer.querySelector('#communication-content-area');

        // Load default view
        contentArea.innerHTML = communicationTemplates.sms;

        conversationList.addEventListener('click', (e) => {
            const conversationItem = e.target.closest('.conversation-item');
            if (!conversationItem) return;

            // Handle selecting a conversation thread
            conversationList.querySelectorAll('.conversation-item').forEach(item => item.classList.remove('active'));
            conversationItem.classList.add('active');

            // Handle clicking an action button within a conversation
            const actionButton = e.target.closest('.icon-button[data-action]');
            if (actionButton) {
                e.stopPropagation(); 
                const action = actionButton.dataset.action;
                
                if(communicationTemplates[action]) {
                    contentArea.innerHTML = communicationTemplates[action];
                }
                
                const allActionButtons = conversationItem.querySelectorAll('.conversation-actions .icon-button');
                allActionButtons.forEach(btn => btn.classList.remove('active'));
                actionButton.classList.add('active');
            }
        });
    }

    
    function setupTabbedPage(container) {
        const tabButtons = container.querySelectorAll('.page-tabs .button');
        const tabContents = container.querySelectorAll('.tab-content');
        if (!tabButtons.length) return;

        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabId = button.dataset.tab;
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                const activeContent = container.querySelector('#' + tabId);
                tabContents.forEach(content => {
                    if (content === activeContent) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });
            });
        });
    }
    
    function setupModal(modalId, openTriggerSelector) { 
         const modalOverlay = document.getElementById(modalId);
         if(!modalOverlay) return;
        
         const closeTriggers = modalOverlay.querySelectorAll('[data-close-modal]');

         document.body.addEventListener('click', (e) => {
             const trigger = e.target.closest(openTriggerSelector);
             if (trigger) {
                 e.preventDefault();
                 
                 // --- Dynamic data population for modals ---
                 if (modalId === 'clientInfoModal') {
                     populateClientInfoModal(trigger);
                 } else if (modalId === 'videoCallModal') {
                     populateVideoCallModal(trigger);
                 } else if (modalId === 'planModal') {
                     populatePlanModal(trigger);
                 }
                 modalOverlay.classList.add('show');
             }
         });

         closeTriggers.forEach(trigger => {
             trigger.addEventListener('click', () => modalOverlay.classList.remove('show'));
         });
         
         modalOverlay.addEventListener('click', (e) => {
             if (e.target === modalOverlay) {
                  modalOverlay.classList.remove('show');
             }
         });
    }

    function populateClientInfoModal(trigger) {
        const card = trigger.closest('.client-card-item');
        const name = card.querySelector('.client-name').textContent;
        const email = card.querySelector('.client-email').textContent;
        
        const modalTitle = document.getElementById('clientInfoModalTitle');
        const modalBody = document.getElementById('clientInfoModalBody');

        modalTitle.textContent = `${name}'s Information`;
        modalBody.innerHTML = `
            <h4 style="margin-top: 1rem; margin-bottom: 1rem; font-size: 1.1rem;">Personal Information</h4>
             <div class="form-grid">
               <div class="form-group"><label>Full Name</label><input type="text" readonly value="${name}"></div>
               <div class="form-group"><label>Date of Birth</label><input type="text" readonly value="1990-01-01"></div>
               <div class="form-group"><label>Phone Number</label><input type="text" readonly value="+1 555-123-4567"></div>
               <div class="form-group"><label>Email Address</label><input type="text" readonly value="${email}"></div>
           </div>
           <h4 style="margin-top: 2rem; margin-bottom: 1rem; font-size: 1.1rem;">Emergency Contact</h4>
           <div class="form-grid">
               <div class="form-group"><label>Contact Name</label><input type="text" readonly value="Jane Doe"></div>
               <div class="form-group"><label>Contact Phone</label><input type="text" readonly value="+1 555-987-6543"></div>
           </div>
           <h4 style="margin-top: 2rem; margin-bottom: 1rem; font-size: 1.1rem;">Medical History & Records</h4>
           <div class="form-group"><label>Session Notes</label><textarea readonly>Client making good progress. Discussed coping mechanisms for stress. Plan to follow-up in 2 weeks.</textarea></div>
        `;
    }

    function populateVideoCallModal(trigger) {
         const card = trigger.closest('.client-card-item');
         const name = card.querySelector('.client-name').textContent;
         const avatar = card.querySelector('.client-avatar').textContent;

         document.getElementById('videoCallAvatar').textContent = avatar;
         document.getElementById('videoCallName').textContent = `Connecting to ${name}...`;
    }
    
    function populatePlanModal(trigger) {
        const modal = document.getElementById('planModal');
        const title = modal.querySelector('#planModalTitle');
        
        // Reset fields for "Add New"
        modal.querySelector('#plan-name').value = '';
        modal.querySelector('#plan-price').value = '';
        modal.querySelector('#plan-sessions').value = '';
        modal.querySelector('#plan-discount').value = '';
        modal.querySelector('#plan-features-input').value = '';

        if (trigger.id === 'addPlanBtn') {
            title.textContent = 'Add New Plan';
        } else { // It's an "Edit" button
            title.textContent = 'Edit Plan';
            // Here you would fetch the data for the specific plan and populate the fields
            // For demonstration, I'll use placeholder data
            const planCard = trigger.closest('.plan-card');
            const planName = planCard.querySelector('.plan-name').textContent;
            modal.querySelector('#plan-name').value = planName;
            modal.querySelector('#plan-price').value = planName === 'Wellness Basic' ? '50' : '90';
            modal.querySelector('#plan-sessions').value = planName === 'Wellness Basic' ? '1' : '2';
            modal.querySelector('#plan-discount').value = planName === 'Wellness Basic' ? '10' : '15';
            modal.querySelector('#plan-features-input').value = planName === 'Wellness Basic' ? '' : 'Priority Booking';
        }
    }


    function loadContent(pageKey, openTabId) {
        // Use a mapping to handle different keys passed from Django vs. data-attributes
        const pageMap = {
            'Dashboards': 'Dashboards',
            'Communications': 'Communications',
            'Calendar': 'Calendar',
            'Appointments': 'Appointments',
            'Clients': 'Clients',
            'AI Voice Assistant': 'AI Voice Assistant',
            'Reports': 'Reports',
            'Web Services': 'Web Services',
            'Profile': 'Profile',
            'My Payments': 'My Payments',
            'Settings': 'Settings'
        };
        
        const page = pageMap[pageKey] || 'Dashboards';

        if (!pageContent || !pageTitle) {
            console.error("Core elements #pageContent or #pageTitle not found.");
            return;
        }

        if (!contentTemplates[page]) {
             console.error(`Content for page "${page}" not found.`);
             page = 'Default';
        }
        
        pageTitle.textContent = page.replace(/([A-Z])/g, ' $1').trim();
        pageContent.innerHTML = contentTemplates[page];

        // Setup page-specific JS after content is loaded
        setupTabbedPage(pageContent);
        if (page === 'Calendar') setupCalendarPage();
        if (page === 'Communications') setupCommunicationsPage();
        if (page === 'Appointments') setupModal('addServiceModal', '#addNewServiceBtn');
        if (page === 'AI Voice Assistant') {
             pageContent.addEventListener('click', function(e){
                 if(e.target.closest('.danger-button')) {
                     e.target.closest('tr').remove();
                 }
             })
        }
        if (page === 'Settings') {
            setupModal('addStaffModal', '#addStaffBtn');
            setupModal('editStaffModal', '[data-action="edit-staff"]');
            setupModal('planModal', '#addPlanBtn');
            setupModal('planModal', '[data-action="edit-plan"]');
            
            const editStaffModal = document.getElementById('editStaffModal');
            if(editStaffModal) {
                setupTabbedPage(editStaffModal);
            }
        }
        if(page === 'Clients') {
            setupModal('videoCallModal', '[data-action="video-call"]');
            setupModal('clientInfoModal', '[data-action="view-info"]');
        }

        // If a specific tab should be opened, click it.
        if (openTabId) {
            const tabButton = pageContent.querySelector(`.page-tabs .button[data-tab="${openTabId}"]`);
            if (tabButton) {
                tabButton.click();
            }
        }
    }

    // This function is no longer needed as navigation is handled by standard links
    // function handlePageNavigation(e) { ... }
    
    // --- Dropdown Logic ---
    function setupDropdown(buttonId, dropdownId) {
        const button = document.getElementById(buttonId);
        const dropdown = document.getElementById(dropdownId);
        
        if (button && dropdown) {
             button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
                    if (openDropdown.id !== dropdownId) {
                        openDropdown.classList.remove('show');
                    }
                });
                dropdown.classList.toggle('show');
            });
        }
    }

    setupDropdown('profileButton', 'profileDropdown');
    setupDropdown('notificationButton', 'notificationDropdown');
    
    window.addEventListener('click', function(e) {
        document.querySelectorAll('.dropdown-menu.show').forEach(openDropdown => {
            const buttonId = openDropdown.id.replace('Dropdown', 'Button');
            const button = document.getElementById(buttonId);
            if (button && !button.contains(e.target) && !openDropdown.contains(e.target)) {
               openDropdown.classList.remove('show');
            }
        })
    });
    
    // Setup for globally available modals
    setupModal('newAppointmentModal', '#newAppointmentBtn');
    setupModal('allNotificationsModal', '#seeAllNotificationsBtn');
    setupTabbedPage(document.getElementById('newAppointmentModal'));

    // --- INITIAL PAGE LOAD ---
    // Use the page name passed from the Django template
    const initialPage = window.djangoPageContext.page;
    loadContent(initialPage);

    // Set the active state for the corresponding navigation link
    document.querySelectorAll('.side-nav-links a, .side-nav-user a').forEach(l => {
        l.classList.remove('active');
        if (l.dataset.page === initialPage) {
            l.classList.add('active');
        }
    });
});
