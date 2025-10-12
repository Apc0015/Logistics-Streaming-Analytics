"""
UI Enhancement Utilities for Logistics Streaming Analytics
Provides helper functions to apply custom styling and enhanced components
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

def load_custom_styles():
    """Load and inject custom CSS styles"""
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            css_content = f.read()

        # Inject CSS into Streamlit
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        st.warning("Custom styles file not found. Using default styling.")
        return False
    except Exception as e:
        st.error(f"Error loading custom styles: {e}")
        return False

def create_logistics_header(title: str = "Logistics Analytics Dashboard", subtitle: str = "Real-time transportation and logistics monitoring"):
    """Create enhanced logistics header with gradient background"""
    st.markdown(f"""
    <div class="logistics-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def create_enhanced_kpi_card(title: str, value: Any, icon: str = "📊", status: str = "normal", delta: Optional[str] = None):
    """Create enhanced KPI card with custom styling and status indicators"""
    # Apply status-specific styling
    status_class = f"kpi-card {status}" if status != "normal" else "kpi-card"

    card_html = f"""
    <div class="{status_class}">
        <div class="kpi-value">{icon} {value}</div>
        <div class="kpi-label">{title}</div>
    """

    if delta:
        card_html += f"""
        <div style="font-size: 0.875rem; color: var(--gray-600); margin-top: 8px;">
            Δ {delta}
        </div>
        """

    card_html += "</div>"

    st.markdown(card_html, unsafe_allow_html=True)

def create_sidebar_section(title: str, icon: str = ""):
    """Create styled sidebar section"""
    icon_html = f"<span style='margin-right: 8px;'>{icon}</span>" if icon else ""
    st.sidebar.markdown(f"""
    <div class="sidebar-section">
        <h3>{icon_html}{title}</h3>
    """, unsafe_allow_html=True)

def close_sidebar_section():
    """Close sidebar section"""
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

def create_alert(message: str, type: str = "info", dismissible: bool = False):
    """Create styled alert component"""
    alert_class = f"alert alert-{type}"

    alert_html = f'<div class="{alert_class}">{message}'

    if dismissible:
        alert_html += '<button onclick="this.parentElement.style.display=\'none\'" style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;">×</button>'

    alert_html += '</div>'

    st.markdown(alert_html, unsafe_allow_html=True)

