# Frontend Mockup Design

## Context

Create static HTML/CSS mockup pages for the grade management system to serve as a visual reference standard for future AI-assisted development. These mockups will prevent arbitrary design decisions during implementation by providing precise visual specifications for layout, colors, spacing, and component styling.

## Purpose

- Establish a clear visual design language for the entire application
- Provide pixel-perfect reference for layout and styling
- Prevent AI from making arbitrary design choices during implementation
- Serve as a communication tool between stakeholders and developers
- Document the approved design before coding begins

## Scope

**In scope:**
- 4 core static HTML pages with complete visual design
- Shared layout structure (sidebar, top bar, main content area)
- Precise color scheme and typography specifications
- Mock data to demonstrate realistic content density
- Desktop-optimized layout (1920x1080)
- Light theme only

**Out of scope:**
- JavaScript interactivity (no page navigation, form submission, or dynamic updates)
- Backend integration or API calls
- Responsive mobile/tablet layouts
- Dark theme
- Accessibility features beyond semantic HTML
- Real data or database connections
- Authentication flows

## Technical Approach

**Implementation method:**
- Pure HTML5 + CSS3 (no frameworks or libraries)
- Self-contained files with inline CSS
- SVG icons embedded directly in HTML
- CSS Grid and Flexbox for layout
- CSS variables for consistent theming

**File structure:**
```
mockups/
├── dashboard.html              # Dashboard page
├── score-entry.html            # Score entry page
├── student-management.html     # Student management page
└── exam-management.html        # Exam management page
```

Each HTML file is completely independent and can be opened directly in a browser without a server.

## Design System

### Color Palette

```css
--primary: #14b8a6;           /* Teal primary color for accents */
--primary-light: #5eead4;     /* Light teal for hover states */
--primary-bg: #f0fdfa;        /* Very light teal for active backgrounds */
--bg-white: #ffffff;          /* White background for cards and sidebar */
--bg-gray: #f8fafc;           /* Light gray for main content area */
--text-dark: #1e293b;         /* Dark gray for primary text */
--text-gray: #64748b;         /* Medium gray for secondary text */
--text-light: #94a3b8;        /* Light gray for placeholder text */
--border: #e2e8f0;            /* Border color */
--shadow: 0 1px 3px rgba(0,0,0,0.1);  /* Card shadow */
--shadow-hover: 0 4px 6px rgba(0,0,0,0.1);  /* Hover shadow */
```

### Typography

