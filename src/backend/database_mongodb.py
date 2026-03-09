"""
MongoDB Atlas Database Manager
Handles all database operations for lead storage and retrieval
"""
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from bson import ObjectId
from .config import config


class MongoDBManager:
    """Manage MongoDB Atlas database operations"""
    
    def __init__(self):
        """Initialize MongoDB client"""
        try:
            self.client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[config.MONGODB_DB_NAME]
            self.leads_collection = self.db['leads']
            self.queries_collection = self.db['search_queries']
            self._create_indexes()
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {config.MONGODB_DB_NAME}")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    def _create_indexes(self):
        """Create necessary indexes in MongoDB"""
        try:
            # Leads collection indexes
            self.leads_collection.create_index([('email', ASCENDING)])
            self.leads_collection.create_index([('source_platform', ASCENDING)])
            self.leads_collection.create_index([('quality_score', DESCENDING)])
            self.leads_collection.create_index([('linkedin_url', ASCENDING)])
            self.leads_collection.create_index([('created_at', DESCENDING)])
            self.leads_collection.create_index([('query_id', ASCENDING)])
            
            # Search queries collection indexes
            self.queries_collection.create_index([('created_at', DESCENDING)])
        except PyMongoError as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def save_query(self, raw_query: str, keywords_data: Dict) -> str:
        """
        Save search query metadata
        
        Args:
            raw_query: Original user query
            keywords_data: Extracted keywords and parameters
            
        Returns:
            Query ID (as string)
        """
        try:
            data = {
                'raw_query': raw_query,
                'extracted_keywords': keywords_data,
                'platforms_searched': keywords_data.get('platforms', []),
                'total_leads_found': 0,
                'total_leads_filtered': 0,
                'created_at': datetime.utcnow()
            }
            
            result = self.queries_collection.insert_one(data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving query: {e}")
            return None
    
    def save_leads(self, leads: List[Dict], query_id: Optional[str] = None) -> int:
        """
        Save leads to database
        
        Args:
            leads: List of lead dictionaries
            query_id: Associated query ID
            
        Returns:
            Number of leads saved
        """
        try:
            # Prepare leads for insertion
            prepared_leads = []
            for lead in leads:
                prepared_lead = {
                    'name': lead.get('name'),
                    'email': lead.get('email'),
                    'phone': lead.get('phone'),
                    'linkedin_url': lead.get('linkedin_url'),
                    'company': lead.get('company'),
                    'job_title': lead.get('job_title'),
                    'location': lead.get('location'),
                    'source_platform': lead.get('source', 'unknown'),
                    'raw_data': lead.get('raw_data', {}),
                    'quality_score': lead.get('quality_score', 0.0),
                    'warmth_score': lead.get('warmth_score', 0.0),
                    'sentiment': lead.get('sentiment', 'neutral'),
                    'is_duplicate': lead.get('is_duplicate', False),
                    'query_id': query_id,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                prepared_leads.append(prepared_lead)
            
            if not prepared_leads:
                return 0
            
            # Insert all leads
            result = self.leads_collection.insert_many(prepared_leads)
            total_saved = len(result.inserted_ids)
            
            # Update query with counts
            if query_id:
                self.queries_collection.update_one(
                    {'_id': ObjectId(query_id)},
                    {'$set': {'total_leads_found': total_saved}}
                )
            
            return total_saved
            
        except Exception as e:
            print(f"Error saving leads: {e}")
            return 0
    
    def get_leads(self, 
                  query_id: Optional[str] = None,
                  min_quality_score: float = 0.0,
                  limit: int = 100) -> List[Dict]:
        """
        Retrieve leads from database
        
        Args:
            query_id: Filter by query ID
            min_quality_score: Minimum quality score
            limit: Maximum number of results
            
        Returns:
            List of leads
        """
        try:
            filter_query = {
                'is_duplicate': False,
                'quality_score': {'$gte': min_quality_score}
            }
            
            if query_id:
                filter_query['query_id'] = query_id
            
            cursor = self.leads_collection.find(filter_query).sort(
                'quality_score', DESCENDING
            ).limit(limit)
            
            leads = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['id'] = str(doc['_id'])
                del doc['_id']
                leads.append(doc)
            
            return leads
            
        except Exception as e:
            print(f"Error retrieving leads: {e}")
            return []
    
    def mark_duplicates(self, duplicate_ids: List[str]):
        """Mark leads as duplicates"""
        try:
            object_ids = [ObjectId(id) for id in duplicate_ids]
            self.leads_collection.update_many(
                {'_id': {'$in': object_ids}},
                {'$set': {'is_duplicate': True, 'updated_at': datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Error marking duplicates: {e}")
    
    def update_lead_scores(self, lead_id: str, quality_score: float, 
                          warmth_score: float, sentiment: str):
        """Update lead quality metrics"""
        try:
            self.leads_collection.update_one(
                {'_id': ObjectId(lead_id)},
                {
                    '$set': {
                        'quality_score': quality_score,
                        'warmth_score': warmth_score,
                        'sentiment': sentiment,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error updating lead scores: {e}")
    
    def get_stats(self, query_id: Optional[str] = None) -> Dict:
        """Get statistics about leads"""
        try:
            filter_query = {}
            if query_id:
                filter_query['query_id'] = query_id
            
            total_leads = self.leads_collection.count_documents(filter_query)
            
            # Count by platform
            platform_pipeline = [
                {'$match': filter_query},
                {'$group': {
                    '_id': '$source_platform',
                    'count': {'$sum': 1}
                }}
            ]
            platform_counts = {
                doc['_id']: doc['count'] 
                for doc in self.leads_collection.aggregate(platform_pipeline)
            }
            
            # Calculate average quality score
            avg_pipeline = [
                {'$match': filter_query},
                {'$group': {
                    '_id': None,
                    'avg_quality': {'$avg': '$quality_score'},
                    'avg_warmth': {'$avg': '$warmth_score'}
                }}
            ]
            avg_result = list(self.leads_collection.aggregate(avg_pipeline))
            avg_quality = avg_result[0]['avg_quality'] if avg_result else 0.0
            avg_warmth = avg_result[0]['avg_warmth'] if avg_result else 0.0
            
            return {
                'total_leads': total_leads,
                'platforms': platform_counts,
                'avg_quality_score': avg_quality,
                'avg_warmth_score': avg_warmth
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
