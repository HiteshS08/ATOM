# ATOM Frontend with Shadcn UI Styling

This frontend has been updated to use the styling from the multi-agent-system folder, which is based on Tailwind CSS and follows the Shadcn UI design system.

## Setup Instructions

1. Install the new dependencies:

```bash
cd frontend
npm install
```

This will install all the required packages including:
- tailwindcss
- postcss
- autoprefixer
- class-variance-authority
- clsx
- lucide-react
- tailwind-merge
- tailwindcss-animate

2. Start the development server:

```bash
npm start
```

## Styling System

The styling system is based on:

- **Tailwind CSS**: A utility-first CSS framework
- **CSS Variables**: For theme customization (light/dark mode)
- **Shadcn UI**: A component design system

### Key Features

- **Dark Mode by Default**: The UI is designed with a dark theme by default
- **Component-Based Design**: All UI elements are built as reusable components
- **Responsive Layout**: The layout adapts to different screen sizes
- **Custom UI Components**: Button, Card, Badge, Textarea, ScrollArea components

### File Structure

- `tailwind.config.js`: Tailwind configuration
- `postcss.config.js`: PostCSS configuration
- `src/globals.css`: Global styles and CSS variables
- `src/lib/utils.js`: Utility functions for styling
- `src/components/ui/`: UI components

## Notes

- The styling is now completely based on Tailwind CSS instead of Bootstrap
- The UI follows a modern, clean design with proper spacing and typography
- All components are responsive and accessible