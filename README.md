# RecallBox

### Your personal knowledge workspace.

RecallBox is a Django-powered personal knowledge management application designed to help you capture, organize, connect, and revisit information in one place.

From programming notes and code snippets to useful links and learning resources, RecallBox gives you a structured workspace to build and explore your personal knowledge library.

It goes beyond basic note-taking by allowing you to connect related notes, explore their relationships through an interactive Knowledge Graph, and revisit previous versions through revision history.

---

## Screenshots

### Home Dashboard
Your personal workspace for managing and exploring notes.

![RecallBox Home Dashboard](notes/docs/home%20page.png)

### Knowledge Graph
Explore relationships between notes through an interactive force-directed graph. Search, filter, select, and navigate connected knowledge.

![RecallBox Knowledge Graph](notes/docs/knowledge%20graph.png)

### Light Mode
A carefully designed alternative theme with readable colors and a consistent interface.

![RecallBox Light Mode](notes/docs/light%20mode.png)

### Create Note
Create and organize different types of notes.

![RecallBox Create Note](notes/docs/note%20create%20page.png)

### Note Linking
Connect related notes to build a structured knowledge network.

![RecallBox Note Linking](notes/docs/note%20linking.png)

### Note Detail
View and manage individual notes.

![RecallBox Note Detail](notes/docs/note%20view%20page.png)

### Revision History
Review previous versions of your notes and restore them when needed.

![RecallBox Revision History](notes/docs/notes%20revision.png)

### Notes Overview
Browse and manage your collection of notes.

![RecallBox Notes Overview](notes/docs/notes.png)

---

## Features

### Note Management
- Create, view, edit, archive, and delete notes.
- Support for text notes, code snippets, and external links.
- Store programming language information for code notes.
- Organize notes using tags.

### Organization and Discovery
- Search notes by their content.
- Filter notes by type, tag, and archive status.
- Paginate through your notes.
- Quickly find relevant information in your workspace.

### Knowledge Graph
- Visualize notes as nodes in an interactive graph.
- Explore directional relationships between linked notes.
- Display both connected and unconnected notes.
- Select notes and highlight their direct connections.
- Search and filter graph nodes by note type.
- Toggle connected-only view.
- Drag nodes, zoom, pan, and fit the graph to the screen.
- Navigate directly to a note from the graph.

### Note Relationships and History
- Link related notes together.
- Explore incoming and outgoing note connections.
- View previous note revisions.
- Restore earlier versions of notes.

### Authentication and Security
- User registration and authentication.
- Login-protected application features.
- User-level note ownership and access restrictions.
- Users can only access and manage their own notes and relationships.

### Interface and Experience
- Responsive interface for desktop and mobile screens.
- Dark and light themes.
- Consistent visual design across the application.
- Subtle animations and interactive UI elements.

---

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, Django |
| Database | SQLite (development) |
| Frontend | HTML, CSS, JavaScript |
| UI Framework | Bootstrap 5 |
| Graph Visualization | D3.js |
| Icons | Bootstrap Icons |
| Version Control | Git, GitHub |

---

## Getting Started

Follow these steps to run RecallBox locally.

### Prerequisites

- Python installed on your system.
- Git installed on your system.

### 1. Clone the repository

```bash
git clone https://github.com/rhutik123/RecallBox.git
cd RecallBox
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows — Command Prompt:**

```bash
.venv\Scripts\activate
```

**Windows — Git Bash:**

```bash
source .venv/Scripts/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open your browser and visit:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

You can now register an account and start using RecallBox.

---

## Running Tests

RecallBox includes automated Django tests covering important application functionality, including authentication, note ownership, permissions, and other application behavior.

Run the complete test suite:

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

---

## Database Design

The database schema and entity relationships are documented separately.

[View Database Design](notes/docs/database-design.md)

The application uses Django models and relationships to manage users, notes, tags, note connections, and revision history.

---

## Project Goals

RecallBox was developed as a practical Django learning and portfolio project.

The main objectives were to:

- Build a complete web application using Django.
- Develop a deeper understanding of Django models, ORM, relationships, and migrations.
- Implement authentication and object-level permissions.
- Work with Django forms, views, templates, and URL routing.
- Build and test application functionality using automated tests.
- Integrate an interactive JavaScript visualization with a Django backend.
- Create a polished, responsive user interface.
- Apply software development practices using Git and GitHub.

---

## Future Improvements

Potential enhancements for future development:

- AI-powered note summaries.
- Production deployment with a production-ready database.
- Additional knowledge discovery and organization features.
- Further performance and usability improvements.

---

## Author

**Rhutik Bhoir**

GitHub: [@rhutik123](https://github.com/rhutik123)

---

*RecallBox — Capture knowledge. Connect ideas. Build understanding.*