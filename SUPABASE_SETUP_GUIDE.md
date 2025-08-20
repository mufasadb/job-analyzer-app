# Local Supabase + MCP Server Setup Guide

This guide documents the complete setup of a local Supabase instance with an MCP (Model Context Protocol) server for integration with Claude Code and other AI agents.

## 🏗️ Setup Summary

### What was installed:
1. **Supabase CLI** - Downloaded binary for local development
2. **Local Supabase Project** - Initialized in `./supabase/` directory
3. **Supabase MCP Server** - npm package `supabase-mcp` for Claude integration
4. **Configuration Files** - MCP config and environment files

### Project Structure:
```
/Users/danielbeach/Code/agent_apps/applying_agent/
├── supabase-cli                    # Supabase CLI binary
├── supabase/                       # Supabase project configuration
│   └── config.toml                 # Main configuration file
├── mcp-config.json                 # MCP server configuration for Claude Code
├── .env.supabase                   # Environment variables for local Supabase
├── test-supabase-connection.js     # Connection test script
└── node_modules/                   # Contains supabase-mcp package
```

## 🚀 Quick Start Commands

### Start Supabase Services:
```bash
./supabase-cli start
```

### Stop Supabase Services:
```bash
./supabase-cli stop
```

### Check Status:
```bash
./supabase-cli status
```

### Test Connection:
```bash
node test-supabase-connection.js
```

## 📊 Service URLs & Connection Details

When Supabase is running, the following services are available:

| Service | URL | Purpose |
|---------|-----|---------|
| **API URL** | http://127.0.0.1:54321 | Main REST API endpoint |
| **GraphQL URL** | http://127.0.0.1:54321/graphql/v1 | GraphQL endpoint |
| **Storage URL** | http://127.0.0.1:54321/storage/v1/s3 | File storage (S3-compatible) |
| **Studio URL** | http://127.0.0.1:54323 | Web-based database admin interface |
| **Inbucket URL** | http://127.0.0.1:54324 | Email testing interface |
| **Database URL** | postgresql://postgres:postgres@127.0.0.1:54322/postgres | Direct PostgreSQL connection |

### Authentication Keys:
- **Anonymous Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU`

### S3 Storage Credentials:
- **Access Key**: `625729a08b95bf1b7ff351a663f3a23c`
- **Secret Key**: `850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907`
- **Region**: `local`

## 🤖 Using with Claude Code (MCP)

### Configuration File: `mcp-config.json`
The MCP server is configured to connect to your local Supabase instance:

```json
{
  "mcpServers": {
    "supabase-local": {
      "command": "npx",
      "args": ["-y", "supabase-mcp@latest", "supabase-mcp-claude"],
      "env": {
        "SUPABASE_URL": "http://127.0.0.1:54321",
        "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        "MCP_API_KEY": "local-dev-key-12345"
      }
    }
  }
}
```

### Available MCP Tools:
Once connected, Claude Code can use these Supabase operations:

1. **queryDatabase** - Query data with filters
2. **insertData** - Insert new records
3. **updateData** - Update existing records
4. **deleteData** - Delete records
5. **listTables** - List all available tables

### Example Usage in Claude Code:
```bash
# In Claude Code, you can now run commands like:
"Create a users table in the local Supabase database"
"Insert a test user with name 'John Doe' and email 'john@example.com'"
"Query all users from the users table"
```

## 🔧 Configuration Details

### Analytics Disabled
Analytics service has been disabled in `/Users/danielbeach/Code/agent_apps/applying_agent/supabase/config.toml` to avoid health check issues:
```toml
[analytics]
enabled = false
```

### Main Ports:
- **54321**: REST API and main services
- **54322**: PostgreSQL database  
- **54323**: Supabase Studio (web UI)
- **54324**: Inbucket (email testing)

## 🧪 Testing & Verification

### Connection Test Script
Run the provided test script to verify everything is working:
```bash
node test-supabase-connection.js
```

### Manual Testing
1. **Database Connection**: 
   ```bash
   psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT version();"
   ```

2. **REST API**:
   ```bash
   curl -s http://127.0.0.1:54321/rest/v1/ -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
   ```

3. **Web Interface**: Visit http://127.0.0.1:54323 for the Supabase Studio

## 🔒 Security Notes

**⚠️ IMPORTANT**: These are development credentials for local use only!
- Never use these keys in production
- The JWT secret and API keys are demo values
- The setup is configured for local development only

## 🛠️ Troubleshooting

### Common Issues:

1. **Services won't start**: 
   - Check if Docker is running
   - Ensure ports 54321-54324 are not in use
   - Try: `./supabase-cli stop && ./supabase-cli start`

2. **MCP connection fails**:
   - Verify Supabase services are running (`./supabase-cli status`)
   - Check that the MCP_API_KEY is set in the configuration
   - Ensure `supabase-mcp` package is installed

3. **Database connection issues**:
   - Verify PostgreSQL is accessible on port 54322
   - Use the test script to diagnose: `node test-supabase-connection.js`

4. **Docker container conflicts**:
   - Clean up containers: `docker container prune -f`
   - Remove networks: `docker network prune -f`

### Useful Commands:
```bash
# View Supabase logs
./supabase-cli logs

# Reset database
./supabase-cli db reset

# View Docker containers
docker ps | grep supabase
```

## 📚 Next Steps

1. **Create your first table** via Studio (http://127.0.0.1:54323)
2. **Test MCP integration** with Claude Code using the configured server
3. **Develop your application** using the local Supabase APIs
4. **Set up migrations** in the `supabase/migrations/` directory for version control

---

🎉 **Your local Supabase instance with MCP integration is now ready for development!**