def create_loading_state(message: str = "Loading...", show_progress: bool = False):
    """Create enhanced loading state with spinner"""
    loading_html = f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <p>{message}</p>
    </div>
    """

    st.markdown(loading_html, unsafe_allow_html=True)

    if show_progress:
        progress_bar = st.progress(0)
        return progress_bar

    return None

def create_status_indicator(status: str, text: str = ""):
    """Create status indicator badge"""
    status_class = f"status-indicator status-{status}"
    display_text = text if text else status.replace("-", " ").title()

    st.markdown(f'<span class="{status_class}">{display_text}</span>', unsafe_allow_html=True)

def create_vehicle_icon(vehicle_type: str):
    """Create vehicle type icon"""
    icon_class = f"vehicle-icon vehicle-{vehicle_type.lower().replace(' ', '').replace('-', '')}"
    st.markdown(f'<span class="{icon_class}"></span>', unsafe_allow_html=True)

def create_priority_indicator(priority: str):
    """Create priority indicator with color coding"""
    priority_class = f"priority-{priority.lower()}"
    st.markdown(f'<span class="{priority_class}">● {priority.upper()}</span>', unsafe_allow_html=True)

def create_progress_bar(percentage: float, label: str = "", color: str = "primary"):
    """Create animated progress bar"""
    st.markdown(f"""
    <div style="margin-bottom: 16px;">
        {f'<div style="font-size: 0.875rem; color: var(--gray-700); margin-bottom: 4px;">{label}</div>' if label else ''}
        <div class="progress-container">
            <div class="progress-bar" style="width: {min(percentage, 100)}%; background: linear-gradient(90deg, var(--{color}-500), var(--{color}-600));"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--gray-600); text-align: right; margin-top: 2px;">
            {percentage:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_tooltip(text: str, tooltip_content: str):
    """Create element with tooltip on hover"""
    st.markdown(f'<span class="tooltip" data-tooltip="{tooltip_content}">{text}</span>', unsafe_allow_html=True)

def create_enhanced_metric(label: str, value: Any, delta: Optional[str] = None, help_text: str = ""):
    """Create enhanced metric with optional delta and help text"""
    col1, col2 = st.columns([3, 1])

    with col1:
        if help_text:
            create_tooltip(label, help_text)
        else:
            st.markdown(f"**{label}**")

        if delta:
            st.markdown(f"""
            <div style="font-size: 2rem; font-weight: 700; color: var(--gray-900); margin-bottom: 4px;">
                {value}
            </div>
            <div style="font-size: 0.875rem; color: var(--success-600);">
                ↗ {delta}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-size: 2rem; font-weight: 700; color: var(--gray-900);">
                {value}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Space for additional content or leave empty for alignment
        pass

def create_navigation_item(label: str, icon: str, page: str, is_active: bool = False):
    """Create styled navigation item"""
    active_class = " nav-item-active" if is_active else ""
    st.sidebar.markdown(f"""
    <div class="nav-item{active_class}" onclick="window.location.href='?page={page}'" style="cursor: pointer;">
        <span class="nav-icon">{icon}</span>
        <span>{label}</span>
    </div>
    """, unsafe_allow_html=True)

def create_chart_container(title: str, description: str = ""):
    """Create styled chart container"""
    st.markdown(f"""
    <div class="chart-container">
        <div class="chart-header">
            <h3 class="chart-title">{title}</h3>
            {f'<p style="color: var(--gray-600); font-size: 0.875rem; margin: 0;">{description}</p>' if description else ''}
        </div>
    """, unsafe_allow_html=True)

def close_chart_container():
    """Close chart container"""
    st.markdown("</div>", unsafe_allow_html=True)

def create_form_section(title: str, icon: str = ""):
    """Create styled form section"""
    icon_html = f"<span style='margin-right: 8px;'>{icon}</span>" if icon else ""
    st.markdown(f"""
    <div class="form-container">
        <div class="form-section">
            <h4>{icon_html}{title}</h4>
    """, unsafe_allow_html=True)

def close_form_section():
    """Close form section"""
    st.markdown("</div></div>", unsafe_allow_html=True)

def create_custom_table(data: List[Dict], title: str = "", highlight_columns: List[str] = None):
    """Create custom styled table"""
    if not data:
        st.info("No data available")
        return

    if title:
        st.subheader(title)

    # Convert to DataFrame for display
    df = st.dataframe(data, use_container_width=True)

    # Apply custom styling if needed
    if highlight_columns:
        # This would require additional JavaScript for column highlighting
        pass

    return df

def create_export_section(data: Dict, filename_prefix: str = "logistics_export"):
    """Create data export functionality"""
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export Dashboard Data", key="export_dashboard"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"

            st.download_button(
                label="Download JSON",
                data=json.dumps(data, indent=2, default=str),
                file_name=filename,
                mime="application/json",
                key="download_json"
            )

    with col2:
        if st.button("📈 Export Charts", key="export_charts"):
            st.info("Chart export feature - Coming Soon!")

    with col3:
        if st.button("📋 Generate Report", key="generate_report"):
            st.info("Automated report generation - Coming Soon!")

def create_filter_section():
    """Create comprehensive filter section"""
    st.sidebar.markdown("### 🔍 Filters")

    # Date range filter
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime.now().date() - timedelta(days=7), datetime.now().date()),
        max_value=datetime.now().date(),
        key="date_filter"
    )

    # Status filter
    status_options = ["All", "In Transit", "Delivered", "Pending", "Delayed"]
    status_filter = st.sidebar.selectbox(
        "Shipment Status",
        options=status_options,
        key="status_filter"
    )

    # Vehicle type filter
    vehicle_options = ["All", "Truck", "Van", "Semi-trailer", "Delivery", "Refrigerated"]
    vehicle_filter = st.sidebar.selectbox(
        "Vehicle Type",
        options=vehicle_options,
        key="vehicle_filter"
    )

    # Priority filter
    priority_options = ["All", "Low", "Medium", "High", "Critical"]
    priority_filter = st.sidebar.selectbox(
        "Priority",
        options=priority_options,
        key="priority_filter"
    )

    return {
        'date_range': date_range,
        'status_filter': status_filter if status_filter != "All" else None,
        'vehicle_filter': vehicle_filter if vehicle_filter != "All" else None,
        'priority_filter': priority_filter if priority_filter != "All" else None
    }

def apply_responsive_classes():
    """Apply responsive utility classes"""
    st.markdown("""
    <style>
    /* Additional responsive utilities */
    @media (max-width: 768px) {
        .kpi-card {
            margin-bottom: 1rem;
        }
        .logistics-header {
            padding: 2rem 1rem;
            text-align: center;
        }
        .logistics-header h1 {
            font-size: 2rem;
        }
    }

    /* Enhanced mobile navigation */
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg-primary);
        border-top: 1px solid var(--gray-200);
        padding: 1rem;
        display: flex;
        justify-content: space-around;
        z-index: 1000;
    }

    /* Tablet optimizations */
    @media (min-width: 769px) and (max-width: 1023px) {
        .kpi-value {
            font-size: 3rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def create_dashboard_grid(kpi_data: List[Dict]):
    """Create responsive dashboard grid with KPI cards"""
    # Calculate number of columns based on screen size
    cols = st.columns(4)  # Default 4 columns

    for i, kpi in enumerate(kpi_data):
        col_idx = i % 4
        with cols[col_idx]:
            status = kpi.get('status', 'normal')
            delta = kpi.get('delta')
            icon = kpi.get('icon', '📊')

            create_enhanced_kpi_card(
                title=kpi['title'],
                value=kpi['value'],
                icon=icon,
                status=status,
                delta=delta
            )

def create_notification_center(notifications: List[Dict]):
    """Create notification center for alerts and updates"""
    if not notifications:
        return

    st.markdown("### 🔔 Notifications")

    for notification in notifications:
        alert_type = notification.get('type', 'info')
        message = notification.get('message', '')
        dismissible = notification.get('dismissible', False)

        create_alert(message, type=alert_type, dismissible=dismissible)

def initialize_ui_enhancements():
    """Initialize all UI enhancements"""
    # Load custom styles
    styles_loaded = load_custom_styles()

    if styles_loaded:
        st.success("✨ Enhanced UI loaded successfully!")
    else:
        st.warning("Using default styling")

    # Apply responsive classes
    apply_responsive_classes()

    return styles_loaded

# Utility functions for common UI patterns
def format_number(num: float, precision: int = 1) -> str:
    """Format numbers with appropriate precision"""
    if abs(num) >= 1000000:
        return f"{num/1000000:.{precision}f}M"
    elif abs(num) >= 1000:
        return f"{num/1000:.{precision}f}K"
    else:
        return f"{num:.{precision}f}"

def format_time(hours: float) -> str:
    """Format time duration"""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}m"
    else:
        return f"{hours:.1f}h"

def format_percentage(value: float) -> str:
    """Format percentage with appropriate precision"""
    return f"{value:.1f}%"

def get_status_color(status: str) -> str:
    """Get color class for status"""
    color_map = {
        'active': 'success',
        'pending': 'warning',
        'delayed': 'danger',
        'completed': 'primary',
        'cancelled': 'danger'
    }
    return color_map.get(status.lower(), 'normal')

def get_priority_color(priority: str) -> str:
    """Get color for priority level"""
    color_map = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'critical': 'danger'
    }
    return color_map.get(priority.lower(), 'normal')