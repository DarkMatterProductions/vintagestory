# Design System Update - Visual Guide

## Color Palette Changes

### Before (Old Theme)
```
Primary Color:      #8B4513 (Saddle Brown)
Secondary Color:    #D2691E (Chocolate)
Success Color:      #2ecc71 (Emerald Green)
Danger Color:       #e74c3c (Alizarin Red)
Warning Color:      #f39c12 (Orange)
Background:         #1a1a1a (Very Dark)
```

### After (New Theme)
```
Brand Primary:      rgb(143, 206, 0) - Vintage Story Green
Primary Button:     rgb(23, 126, 201) - Professional Blue
Success:            #2C8C69 (Teal Green)
Danger:             #C53030 (Deep Red)
Warning:            #DD6B20 (Burnt Orange)
Info:               #2981bf (Azure Blue)
Background:         rgb(237, 240, 244) - Light Gray
```

## Visual Changes

### Header
- **Background:** Dark (#0f0f0f) → Light White (#ffffff)
- **Text Color:** Light (#ecf0f1) → Dark (#2d3748)
- **Border:** Brown → Green (brand primary)
- **Shadow:** Heavy dark → Subtle light

### Cards
- **Background:** Dark Blue-Gray (#2c3e50) → Clean White (#ffffff)
- **Border:** Heavy dark (#34495e) → Subtle light (rgba)
- **Shadow:** Heavy dark → Professional light shadow
- **Border Radius:** 8px → Consistent with design system

### Buttons
#### Primary Button
- **Background:** Brown (#8B4513) → Professional Blue (rgb(23, 126, 201))
- **Hover:** Darker Brown → Brighter Blue with shadow
- **Text:** White (maintained)

#### Secondary Button
- **Background:** Gray (#95a5a6) → Light Gray (#f0f4f8)
- **Text:** White → Dark Gray (#7f858d)

#### Danger Button
- **Background:** Red (#e74c3c) → Deep Red (#C53030)
- **Maintained:** Consistent danger signaling

### Forms
#### Input Fields
- **Background:** Dark (#1e1e1e) → Light (#f7fafcf)
- **Border:** Dark gray → Light gray with better contrast
- **Focus State:** Brown border → Blue border with shadow glow
- **Text Color:** Light → Dark for better readability

### Console
- **Background:** Very Dark (#1e1e1e) → Dark Gray (rgb(45, 55, 72))
- **Text:** Light (maintained for readability)
- **Scrollbar:** Brown → Green (brand)
- **Syntax Colors:**
  - System: Orange → Burnt Orange (#DD6B20)
  - Command: Blue (#3498db) → Azure Blue (#2981bf)
  - Success: Emerald → Teal (#2C8C69)
  - Error: Red → Deep Red (#C53030)

### Status Badges
#### Connected
- **Background:** Solid green → Light green (#e3f3ec)
- **Text:** White → Dark green (#2C8C69)
- **Border:** None → 1px solid dark green

#### Disconnected
- **Background:** Gray → Light gray (#f0f4f8)
- **Text:** White → Dark gray (#7f858d)
- **Border:** None → 1px solid dark gray

### Messages
All message types now have:
- Light background with matching color
- Solid border in darker shade
- Better contrast and readability

**Success:** Green tinted background (#e3f3ec) with dark green text
**Error:** Red tinted background (#FFF5F5) with dark red text
**Warning:** Orange tinted background (#FFFAF0) with burnt orange text
**Info:** Blue tinted background (#e9f0f5) with azure blue text

## Spacing Improvements

### Old System
- Hard-coded pixel values (1rem, 2rem, etc.)
- Inconsistent spacing throughout

### New System
- Standardized spacing scale (--sp-0 through --sp-10)
- Consistent padding: --sp-3 (12px), --sp-4 (16px), --sp-6 (24px)
- Consistent margins using the same scale
- Predictable visual rhythm

## Typography

### Maintained
- Font family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- Console: 'Courier New', monospace

### Enhanced
- Better color contrast ratios
- Standardized size scale (--size-1 through --size-8)
- Improved readability on light backgrounds

## Accessibility Improvements

1. **Color Contrast:** All text now meets WCAG AA standards
2. **Focus States:** Enhanced with blue outline and proper offset
3. **Keyboard Navigation:** Visible focus indicators on all interactive elements
4. **Status Colors:** Distinct colors with sufficient contrast

## Professional Appearance

The new theme transforms the RCon client from a dark, gaming-style interface to a professional, modern web application while maintaining the Vintage Story brand identity through:

- Clean white backgrounds for content areas
- Professional blue for primary actions
- Vintage Story green as the brand accent
- Subtle shadows and rounded corners
- Consistent spacing and sizing
- Better visual hierarchy

## Mobile Responsiveness

Maintained and enhanced with:
- Consistent spacing that scales properly
- Adaptive card padding
- Flexible layouts using the spacing system

## Theme Customization

The new CSS variable system makes it easy to:
- Switch between light/dark themes
- Adjust spacing globally
- Change brand colors
- Customize border radius
- Modify shadow intensities

All without touching individual component styles!