- Font family: system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`)
- Base font size: 14px
- Headings: 
  - Page title: 24px, font-weight 600
  - Card title: 16px, font-weight 600
  - Section title: 14px, font-weight 600
- Body text: 14px, font-weight 400
- Small text: 12px (for labels, captions)

### Spacing Scale

- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px

### Border Radius

- Cards: 8px
- Buttons: 6px
- Inputs: 6px
- Avatar: 50% (circular)

## Layout Structure

### Overall Layout

```
┌──────────────────────────────────────────────────────────┐
│  Sidebar (240px)  │  Top Bar (full width, 60px height)   │
│                   ├──────────────────────────────────────┤
│  - Logo           │                                      │
│  - Navigation     │  Main Content Area                   │
│    Menu           │  (background: #f8fafc)               │
│                   │  (padding: 24px)                     │
│                   │                                      │
│                   │  [Cards and content here]            │
│                   │                                      │
└──────────────────────────────────────────────────────────┘
```

### Sidebar

- Width: 240px (fixed)
- Position: fixed left
- Background: #ffffff
- Border right: 1px solid #e2e8f0
- Height: 100vh

**Logo area:**
- Height: 60px
- Text: "成绩管理系统"
- Font size: 18px, font-weight 600
- Color: --text-dark
- Centered horizontally
- Border bottom: 1px solid #e2e8f0

**Navigation menu:**
- Menu items:
  1. 仪表盘 (Dashboard)
  2. 班级管理 (Class Management)
  3. 学生管理 (Student Management)
  4. 课程管理 (Course Management)
  5. 课程表管理 (Schedule Management)
  6. 考试管理 (Exam Management)
  7. 成绩录入 (Score Entry)
  8. 统计分析 (Statistics)
  9. 导入记录 (Import Records)
  10. 账户设置 (Account Settings)

**Menu item styling:**
- Height: 48px
- Padding: 0 24px
- Display: flex, align-items: center
- Gap between icon and text: 12px
- Icon size: 20px
- Font size: 14px
- Color: --text-gray

**Menu item states:**
- Default: transparent background
- Hover: background #f8fafc
- Active: 
  - Background: #f0fdfa
  - Text color: --primary
  - Left border: 3px solid --primary
  - Font weight: 500

### Top Bar

- Height: 60px
- Position: fixed top
- Left margin: 240px (sidebar width)
- Width: calc(100% - 240px)
- Background: #ffffff
- Border bottom: 1px solid #e2e8f0
- Display: flex, justify-content: space-between, align-items: center
- Padding: 0 24px

**Left section (search):**
- Search input:
  - Width: 320px
  - Height: 36px
  - Border: 1px solid --border
  - Border radius: 6px
  - Padding: 0 12px 0 36px (space for search icon)
  - Placeholder: "搜索..."
  - Background: #f8fafc

**Right section (user info):**
- Display: flex, align-items: center, gap: 16px
- Notification icon: 20px, color: --text-gray
- Avatar: 40px diameter, circular, background: --primary-light
- Teacher name: font-size 14px, color: --text-dark

### Main Content Area

- Margin left: 240px (sidebar width)
- Margin top: 60px (top bar height)
- Min height: calc(100vh - 60px)
- Background: #f8fafc
- Padding: 24px

**Card styling:**
- Background: #ffffff
- Border radius: 8px
- Box shadow: 0 1px 3px rgba(0,0,0,0.1)
- Padding: 20px
- Margin bottom: 24px (gap between cards)

## Page Specifications

### 1. Dashboard (dashboard.html)

**Summary cards (top section):**
- Layout: 4 cards in a row, equal width with gap: 24px
- Each card contains:
  - Icon (32px, colored with primary)
  - Label (12px, color: --text-gray, margin-bottom: 8px)
  - Value (32px, font-weight 600, color: --text-dark)
  - Trend indicator (optional, 12px, color: green/red)

**Mock data:**
1. 班级数量: 5
2. 学生数量: 156
3. 课程数量: 8
4. 待录入成绩: 23

**Today's schedule card:**
- Title: "今日课程表"
- Subtitle: "2026年5月21日 星期三"
- Table columns: 节次 | 时间 | 班级 | 课程 | 地点
- 5 rows of sample data:
  - 第1节 | 08:00-08:45 | 高一(1)班 | 数学 | 教学楼A201
  - 第2节 | 08:55-09:40 | 高一(2)班 | 英语 | 教学楼A203
  - 第3节 | 10:00-10:45 | 高一(1)班 | 物理 | 实验楼B301
  - 第4节 | 10:55-11:40 | 高一(3)班 | 化学 | 实验楼B302
  - 第5节 | 14:00-14:45 | 高一(2)班 | 语文 | 教学楼A205

**Recent exams card:**
- Title: "最近考试"
- Table columns: 考试名称 | 类型 | 学期 | 日期 | 操作
- 4 rows of sample data:
  - 期中考试 | 校考 | 2025-2026学年第二学期 | 2026-05-15 | [查看详情]
  - 第二次月考 | 月考 | 2025-2026学年第二学期 | 2026-04-28 | [查看详情]
  - 第一次月考 | 月考 | 2025-2026学年第二学期 | 2026-03-20 | [查看详情]
  - 期末考试 | 校考 | 2025-2026学年第一学期 | 2026-01-10 | [查看详情]

**Score overview card:**
- Title: "成绩概览"
- Subtitle: "期中考试 - 数学"
- 4 metrics in a row:
  - 平均分: 78.5
  - 最高分: 98
  - 最低分: 45
  - 缺考人数: 3

**Class average trend card:**
- Title: "班级平均分趋势"
- Simple CSS-based line chart showing 3 lines (3 classes)
- X-axis: 5 exams
- Y-axis: scores 0-100
- Legend: 高一(1)班, 高一(2)班, 高一(3)班

### 2. Score Entry (score-entry.html)

**Filter section (top):**
- Layout: horizontal flex with gap: 16px
- Components:
  - 考试选择: dropdown (width: 240px)
  - 班级选择: dropdown (width: 180px)
  - 科目选择: dropdown (width: 180px)
  - 查询按钮: primary button

**Score entry table:**
- Full width card
- Table columns: 学号 | 姓名 | 班级 | 分数 | 状态 | 备注
- Column widths: 120px | 100px | 120px | 100px | 120px | flex
- 15 rows of sample data with input fields:
  - 学号: text (e.g., "2024010101")
  - 姓名: text (e.g., "张三")
  - 班级: text (e.g., "高一(1)班")
  - 分数: number input (width: 80px)
  - 状态: select (正常/缺考/缓考/作弊/免考)
  - 备注: text input

**Bottom action bar:**
- Layout: flex, justify-content: space-between
- Left: "已选择 0 条记录"
- Right: 
  - 导入Excel按钮 (secondary)
  - 批量保存按钮 (primary)

### 3. Student Management (student-management.html)

**Top action bar:**
- Layout: flex, justify-content: space-between
- Left:
  - 添加学生按钮 (primary)
  - 导入Excel按钮 (secondary)
- Right:
  - 班级筛选: dropdown (width: 180px)
  - 搜索框: input (width: 240px)

**Student list table:**
- Table columns: 学号 | 姓名 | 性别 | 班级 | 状态 | 操作
- Column widths: 120px | 100px | 80px | 120px | 100px | 120px
- 20 rows of sample data:
  - 学号: "2024010101" to "2024010120"
  - 姓名: various Chinese names
  - 性别: 男/女
  - 班级: 高一(1)班, 高一(2)班, 高一(3)班
  - 状态: badge (在读/休学/转出)
  - 操作: [编辑] [删除] links

**Pagination:**
- Bottom of card
- Layout: flex, justify-content: space-between
- Left: "共 156 条记录"
- Right: page numbers (1 2 3 4 5 ... 8)

### 4. Exam Management (exam-management.html)

**Top action bar:**
- Layout: flex, justify-content: space-between
- Left:
  - 创建考试按钮 (primary)
- Right:
  - 学期筛选: dropdown (width: 240px)
  - 搜索框: input (width: 240px)

**Exam list table:**
- Table columns: 考试名称 | 类型 | 学期 | 参与班级 | 科目数 | 状态 | 操作
- Column widths: 180px | 100px | 200px | 120px | 80px | 100px | 180px
- 10 rows of sample data:
  - 考试名称: "期中考试", "第二次月考", etc.
  - 类型: badge (校考/月考/周测)
  - 学期: "2025-2026学年第二学期"
  - 参与班级: "3个班级"
  - 科目数: "9科"
  - 状态: badge (未开始/进行中/已结束)
  - 操作: [查看] [编辑] [删除] links

**Pagination:**
- Same as student management page
- "共 45 条记录"

## Component Specifications

### Buttons

**Primary button:**
- Background: --primary
- Color: white
- Padding: 8px 16px
- Border radius: 6px
- Font size: 14px
- Border: none
- Cursor: pointer
- Hover: background darken 10%

**Secondary button:**
- Background: white
- Color: --text-dark
- Padding: 8px 16px
- Border: 1px solid --border
- Border radius: 6px
- Font size: 14px
- Cursor: pointer
- Hover: background --bg-gray

### Form Inputs

**Text input:**
- Height: 36px
- Padding: 0 12px
- Border: 1px solid --border
- Border radius: 6px
- Font size: 14px
- Background: white
- Focus: border-color --primary, outline: none

**Select dropdown:**
- Same styling as text input
- Appearance: custom arrow icon

### Table

**Table styling:**
- Width: 100%
- Border collapse: collapse

**Table header:**
- Background: #f8fafc
- Font weight: 600
- Font size: 14px
- Color: --text-dark
- Padding: 12px 16px
- Border bottom: 1px solid --border
- Text align: left

**Table row:**
- Border bottom: 1px solid --border
- Hover: background #f8fafc

**Table cell:**
- Padding: 12px 16px
- Font size: 14px
- Color: --text-dark
- Vertical align: middle

### Badges

**Status badge:**
- Display: inline-block
- Padding: 4px 12px
- Border radius: 12px
- Font size: 12px
- Font weight: 500

**Badge variants:**
- Success (在读/正常): background #d1fae5, color #065f46
- Warning (休学/进行中): background #fef3c7, color #92400e
- Danger (转出/已结束): background #fee2e2, color #991b1b
- Info (未开始): background #dbeafe, color #1e40af

### Icons

Use inline SVG icons with consistent sizing:
- Navigation icons: 20px
- Action icons: 16px
- Status icons: 14px

Common icons needed:
- Dashboard: grid icon
- Students: users icon
- Classes: folder icon
- Courses: book icon
- Exams: clipboard icon
- Scores: edit icon
- Statistics: chart icon
- Settings: gear icon
- Search: magnifying glass
- Notification: bell
- Add: plus
- Edit: pencil
- Delete: trash
- View: eye

## Mock Data Guidelines

**Realistic content:**
- Use Chinese names, class names, and terminology
- Use realistic score ranges (0-100)
- Use current academic year (2025-2026)
- Use realistic dates (recent past)

**Data variety:**
- Mix of different statuses
- Range of scores (high, medium, low)
- Different class names
- Various exam types

**Content density:**
- Dashboard: moderate density, scannable
- Tables: 10-20 rows to show scrolling behavior
- Forms: realistic field counts

## Implementation Notes

**CSS organization:**
- CSS variables at the top
- Reset/base styles
- Layout styles (sidebar, top bar, main)
- Component styles (buttons, inputs, tables, badges)
- Page-specific styles
- Utility classes

**HTML structure:**
- Semantic HTML5 elements
- Consistent class naming (BEM-like)
- Proper heading hierarchy
- Accessible form labels

**Browser compatibility:**
- Target modern browsers (Chrome, Firefox, Safari, Edge)
- Use standard CSS Grid and Flexbox
- No vendor prefixes needed for target browsers

## Success Criteria

The mockups are successful if they:
1. Accurately represent the approved design system
2. Can be opened directly in any modern browser without errors
3. Display correctly at 1920x1080 resolution
4. Provide clear visual reference for all core pages
5. Use consistent spacing, colors, and typography throughout
6. Include realistic mock data that demonstrates content density
7. Serve as unambiguous reference for future implementation

## Future Considerations

After implementation begins:
- These mockups remain the source of truth for visual design
- Any design changes should update the mockups first
- Additional pages can follow the same design patterns
- Interactive prototypes can be built on top of these mockups
- Responsive layouts for mobile/tablet can reference these desktop designs
