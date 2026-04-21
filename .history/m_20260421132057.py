from pymongo import MongoClient

# Your connection string
MONGODB_URI = "mongodb+srv://sara_db_user:sara@cluster0.hhaghbf.mongodb.net/?retryWrites=true&w=majority"

try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    print("✅ MongoDB Connected Successfully!")
    
    # List databases
    print("\n📁 Databases:")
    for db in client.list_database_names():
        print(f"   - {db}")

except Exception as e:
    print(f"❌ Connection failed: {e}")