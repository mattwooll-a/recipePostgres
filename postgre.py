import os
import json
from supabase import create_client, Client

_ = load_dotenv(find_dotenv())
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL= os.getenv("SUPABASE_URL")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

