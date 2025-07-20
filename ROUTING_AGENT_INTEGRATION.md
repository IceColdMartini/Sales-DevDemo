# Sales Agent Integration Guide for Routing Agent

## Overview
This document provides all the details needed to integrate with the Sales Agent microservice for customer conversation handling and product recommendations.

## Base URL
```
http://localhost:8000
```

## Main Integration Endpoint

### POST `/api/webhook`
**Purpose**: Send customer messages to Sales Agent and receive AI-generated responses

#### Request Format
```json
{
  "sender": "facebook_profile_id",
  "recipient": "page_id", 
  "text": "customer_message_text"
}
```

#### Request Headers
```
Content-Type: application/json
```

#### Response Format
```json
{
  "sender": "facebook_profile_id",
  "product_interested": "Product Name or null",
  "response_text": "AI-generated response to send to customer",
  "is_ready": false
}
```

#### Response Fields Explanation

| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | The same Facebook profile ID you sent |
| `product_interested` | string/null | Name of product customer is most interested in |
| `response_text` | string | AI response to display to the customer |
| `is_ready` | boolean | **CRITICAL**: When `true`, stop sending to Sales Agent and hand over to onboarding |

## Integration Logic

### 1. Message Flow
```
Customer Message → Routing Agent → Sales Agent → AI Response → Routing Agent → Customer
```

### 2. Handover Logic
- **When `is_ready: false`**: Continue sending customer messages to Sales Agent
- **When `is_ready: true`**: STOP sending to Sales Agent, route to onboarding system

### 3. Sample Integration Code

#### Python Example
```python
import requests

def send_to_sales_agent(facebook_profile_id, page_id, customer_message):
    url = "http://localhost:8000/api/webhook"
    payload = {
        "sender": facebook_profile_id,
        "recipient": page_id,
        "text": customer_message
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        
        # Send AI response back to customer
        send_to_customer(facebook_profile_id, data["response_text"])
        
        # Check if ready for purchase
        if data["is_ready"]:
            # Hand over to onboarding agent
            hand_over_to_onboarding(facebook_profile_id, data["product_interested"])
        
        return data
    else:
        # Handle error
        return None
```

#### Node.js Example
```javascript
const axios = require('axios');

async function sendToSalesAgent(facebookProfileId, pageId, customerMessage) {
    try {
        const response = await axios.post('http://localhost:8000/api/webhook', {
            sender: facebookProfileId,
            recipient: pageId,
            text: customerMessage
        });
        
        const data = response.data;
        
        // Send AI response to customer
        await sendToCustomer(facebookProfileId, data.response_text);
        
        // Check handover condition
        if (data.is_ready) {
            // Route to onboarding system
            await handOverToOnboarding(facebookProfileId, data.product_interested);
        }
        
        return data;
    } catch (error) {
        console.error('Sales Agent error:', error);
        return null;
    }
}
```

## Additional Endpoints

### Health Check
**GET** `/health`
- Check if Sales Agent is running and databases are connected

### Conversation Status  
**GET** `/api/webhook/status/{sender_id}`
- Get conversation statistics for debugging

### Reset Conversation (Testing)
**DELETE** `/api/webhook/conversation/{sender_id}`
- Reset conversation history for testing

## Error Handling

### Common Response Codes
- `200`: Success
- `400`: Bad request (missing required fields)
- `500`: Internal server error

### Error Response Format
```json
{
    "detail": "Error message description"
}
```

## Data You Need to Provide to Sales Agent

### From Facebook Webhook
```json
{
  "sender": { "id": "24869641652625416" },
  "recipient": { "id": "579889325206435" },
  "message": { "text": "Customer message" }
}
```

### Transform to Sales Agent Format
```json
{
  "sender": "24869641652625416",
  "recipient": "579889325206435", 
  "text": "Customer message"
}
```

## Data Sales Agent Provides to You

### Response Data
```json
{
  "sender": "24869641652625416",
  "product_interested": "Wild Stone Code Platinum Perfume",
  "response_text": "Great choice! This premium perfume...",
  "is_ready": false
}
```

### Usage
1. **Display `response_text`** to customer via Facebook Messenger
2. **Track `product_interested`** for analytics
3. **Monitor `is_ready`** for handover logic

## Critical Implementation Notes

### 1. Handover Logic
```python
if response_data["is_ready"] == True:
    # STOP sending messages to Sales Agent
    # Route to onboarding system instead
    onboarding_agent.handle(customer_id, product_interested)
```

### 2. Error Fallback
```python
try:
    response = sales_agent.process(message)
except:
    # Fallback to generic response
    response_text = "I'm sorry, I'm having technical difficulties. Please try again."
```

### 3. Conversation Context
- Sales Agent automatically maintains conversation history
- No need to send previous messages
- Each customer's conversation is tracked by `sender` ID

## Testing

### Test Endpoint
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
  "response_text": "I'd love to help you find the perfect fragrance! Based on what you're looking for, I recommend our Wild Stone Code Platinum Perfume...",
  "is_ready": false
}
```

## Environment Requirements

- Sales Agent API must be running on `http://localhost:8000`
- PostgreSQL and MongoDB databases must be available
- Azure OpenAI credentials must be configured

## Support

For any integration issues:
1. Check `/health` endpoint for system status
2. Review Sales Agent logs for errors
3. Test with curl commands first
4. Verify JSON payload format

---

**IMPORTANT**: Always check the `is_ready` field in the response. When it's `true`, the customer is ready to purchase and should be handed over to the onboarding system immediately.
