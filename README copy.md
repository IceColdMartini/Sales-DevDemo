
# Demo Sales Agent

This project is a simplified sales agent microservice for demonstration purposes.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    Create a `.env` file and fill in your database and Azure OpenAI credentials. A `.env.example` is provided.

3.  **Initialize the database:**
    You'll need a running PostgreSQL instance. You can use the provided `init-db.sql` script to create the necessary tables and seed some data.

4.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```

## API

The main endpoint is `/api/webhook`. It accepts a POST request with the following JSON body:

```json
{
  "sender": "user_id",
  "recipient": "page_id",
  "text": "Hello, I'm interested in a perfume."
}
```

It returns a JSON response like this:

```json
{
  "sender": "user_id",
  "product_interested": "Wild Stone Code Platinum Perfume",
  "response_text": "That's a great choice! The Wild Stone Code Platinum is a fantastic perfume.",
  "is_ready": false
}
```
