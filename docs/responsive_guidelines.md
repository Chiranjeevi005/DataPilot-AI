# Responsive Design Guidelines

## Overview
DataPilot AI uses a mobile-first responsive design approach. This document outlines breakpoints, patterns, and best practices for creating responsive components.

## Breakpoints

We use Tailwind's standard breakpoints with explicit configuration:

```typescript
{
  'sm': '640px',   // Small tablets and large phones
  'md': '768px',   // Tablets  
  'lg': '1024px',  // Laptops and small desktops
  'xl': '1280px',  // Desktops
  '2xl': '1536px', // Large desktops
}
```

### Mobile-First Approach
Always write CSS/components for mobile first, then enhance for larger screens:

```tsx
// ✅ Correct - Mobile first
<div className="flex-col md:flex-row">

// ❌ Wrong - Desktop first  
<div className="flex-row md:flex-col">
```

## Test Viewports

Test all components on these standard viewports:

- **Mobile**: 375×812 (iPhone X)
- **Small Tablet**: 768×1024 (iPad)
- **Large Tablet**: 1024×1366
- **Laptop**: 1366×768
- **Desktop**: 1920×1080

## Component Patterns

### 1. Responsive Container

Use `ResponsiveContainer` for consistent padding and max-width:

```tsx
import ResponsiveContainer from '@/components/ResponsiveContainer';

<ResponsiveContainer maxWidth="xl">
  <YourContent />
</ResponsiveContainer>
```

**Props:**
- `maxWidth`: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full' (default: 'xl')
- `noPadding`: boolean (default: false)
- `className`: string (optional)

### 2. Sidebar Collapse Pattern

**Desktop (lg+)**: Persistent left sidebar
**Tablet (md)**: Collapsible mini-icon sidebar
**Mobile (sm-)**: Off-canvas panel (hamburger menu)

```tsx
// Sidebar visibility
<aside className={cn(
  "fixed inset-y-0 left-0 z-40",
  "w-64 lg:w-64",                    // Full width on desktop
  "md:w-16",                          // Mini on tablet
  "transform transition-transform",
  isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
)}>
```

### 3. Table → Card View Pattern

Tables should switch to card view on mobile for better readability:

```tsx
// Desktop: Table view
<div className="hidden md:block">
  <table>...</table>
</div>

// Mobile: Card view
<div className="md:hidden space-y-3">
  {data.map(item => (
    <div key={item.id} className="bg-white p-4 rounded-xl shadow-card">
      <div className="font-semibold">{item.name}</div>
      <div className="text-sm text-slate-600">{item.value}</div>
    </div>
  ))}
</div>
```

### 4. Responsive Charts (Recharts)

Always use `ResponsiveContainer` and adapt detail level:

```tsx
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <XAxis 
      dataKey="name"
      tick={{ fontSize: 12 }}
      interval={isMobile ? 2 : 0}  // Fewer ticks on mobile
    />
    <YAxis 
      tick={{ fontSize: 12 }}
      width={isMobile ? 40 : 60}   // Narrower on mobile
    />
    <Line type="monotone" dataKey="value" stroke="#2563EB" />
  </LineChart>
</ResponsiveContainer>
```

**Mobile Chart Settings:**
- Reduce tick count: `interval={2}` or `tickCount={5}`
- Hide gridlines: `grid={false}`
- Smaller fonts: `tick={{ fontSize: 10 }}`
- Narrower Y-axis: `width={40}`
- Hide legend on very small screens

### 5. Touch Targets

All interactive elements must meet 44×44px minimum:

```tsx
// ✅ Correct - Minimum touch target
<button className="min-h-touch min-w-touch p-3">
  <Icon size={20} />
</button>

// ❌ Wrong - Too small
<button className="p-1">
  <Icon size={16} />
</button>
```

Use Tailwind tokens:
- `min-h-touch` = 44px
- `min-w-touch` = 44px
- `spacing-touch` = 44px

### 6. Responsive Typography

Use fluid typography with `clamp()`:

```tsx
// Headings
<h1 className="text-h1">Main Heading</h1>      // clamp(1.875rem, 4vw, 3rem)
<h2 className="text-h2">Section Heading</h2>   // clamp(1.5rem, 3vw, 2.25rem)
<h3 className="text-h3">Subsection</h3>        // clamp(1.25rem, 2.5vw, 1.875rem)

// Body text
<p className="text-body-lg">Large body text</p>
<p className="text-body">Regular body text</p>
```

### 7. Grid Layouts

Use responsive grid columns:

```tsx
// 1 column mobile, 2 tablet, 3 desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>

// KPI cards: 2 mobile, 3 tablet, 4 desktop
<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
  {kpis.map(kpi => <KpiCard key={kpi.id} {...kpi} />)}
</div>
```

### 8. Modal/Overlay Patterns

Modals should be full-screen on mobile, centered on desktop:

