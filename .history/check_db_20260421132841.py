from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://sara_db_user:YOUR_CORRECT_PASSWORD@cluster0.hhaghbf.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGODB_URI)
db = client['communisense']

print("📁 Collections in communisense database:")
for collection in db.list_collection_names():
    count = db[collection].count_documents({})
    print(f"   - {collection}: {count} documents")

# Show users
print("\n👥 Users:")
for user in db['users'].find({}):
    print(f"   - {user.get('username')} - {user.get('email')}")