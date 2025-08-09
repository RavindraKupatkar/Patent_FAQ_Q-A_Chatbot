"""
Theme configuration for the Patent & BIS FAQ Assistant

This module contains theme colors, fonts, and styling configurations.
"""

class Theme:
    """Theme configuration class."""
    
    # Color palette
    COLORS = {
        # Primary colors
        'primary': '#667eea',
        'primary_dark': '#764ba2',
        'primary_light': '#a78bfa',
        
        # Secondary colors
        'secondary': '#0ea5e9',
        'secondary_dark': '#0284c7',
        'secondary_light': '#38bdf8',
        
        # Status colors
        'success': '#10b981',
        'success_bg': '#dcfce7',
        'warning': '#f59e0b',
        'warning_bg': '#fef3c7',
        'error': '#ef4444',
        'error_bg': '#fee2e2',
        'info': '#3b82f6',
        'info_bg': '#dbeafe',
        
        # Neutral colors
        'gray_50': '#f8fafc',
        'gray_100': '#f1f5f9',
        'gray_200': '#e2e8f0',
        'gray_300': '#cbd5e1',
        'gray_400': '#94a3b8',
        'gray_500': '#64748b',
        'gray_600': '#475569',
        'gray_700': '#334155',
        'gray_800': '#1e293b',
        'gray_900': '#0f172a',
        
        # Background colors
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_accent': '#f0f9ff',
        
        # Text colors
        'text_primary': '#1e293b',
        'text_secondary': '#64748b',
        'text_muted': '#94a3b8',
    }
    
    # Typography
    FONTS = {
        'primary': "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        'mono': "'JetBrains Mono', 'Fira Code', monospace",
    }
    
    # Spacing
    SPACING = {
        'xs': '0.25rem',
        'sm': '0.5rem',
        'md': '1rem',
        'lg': '1.5rem',
        'xl': '2rem',
        '2xl': '3rem',
        '3xl': '4rem',
    }
    
    # Border radius
    RADIUS = {
        'sm': '0.375rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
        'full': '9999px',
    }
    
    # Shadows
    SHADOWS = {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    }
    
    @classmethod
    def get_css_variables(cls):
        """Generate CSS custom properties from theme configuration."""
        css_vars = ":root {\n"
        
        # Colors
        for name, value in cls.COLORS.items():
            css_vars += f"  --color-{name.replace('_', '-')}: {value};\n"
        
        # Spacing
        for name, value in cls.SPACING.items():
            css_vars += f"  --spacing-{name}: {value};\n"
        
        # Border radius
        for name, value in cls.RADIUS.items():
            css_vars += f"  --radius-{name}: {value};\n"
        
        # Fonts
        for name, value in cls.FONTS.items():
            css_vars += f"  --font-{name}: {value};\n"
        
        css_vars += "}\n"
        return css_vars
    
    @classmethod
    def get_component_styles(cls):
        """Get component-specific styles."""
        return {
            'button_primary': f"""
                background: linear-gradient(135deg, {cls.COLORS['primary']}, {cls.COLORS['primary_dark']});
                color: white;
                border: none;
                border-radius: {cls.RADIUS['lg']};
                padding: {cls.SPACING['md']} {cls.SPACING['lg']};
                font-weight: 500;
                transition: all 0.2s ease;
                box-shadow: {cls.SHADOWS['md']};
            """,
            
            'card': f"""
                background: {cls.COLORS['bg_primary']};
                border: 1px solid {cls.COLORS['gray_200']};
                border-radius: {cls.RADIUS['xl']};
                padding: {cls.SPACING['lg']};
                box-shadow: {cls.SHADOWS['sm']};
            """,
            
            'chat_message_user': f"""
                background: linear-gradient(135deg, {cls.COLORS['primary']}, {cls.COLORS['primary_dark']});
                color: white;
                padding: {cls.SPACING['md']} {cls.SPACING['lg']};
                border-radius: {cls.RADIUS['2xl']} {cls.RADIUS['2xl']} {cls.RADIUS['sm']} {cls.RADIUS['2xl']};
                margin-left: 20%;
                box-shadow: {cls.SHADOWS['md']};
            """,
            
            'chat_message_assistant': f"""
                background: {cls.COLORS['bg_secondary']};
                border: 1px solid {cls.COLORS['gray_200']};
                padding: {cls.SPACING['lg']};
                border-radius: {cls.RADIUS['2xl']} {cls.RADIUS['2xl']} {cls.RADIUS['2xl']} {cls.RADIUS['sm']};
                margin-right: 20%;
                box-shadow: {cls.SHADOWS['sm']};
            """,
        }