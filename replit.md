# Python Hostfly

## Overview

Python Hostfly is a cloud-based platform for hosting and running Python projects 24/7. It enables users to deploy Python bots, scripts, and applications with real-time log monitoring, environment variable management, and package installation capabilities. The platform provides a developer-focused interface inspired by modern development tools like GitHub, Vercel, and Railway.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework & Build System**
- **React 18** with TypeScript for type-safe component development
- **Vite** as the build tool and development server with hot module replacement
- **Wouter** for lightweight client-side routing (no React Router dependency)

**UI Component Library**
- **Shadcn/ui** with Radix UI primitives for accessible, customizable components
- **Tailwind CSS** for utility-first styling with custom design tokens
- **New York** style variant selected for Shadcn components
- Custom theming system supporting light/dark modes with CSS variables

**Design System**
- Typography: Inter for UI text, JetBrains Mono for code/technical content
- Developer tool aesthetics with terminal-inspired elements
- Spacing based on Tailwind's 2/4/6/8/12 unit system
- Information-dense layouts without clutter

**State Management**
- **TanStack Query (React Query)** for server state management and caching
- Custom query client with infinite stale time and disabled automatic refetching
- Session-based authentication state via HTTP-only cookies
- React hooks for local component state

### Backend Architecture

**Server Framework**
- **Express.js** on Node.js for HTTP server and API routing
- TypeScript with ES modules for type safety and modern JavaScript features
- Session-based authentication using `express-session` with PostgreSQL store
- WebSocket server for real-time log streaming

**Process Management**
- Custom `PythonProcessManager` class for spawning and managing Python processes
- Runtime directory structure: `runtime/{repositoryId}/` for isolated execution environments
- Real-time log capture from stdout/stderr of Python processes
- Process lifecycle management (start/stop) with status tracking

**File System Operations**
- In-memory file tree representation stored in database
- Physical file materialization to `runtime/` directories when executing
- Support for file upload, creation, editing, and deletion
- Directory hierarchy support with path-based organization

**API Design**
- RESTful endpoints under `/api/` namespace
- JSON request/response format
- Request logging middleware with response capture
- Zod schemas for input validation (shared between client/server)

### Data Storage Solutions

**Database**
- **PostgreSQL** via Neon serverless driver with WebSocket support
- **Drizzle ORM** for type-safe database queries and schema management
- Connection pooling for efficient database connections

**Schema Design**
- `users`: Authentication and profile data (email/password with bcrypt hashing)
- `repositories`: Project metadata (name, description, main file, Python version, status)
- `files`: File content and structure (name, path, content, size, isDirectory flag)
- `environment_variables`: Key-value pairs scoped to repositories
- `sessions`: Express session storage (required for session-based auth)

**Data Relationships**
- Users own multiple repositories (one-to-many)
- Repositories contain multiple files and environment variables (one-to-many)
- Cascade deletion: removing a repository deletes associated files and environment variables

### Authentication & Authorization

**Authentication Strategy**
- Session-based authentication with HTTP-only cookies (no JWT tokens)
- bcrypt password hashing (10 rounds) for secure credential storage
- PostgreSQL-backed session store with 7-day TTL
- `isAuthenticated` middleware for protecting routes

**Security Considerations**
- Session secret from environment variable (`SESSION_SECRET`)
- Trust proxy enabled for deployment behind reverse proxies
- CSRF protection through same-origin policy and session validation
- Password validation enforced via Zod schemas (minimum 8 characters)

### External Dependencies

**Third-Party Services**
- **Neon Database**: Serverless PostgreSQL hosting with WebSocket support
- **Google Fonts**: Inter and JetBrains Mono font families

**NPM Packages**
- **Core**: express, react, react-dom, drizzle-orm, @neondatabase/serverless
- **UI Components**: @radix-ui/* primitives, @tanstack/react-query
- **Validation**: zod, drizzle-zod, @hookform/resolvers
- **Build Tools**: vite, typescript, tailwindcss, postcss
- **Utilities**: bcryptjs, ws (WebSocket), adm-zip (archive handling)
- **Dev Tools**: @replit/* plugins for Replit-specific features

**Python Runtime**
- Executes user Python code using system Python interpreter
- Support for pip package installation via subprocess spawn
- Configurable Python version per repository (default: 3.11)

**Development Environment**
- Replit-specific Vite plugins for error handling and development banners
- Runtime error modal overlay for better DX
- Source maps enabled for debugging