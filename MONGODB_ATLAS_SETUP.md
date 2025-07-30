# MongoDB Atlas Migration Guide

This guide will help you migrate your Sales Agent application from local MongoDB to MongoDB Atlas (cloud database).

## What is MongoDB Atlas?

MongoDB Atlas is MongoDB's cloud database service that provides:
- ✅ Remote accessibility from any location
- ✅ High availability and automatic backups
- ✅ Built-in security features
- ✅ Free tier available (M0) - perfect for development/testing

## Step-by-Step Setup Process

### 1. Create MongoDB Atlas Account

1. **Go to https://cloud.mongodb.com/**
2. **Sign up for a free account** (use your email)
3. **Verify your email address**

### 2. Create a Cluster

1. **Click "Create a New Cluster"**
2. **Choose "M0 Sandbox" (FREE tier)**
3. **Select a cloud provider and region** (choose one closest to you)
4. **Name your cluster** (e.g., "sales-agent-cluster")
5. **Click "Create Cluster"** (takes 3-7 minutes)

### 3. Create Database User

1. **Go to "Database Access" in the left sidebar**
2. **Click "Add New Database User"**
3. **Choose "Password" authentication**
4. **Set username and password** (remember these!)
   - Username: `sales_admin`
   - Password: `your_secure_password`
5. **Set privileges to "Read and write to any database"**
6. **Click "Add User"**

### 4. Configure Network Access

1. **Go to "Network Access" in the left sidebar**
2. **Click "Add IP Address"**
3. **For development, click "Allow Access from Anywhere"** (adds 0.0.0.0/0)
   - For production, add only your specific IP addresses
4. **Click "Confirm"**

### 5. Get Connection String

1. **Go to "Clusters" in the left sidebar**
2. **Click "Connect" on your cluster**
3. **Choose "Connect your application"**
4. **Select "Python" and version "3.6 or later"**
5. **Copy the connection string** - it looks like:
   ```
   mongodb+srv://sales_admin:<password>@sales-agent-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 6. Update Your .env File

Replace `<password>` in the connection string with your actual password and add these variables to your `.env` file:

```bash
# MongoDB Atlas Configuration
USE_MONGODB_ATLAS=true
MONGODB_ATLAS_URI=mongodb+srv://sales_admin:your_secure_password@sales-agent-cluster.xxxxx.mongodb.net/sales_conversations?retryWrites=true&w=majority
MONGODB_ATLAS_DB_NAME=sales_conversations

# Keep these for fallback if needed
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=conversations_db
```

### 7. Test Connection

Run the migration script to test your Atlas connection:

```bash
python migrate_to_atlas.py
# Choose option 1 to test connection
```

### 8. Migrate Existing Data (if any)

If you have existing conversations in local MongoDB:

```bash
python migrate_to_atlas.py
# Choose option 2 to migrate data
```

### 9. Update Docker Configuration

Since you'll be using cloud Atlas, you can remove local MongoDB from docker-compose.yml if desired, or keep it as backup. The application will automatically use Atlas when `USE_MONGODB_ATLAS=true`.

## Verification

1. **Start your application:**
   ```bash
   python main.py
   ```

2. **Check health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

   You should see:
   ```json
   {
     "databases": {
       "mongodb": "connected",
       "mongodb_type": "MongoDB Atlas (Cloud)"
     },
     "configuration": {
       "using_atlas": true
     }
   }
   ```

3. **Test conversation storage:**
   Send a test message and verify it's stored in Atlas dashboard.

## Atlas Dashboard Features

- **Real-time Monitoring**: View connection stats and performance
- **Data Browser**: Browse your conversations directly in the web interface
- **Backup & Restore**: Automatic backups (in paid tiers)
- **Alerts**: Set up monitoring alerts

## Troubleshooting

### Connection Issues

1. **Check IP Allowlist**: Ensure your IP is allowed in Network Access
2. **Verify Credentials**: Double-check username/password in connection string
3. **Test Network**: Try connecting from different network if behind corporate firewall

### Common Errors

1. **"Authentication failed"**
   - Check username/password in connection string
   - Ensure user has correct permissions

2. **"Connection timeout"**
   - Check network access settings
   - Verify your IP is whitelisted

3. **"SSL/TLS error"**
   - Ensure you're using `mongodb+srv://` (not `mongodb://`)
   - Check that TLS is enabled

## Security Best Practices

1. **Use strong passwords** for database users
2. **Limit IP access** to only necessary addresses in production
3. **Enable 2FA** on your Atlas account
4. **Regularly rotate passwords**
5. **Use connection string with SSL/TLS** (mongodb+srv://)

## Cost Information

- **M0 (Free Tier)**: 512 MB storage, shared RAM
- **Paid Tiers**: Start from $9/month with dedicated resources
- **Data Transfer**: First 1GB/month free

## Support

- **Atlas Documentation**: https://docs.atlas.mongodb.com/
- **Community Forums**: https://community.mongodb.com/
- **Support**: Available for paid tiers

---

**Next Steps After Migration:**
1. Test the application thoroughly with Atlas
2. Monitor performance in Atlas dashboard
3. Set up appropriate alerts and backups
4. Consider upgrading to paid tier for production use
