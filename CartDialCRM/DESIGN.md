---
version: alpha
colors:
  background: '#edf2f7'
  surface: '#ffffff'
  ink: '#172c45'
  muted: '#52657a'
  navy: '#112b46'
  navy_hover: '#1e4163'
  teal: '#087f83'
  teal_hover: '#066568'
  border: '#c8d4e0'
  stripe: '#f4f7fb'
  blue: '#285ea7'
  green: '#146745'
  red: '#a33246'
  gold: '#f3c475'
  disabled: '#dce4eb'
  header_text: '#d6e3ef'
  teal_tint: '#e3f5f1'
  blue_tint: '#e7effc'
  gold_tint: '#fff3dc'
  gold_ink: '#805219'
  white: '#ffffff'
typography:
  sans:
    fontFamily: 'Segoe UI'
omitted:
  - section: rounded
    reason: Native desktop controls own geometry.
  - section: spacing
    reason: Tk layout is measured in desktop pixels.
  - section: components
    reason: Native controls use the shared theme adapter.
---
## Overview
A polished appointment desk for a cart advertising caller. Product interface,
English, Windows laptop. The signature is a navy masthead with a teal rule and
three tinted activity tiles; surrounding forms stay quiet and readable.
## Colors
Runtime source: theme.py COLORS. apply_theme maps roles to ttk styles, native
text fields, dropdown popups, and scrollbars. App uses these same tokens for
header, metrics, and row tags. No screen-local palette. Navy anchors hierarchy,
teal identifies primary actions, blue indicates callbacks, green appointments,
and red do-not-call records. Status text remains visible alongside color.
## Typography
Segoe UI 10 controls; 27 bold masthead; 25 bold metrics; 23 bold dialog titles;
11 for note content. Numerical summaries have dedicated colored panels.
## Layout
Masthead, action toolbar, business-type summary, activity date, three metrics,
search/filter, bounded scrollable table, pagination, and feedback. Main window
1180 by 800 initially, resizable to 920 by 650. Lead cards retain their tabs.
## Elevation & Depth
Flat tinted tiles and native modal windows. No fake shadows or animation.
## Shapes
Rectangular native controls with deliberate padding and visible focus states.
## Components
Primary.TButton commits/adds records; Navy.TButton opens the call form. Shared
apply_theme owns entries, readonly Comboboxes, selected tabs, dark table headers,
selected rows and visible scrollbars. Native controls retain keyboard behavior.
## Do's and Don'ts
Keep phone numbers visible and selection legible. Do not convey status only by
color. Preserve all business data and call-count behavior during theme changes.
