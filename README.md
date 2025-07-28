# 🤖 Payment Ops Copilot

An AI-powered FastAPI application with PydanticAI that enables natural language querying of transaction data stored in PostgreSQL. The system augments user queries with dataset information, generates SQL queries, retrieves data, and provides AI-powered summaries and insights.


[![Watch the video](https://www.loom.com/share/42db4846da3b453190bb37304c944f20?sid=77e85dbb-0ef1-4c6d-9739-e5021d62bb5b)]

## 🌟 Features

- **Natural Language Queries**: Ask questions in plain English about your transaction data
- **Intelligent SQL Generation**: AI automatically generates optimized PostgreSQL queries
- **Data Augmentation**: System automatically includes dataset schema information for better query generation
- **AI-Powered Summaries**: Get comprehensive summaries and insights from retrieved data
- **Real-time Analysis**: Instant results with detailed explanations and recommendations
- **Beautiful UI**: Modern Streamlit interface with organized data display
- **PostgreSQL Integration**: Full database connectivity with efficient querying

## 🏗️ Architecture

The system follows a multi-step AI workflow:

1. **Query Augmentation**: User queries are enriched with dataset schema information
2. **SQL Generation**: PydanticAI generates optimized PostgreSQL queries
3. **Data Retrieval**: Execute queries against PostgreSQL database
4. **AI Summarization**: Pass retrieved data back to AI for analysis and insights
5. **Response Delivery**: Return comprehensive results with summaries, insights, and recommendations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key

### Installation

1. **Clone and setup**:

```bash
git clone <your-repo>
cd ivyhack
pip install -r requirements.txt
```

2. **Set up environment variables**:

```bash
# Create .env file
export OPENAI_API_KEY="your_openai_api_key_here"
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```

3. **Set up PostgreSQL database**:

```bash
# Make sure PostgreSQL is running, then:
python setup_database.py
```

4. **Start the FastAPI backend**:

```bash
python run_api.py
```

Or alternatively:

```bash
uvicorn api.main:app --reload --port 8001
```

5. **Launch the Streamlit frontend** (in a new terminal):

```bash
streamlit run app.py
```

6. **Open your browser** to `http://localhost:8501`

## 🗄️ Database Setup

The system currently uses a blockchain transaction database, with a schema designed for detailed financial, user, and compliance data. Support for additional data types and broader datasets is planned for future releases, enabling flexible integration beyond blockchain transactions.

### Main Query Endpoint

```
POST /api/query
```

Processes natural language queries through the complete AI workflow.

**Request**:

```json
{
  "query": "What is the status of transaction abc-123?"
}
```

**Response**:

```json
{
  "explanation": "Generated SQL query explanation",
  "data": [...], // Retrieved data rows
  "summary": "AI-generated summary",
  "insights": ["Key insight 1", "Key insight 2"],
  "recommendation": "Optional recommendation"
}
```

### Additional Endpoints

- `GET /api/health` - Health check
- `GET /api/schema` - Get database schema
- `POST /api/sql-only` - Generate SQL without execution

## 💡 Example Queries

Try these natural language queries:

- `"What is the status of transaction ddd0a123-aa80-486a-a551-4819b4452e71?"`
- `"Show me all failed transactions from the last week"`
- `"What are the most common error codes?"`
- `"Show me all transactions for user usr_611341"`
- `"Find all transactions with high AML risk scores"`
- `"Show me transactions that are pending KYC verification"`
- `"What are the largest fiat amounts converted today?"`
- `"Show me all transactions involving BNB token"`

## 🎯 AI Agents

The system uses two specialized PydanticAI agents:

### SQL Generation Agent

- Analyzes natural language queries
- Has full knowledge of database schema
- Generates optimized PostgreSQL queries
- Provides explanations and reasoning

### Data Summary Agent

- Analyzes retrieved transaction data
- Identifies patterns and anomalies
- Provides actionable insights
- Generates recommendations

## 📊 Frontend Features

The Streamlit interface includes:

- **Query Input**: Natural language text area with example queries
- **Schema Browser**: Organized view of available database columns
- **Tabbed Results**: Separate tabs for summary, data, insights, and technical details
- **Data Export**: Download results as CSV
- **Real-time Processing**: Live status updates during query processing

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Optional
OPENAI_MODEL=gpt-4  # Default model for AI agents
```

### Database Connection Formats

```bash
# Local PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/payment_ops

# Docker PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/payment_ops

# Cloud PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
DATABASE_URL=postgresql://username:password@your-db-host:5432/database_name
```

## 🐳 Docker Deployment

Create a `docker-compose.yml` for easy deployment:

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: payment_ops
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/payment_ops
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Verify PostgreSQL is running
   - Check DATABASE_URL format
   - Ensure database exists

2. **OpenAI API Errors**

   - Verify OPENAI_API_KEY is set
   - Check API key permissions
   - Monitor rate limits

3. **CSV Import Issues**

   - Ensure CSV files are in the project directory
   - Check file permissions
   - Verify data format matches schema

4. **Query Performance**
   - Database indexes are created automatically
   - Consider adding custom indexes for frequent queries
   - Monitor query execution times

### Debug Mode

Enable debug logging by setting:

```bash
export LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [PydanticAI](https://ai.pydantic.dev/)
- UI with [Streamlit](https://streamlit.io/)
- Database with [PostgreSQL](https://postgresql.org/)
- AI by [OpenAI](https://openai.com/)