```tsx
<div className={cn(
  "fixed inset-0 z-modal",
  "md:flex md:items-center md:justify-center md:p-4"
)}>
  <div className={cn(
    "bg-white",
    "h-full w-full md:h-auto md:w-auto md:max-w-2xl md:rounded-2xl",
    "overflow-y-auto"
  )}>
    {/* Modal content */}
  </div>
</div>
```

### 9. Navigation Patterns

**Hamburger Menu (Mobile)**:
```tsx
<button
  onClick={toggleMenu}
  className="lg:hidden min-h-touch min-w-touch"
  aria-expanded={isOpen}
  aria-controls="mobile-menu"
  aria-label="Toggle navigation"
>
  <Menu size={24} />
</button>
```

**Bottom Sheet (Mobile Alternative)**:
```tsx
<div className={cn(
  "fixed inset-x-0 bottom-0 z-50",
  "bg-white rounded-t-3xl shadow-2xl",
  "transform transition-transform",
  isOpen ? "translate-y-0" : "translate-y-full"
)}>
  {/* Bottom sheet content */}
</div>
```

## Accessibility Requirements

### 1. Focus Styles
All interactive elements have visible focus indicators:

```css
*:focus-visible {
  @apply outline-none ring-2 ring-primary ring-offset-2;
}
```

### 2. ARIA Attributes

```tsx
// Expandable sections
<button
  aria-expanded={isExpanded}
  aria-controls="section-id"
>

// Hidden content
<div
  id="section-id"
  aria-hidden={!isExpanded}
>

// Live regions for status updates
<div aria-live="polite" aria-atomic="true">
  Processing step {currentStep} of {totalSteps}
</div>
```

### 3. Keyboard Navigation

- All interactive elements must be keyboard accessible
- Tab order should be logical
- ESC key should close modals/overlays
- Enter/Space should activate buttons

## Performance Best Practices

### 1. Lazy Loading

```tsx
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  ssr: false,
  loading: () => <div>Loading chart...</div>
});
```

### 2. Image Optimization

```tsx
import Image from 'next/image';

<Image
  src="/hero.png"
  alt="Description"
  width={1200}
  height={600}
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
  priority={isAboveFold}
/>
```

### 3. Virtualization for Long Lists

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// For tables with 100+ rows
const rowVirtualizer = useVirtualizer({
  count: data.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
});
```

## Common Responsive Patterns

### Spacing

```tsx
// Responsive padding
<div className="p-4 md:p-6 lg:p-8">

// Responsive gaps
<div className="space-y-4 md:space-y-6 lg:space-y-8">
<div className="gap-3 md:gap-4 lg:gap-6">
```

### Visibility

```tsx
// Hide on mobile
<div className="hidden md:block">

// Show only on mobile
<div className="md:hidden">

// Show on tablet and up
<div className="hidden md:block">
```

### Flexbox Direction

```tsx
// Stack on mobile, row on desktop
<div className="flex flex-col md:flex-row">

// Reverse order on mobile
<div className="flex flex-col-reverse md:flex-row">
```

## Testing Checklist

- [ ] Component renders correctly on all 5 test viewports
- [ ] Touch targets are minimum 44×44px
- [ ] Text is readable (contrast ratio ≥ 4.5:1)
- [ ] Charts don't overflow and adapt tick density
- [ ] Tables switch to card view on mobile
- [ ] Modals are full-screen on mobile
- [ ] Sidebar collapses appropriately
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] ARIA attributes are correct
- [ ] Images have proper `sizes` attribute
- [ ] No horizontal scroll on any viewport

## Recharts Responsive Settings

### Mobile (< 640px)
```tsx
<ResponsiveContainer width="100%" height={250}>
  <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
    <XAxis 
      dataKey="name"
      tick={{ fontSize: 10 }}
      tickCount={5}
      interval="preserveStartEnd"
    />
    <YAxis 
      tick={{ fontSize: 10 }}
      width={35}
      tickCount={5}
    />
    <Tooltip />
    <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} />
  </LineChart>
</ResponsiveContainer>
```

### Tablet (640px - 1024px)
```tsx
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
    <XAxis 
      dataKey="name"
      tick={{ fontSize: 11 }}
      interval={1}
    />
    <YAxis 
      tick={{ fontSize: 11 }}
      width={45}
    />
    <Tooltip />
    <Legend />
    <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2} />
  </LineChart>
</ResponsiveContainer>
```

### Desktop (≥ 1024px)
```tsx
<ResponsiveContainer width="100%" height={400}>
  <LineChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
    <XAxis 
      dataKey="name"
      tick={{ fontSize: 12 }}
    />
    <YAxis 
      tick={{ fontSize: 12 }}
      width={60}
    />
    <Tooltip />
    <Legend />
    <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={2.5} />
  </LineChart>
</ResponsiveContainer>
```

## Resources

- [Tailwind Responsive Design](https://tailwindcss.com/docs/responsive-design)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Touch Target Sizes](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)
- [Recharts Documentation](https://recharts.org/en-US/api)
