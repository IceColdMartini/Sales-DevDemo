# Sales Agent Microservice

A sophisticated AI-powered sales agent microservice that receives customer messages from a Routing Agent, analyzes customer intent, recommends products, and determines when customers are ready to make a purchase.

## Features

- **Intelligent Product Matching**: Uses Azure OpenAI to extract keywords and match them with products based on similarity scoring (≥70% threshold)
- **Conversation Memory**: Maintains conversation history (last 10 exchanges) for contextual responses
- **Purchase Intent Detection**: Automatically detects when customers are ready to buy
- **Dual Database Architecture**:
  - PostgreSQL for structured product data
  - MongoDB for unstructured conversation history
- **Smart Response Generation**: Context-aware responses with sophisticated prompt engineering
- **RESTful API**: Clean API interface for integration with Routing Agent

## Architecture

```
Routing Agent → Sales Agent → Database → AI Service → Response → Routing Agent
```

### Data Flow

1. **Incoming Message**: Routing Agent sends customer message with sender ID
2. **Context Retrieval**: Fetch conversation history and product catalog
3. **Keyword Extraction**: AI extracts relevant keywords from customer message
4. **Product Matching**: Match keywords with product tags using similarity scoring
5. **Response Generation**: Generate contextual response based on conversation stage
6. **Purchase Detection**: Determine if customer is ready to buy
7. **Response Delivery**: Send response back with product recommendations and readiness flag

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+
- Azure OpenAI API access

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Sales-DevDemo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup**
   ```bash
   # Start PostgreSQL and MongoDB
   # Execute the init-db.sql script in PostgreSQL
   psql -U your_user -d sales_db -f init-db.sql
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Reference

### Webhook Endpoint

**POST** `/api/webhook`

Receives customer messages from Routing Agent and returns AI-generated responses.

**Request Body:**
```json
{
  "sender": "facebook_profile_id",
  "recipient": "page_id",
  "text": "customer_message"
}
```

**Response:**
```json
{
  "sender": "facebook_profile_id",
  "product_interested": "Product Name",
  "response_text": "AI-generated response",
  "is_ready": false
}
```

**Response Fields:**
- `sender`: Customer's unique profile ID
- `product_interested`: Name of the product customer is most interested in (null if none)
- `response_text`: AI-generated response to send back to customer
- `is_ready`: Boolean indicating if customer is ready to purchase (triggers handover to onboarding)

### Additional Endpoints

**GET** `/api/webhook/status/{sender_id}`
- Get conversation statistics for a specific customer

**DELETE** `/api/webhook/conversation/{sender_id}`
- Delete conversation history (for testing/reset)

**GET** `/health`
- Health check with database connectivity status

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_*` | PostgreSQL connection settings | localhost:5432 |
| `MONGO_*` | MongoDB connection settings | mongodb://localhost:27017 |
| `AZURE_OPENAI_*` | Azure OpenAI API configuration | Required |
| `MAX_CONVERSATION_HISTORY` | Max conversation messages to retain | 20 |
| `SIMILARITY_THRESHOLD` | Product matching threshold | 0.7 |
| `MAX_RELEVANT_PRODUCTS` | Max products to consider | 3 |

### Database Schema

#### Products Table (PostgreSQL)
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    sale_price NUMERIC(10, 2),
    stock_count INTEGER DEFAULT 0,
    image_url VARCHAR(255),
    images TEXT[],
    rating NUMERIC(3, 2) DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    category_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    product_tag TEXT[]  -- Key field for product matching
);
```

#### Conversations Collection (MongoDB)
```json
{
  "sender_id": "facebook_profile_id",
  "conversation": [
    {"role": "user", "content": "message"},
    {"role": "assistant", "content": "response"}
  ],
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "message_count": 10
}
```

## AI Service Details

### Keyword Extraction
- Analyzes customer messages using Azure OpenAI
- Extracts relevant keywords based on product context
- Focuses on product categories, features, and user intent

### Product Matching Algorithm
1. **Similarity Scoring**: Compare extracted keywords with product tags
2. **Exact Matches**: Full keyword-tag matches (weight: 1.0)
3. **Partial Matches**: Substring matches (weight: 0.5)
4. **Threshold Filtering**: Only products with ≥70% similarity
5. **Ranking**: Sort by similarity score and product rating

### Response Generation Strategy

#### First Interaction
- Warm welcome message
- Understand customer needs
- Present relevant products

#### Ongoing Conversation
- Context-aware responses
- Handle objections gracefully
- Suggest alternatives if uninterested
- Guide toward purchase decision

#### Purchase Ready Detection
- Analyze conversation for purchase signals
- Look for definite interest expressions
- Detect questions about purchase process
- Trigger handover when ready

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

The `docker-compose.yml` includes:
- Sales Agent API service
- PostgreSQL database
- MongoDB database
- Environment configuration

## Testing

### Sample Request
```bash
curl -X POST "http://localhost:8000/api/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user_123",
    "recipient": "page_456", 
    "text": "I am looking for a good perfume"
  }'
```

### Expected Response
```json
{
  "sender": "test_user_123",
  "product_interested": "Wild Stone Code Platinum Perfume",
  "response_text": "I'd be happy to help you find the perfect fragrance! Based on what you're looking for, I recommend our Wild Stone Code Platinum Perfume. It's a premium long-lasting perfume with masculine woody notes, perfect for special occasions. It's currently on sale for ₹450 (was ₹485) and has excellent reviews from our customers. Would you like to know more about its fragrance profile?",
  "is_ready": false
}
```

## Integration with Routing Agent

The Sales Agent is designed to work seamlessly with a Routing Agent that handles:
- Facebook Messenger webhook integration
- Customer message routing
- Frontend display of responses
- Handover to onboarding agent when `is_ready: true`

### Handover Logic
- When `is_ready: false`: Continue sending customer messages to Sales Agent
- When `is_ready: true`: Stop sending to Sales Agent, route to onboarding system

## Performance Considerations

- **Conversation Limits**: Automatically manages conversation history size
- **Product Caching**: Efficiently retrieves and caches product data
- **AI Rate Limits**: Implements proper error handling for OpenAI API limits
- **Database Indexing**: Optimized queries with proper indexing

## Monitoring and Logging

- Comprehensive logging for debugging and monitoring
- Health check endpoints for service monitoring
- Error tracking and graceful fallbacks
- Performance metrics for response times

## Security

- Input validation and sanitization
- Environment variable protection
- Database connection security
- API rate limiting (recommended for production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]
Pruned version of Manipulator for pitch purpose
