# Email Agent - AI-Powered Email Management System

A complete, production-ready email management system that combines a modern React frontend with a powerful Python backend for AI-driven email processing, reply generation, and intelligent conversation tracking.

## Features

- **AI-Powered Email Processing**: Automatically analyze and process emails using OpenAI GPT-4
- **Smart Reply Generation**: Generate contextual, professional email replies
- **Thread Memory**: Intelligent conversation tracking with persistent memory
- **Gmail Integration**: Full Gmail API integration for reading and sending emails
- **Modern UI**: Professional React/Next.js interface with Tailwind CSS
- **Real-time Updates**: Live email fetching and processing status
- **Demo Mode**: Works without backend for testing and demonstration

## Architecture

### Frontend (Next.js/React)
- Modern, responsive email management interface
- Real-time communication with Python backend
- Professional design with Tailwind CSS and shadcn/ui components
- Automatic fallback to demo mode when backend unavailable

### Backend (Python/FastAPI)
- Gmail API integration for email operations
- OpenAI integration for AI-powered email processing
- SQLite database for persistent storage
- RESTful API endpoints for frontend communication
- Comprehensive error handling and logging

## Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.8+
- **Gmail API credentials** (credentials.json)
- **OpenAI API key**

## Complete Setup Guide

### Step 1: Clone and Setup Project Structure

\`\`\`bash
# The project structure should look like this:
email-agent/
├── app/                    # Next.js app directory
├── components/             # React components
├── lib/                   # Utilities and API client
├── backend/               # Python backend
│   ├── agent/            # Core agent logic
│   │   ├── functions.py  # AI functions and database operations
│   │   ├── gmail.py      # Gmail API integration
│   │   └── llm_agent.py  # Main AI agent logic
│   ├── run_backend.py    # FastAPI server
│   ├── requirements.txt  # Python dependencies
│   ├── .env              # Environment variables template
│   └── credentials.json  # Gmail credentials template
└── README.md
\`\`\`

### Step 2: Backend Setup

1. **Install Python dependencies:**
   \`\`\`bash
   cd backend
   pip install -r requirements.txt
   \`\`\`

2. **Set up environment variables:**
   \`\`\`bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your_openai_api_key_here
   \`\`\`

3. **Configure Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create credentials (OAuth 2.0 Client ID)
   - Download credentials and save as `backend/credentials.json`

4. **Start the Python backend:**
   \`\`\`bash
   python run_backend.py
   \`\`\`
   The backend will run on http://localhost:8000

### Step 3: Frontend Setup

1. **Install Node.js dependencies:**
   \`\`\`bash
   # From project root
   npm install
   \`\`\`

2. **Start the Next.js development server:**
   \`\`\`bash
   npm run dev
   \`\`\`
   The frontend will run on http://localhost:3000

### Step 4: First Run Authentication

1. Open http://localhost:3000 in your browser
2. The interface will show "Demo Mode" initially
3. Start the Python backend (Step 2.4)
4. Click "Refresh" - you'll be prompted to authenticate with Gmail
5. Complete OAuth flow in your browser
6. The system will create `token.json` automatically

## Usage Guide

### Basic Operations
1. **Access Interface**: Open http://localhost:3000
2. **Refresh Inbox**: Click "Refresh" to fetch latest unread emails
3. **Generate Drafts**: Click "Generate Draft" on any email for AI-powered replies
4. **Send Replies**: Edit and send replies directly from the interface
5. **Run Agent**: Use "Run Agent" to automatically process multiple emails
6. **View Thread Memory**: Check sidebar for conversation context and insights

### Advanced Features
- **Thread Tracking**: Automatic conversation history and context preservation
- **AI Decision Making**: Intelligent action selection (reply, schedule, summarize, todo)
- **Meeting Scheduling**: Extract meeting requests and schedule automatically
- **Todo Extraction**: Identify and track actionable items from emails

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/emails` | Fetch unread emails |
| GET | `/api/emails/{id}/draft` | Generate AI reply draft |
| POST | `/api/emails/reply` | Send email reply |
| GET | `/api/threads/{id}` | Get thread messages and memory |
| POST | `/api/agent/process-inbox` | Run AI agent on emails |
| POST | `/api/inbox/refresh` | Refresh and fetch latest emails |

## Project Structure

\`\`\`
email-agent/
├── app/
│   ├── layout.tsx          # Root layout with fonts
│   ├── page.tsx           # Main page component
│   └── globals.css        # Global styles and design tokens
├── components/
│   ├── email-management-interface.tsx  # Main interface
│   ├── email-card.tsx                 # Email display component
│   ├── thread-memory-sidebar.tsx      # Thread memory display
│   └── ui/                           # shadcn/ui components
├── lib/
│   ├── api-client.ts      # Frontend API client
│   └── utils.ts          # Utility functions
├── backend/
│   ├── agent/
│   │   ├── functions.py   # Core AI functions
│   │   ├── gmail.py      # Gmail API wrapper
│   │   └── llm_agent.py  # Main agent logic
│   ├── run_backend.py    # FastAPI server
│   ├── requirements.txt  # Python dependencies
│   └── .env.example     # Environment template
└── package.json         # Node.js dependencies
\`\`\`

## Deployment

### Development
\`\`\`bash
# Terminal 1: Start backend
cd backend && python run_backend.py

# Terminal 2: Start frontend
npm run dev
\`\`\`

### Production
1. **Backend**: Deploy FastAPI app using uvicorn, gunicorn, or Docker
2. **Frontend**: Deploy Next.js app to Vercel, Netlify, or similar
3. **Database**: SQLite for development, PostgreSQL for production
4. **Environment**: Set production environment variables

## Configuration

### Environment Variables
\`\`\`bash
# Backend (.env)
OPENAI_API_KEY=your_openai_api_key
DATABASE_PATH=assistant.db
API_HOST=0.0.0.0
API_PORT=8000

# Frontend (if needed)
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

### Gmail API Setup
1. Enable Gmail API in Google Cloud Console
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs: `http://localhost`
4. Download credentials as `credentials.json`

## Troubleshooting

### Common Issues
- **"Demo Mode" showing**: Backend not running or not accessible
- **Gmail authentication fails**: Check credentials.json and OAuth setup
- **API errors**: Verify OpenAI API key and quota
- **Database errors**: Ensure write permissions for SQLite file

### Debug Mode
The interface includes debug logging - check browser console for detailed error messages.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Will be updated.

## Acknowledgments

- OpenAI for GPT-4 API
- Google for Gmail API
- Next.js framework
- shadcn/ui for component library
