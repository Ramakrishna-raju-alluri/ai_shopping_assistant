import boto3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

class ChatHistoryService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'chat-history-coles'
        self.table = self.dynamodb.Table(self.table_name)
        
    def _decimal_default(self, obj):
        """JSON serializer for Decimal objects"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _convert_floats_to_decimal(self, obj):
        """Recursively convert float values to Decimal for DynamoDB compatibility"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        else:
            return obj
    
    def create_chat_session(self, user_id: str, title: str = None, session_id: str = None) -> Dict[str, Any]:
        """Create a new chat session for a user"""
        try:
            # Use provided session_id or generate a new one
            if not session_id:
                session_id = f"chat_{user_id}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
            
            # Get current sessions to enforce 5 chat limit
            current_sessions = self.get_user_chat_sessions(user_id)
            
            # If user has 5 sessions, delete the oldest one
            if len(current_sessions) >= 5:
                oldest_session = min(current_sessions, key=lambda x: x['created_at'])
                self.delete_chat_session(user_id, oldest_session['session_id'])
                print(f"🗑️ Deleted oldest chat session: {oldest_session['session_id']}")
            
            # Create title if not provided
            if not title:
                title = f"New Chat"
            
            # Create new session
            session_data = {
                'user_id': user_id,
                'session_id': session_id,
                'title': title,
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'message_count': 0,
                'is_active': True
            }
            
            # Save to DynamoDB
            self.table.put_item(Item=session_data)
            
            print(f"✅ Created new chat session: {session_id}")
            return session_data
            
        except Exception as e:
            print(f"❌ Error creating chat session: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def add_message_to_session(self, user_id: str, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to an existing chat session"""
        try:
            # Get current session
            response = self.table.get_item(
                Key={'user_id': user_id, 'session_id': session_id}
            )
            
            if 'Item' not in response:
                print(f"❌ Session not found: {session_id}")
                return False
            
            session = response['Item']
            
            # Prepare message with timestamp and ID
            message_with_meta = message.copy()
            if 'id' not in message_with_meta:
                message_with_meta['id'] = str(uuid.uuid4())
            if 'timestamp' not in message_with_meta:
                message_with_meta['timestamp'] = datetime.now().isoformat()
            
            # Convert any float values to Decimal for DynamoDB compatibility
            message_with_meta = self._convert_floats_to_decimal(message_with_meta)
            
            print(f"🔄 Adding message to session {session_id}:")
            print(f"   Type: {message_with_meta.get('type')}")
            print(f"   Content: {message_with_meta.get('content', '')[:50]}...")
            print(f"   ID: {message_with_meta.get('id')}")
            print(f"   Timestamp: {message_with_meta.get('timestamp')}")
            
            # Add message to session
            if 'messages' not in session:
                session['messages'] = []
            
            session['messages'].append(message_with_meta)
            session['message_count'] = len(session['messages'])
            session['updated_at'] = datetime.now().isoformat()
            
            # Update title based on first user message if it's a generic title
            if (session.get('title', '') in ['New Chat', 'Chat'] and 
                message.get('type') == 'user' and 
                len([msg for msg in session['messages'] if msg.get('type') == 'user']) == 1):
                session['title'] = self._generate_title_from_message(message.get('content', ''))
            
            # Convert session data to DynamoDB-compatible format
            session = self._convert_floats_to_decimal(session)
            
            # Update in DynamoDB
            self.table.put_item(Item=session)
            
            print(f"✅ Added message to session: {session_id} (Total messages: {session['message_count']})")
            return True
            
        except Exception as e:
            print(f"❌ Error adding message to session: {str(e)}")
            return False
    
    def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user (up to 5)"""
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
            )
            
            sessions = response.get('Items', [])
            
            # Sort by updated_at (most recent first)
            sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            # Return only active sessions (limit 5)
            active_sessions = [s for s in sessions if s.get('is_active', True)][:5]
            
            print(f"📚 Retrieved {len(active_sessions)} chat sessions for user: {user_id}")
            return active_sessions
            
        except Exception as e:
            print(f"❌ Error retrieving chat sessions: {str(e)}")
            return []
    
    def get_chat_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get a specific chat session with all messages"""
        try:
            response = self.table.get_item(
                Key={'user_id': user_id, 'session_id': session_id}
            )
            
            if 'Item' not in response:
                print(f"❌ Chat session not found: {session_id}")
                return {}
            
            session = response['Item']
            
            # Sort messages by timestamp to ensure chronological order
            messages = session.get('messages', [])
            if messages:
                try:
                    messages.sort(key=lambda x: x.get('timestamp', ''))
                    print(f"📖 Retrieved chat session: {session_id} with {len(messages)} messages (sorted by timestamp)")
                except Exception as sort_error:
                    print(f"⚠️ Warning: Could not sort messages by timestamp: {str(sort_error)}")
                    print(f"📖 Retrieved chat session: {session_id} with {len(messages)} messages (unsorted)")
            else:
                print(f"📖 Retrieved chat session: {session_id} with 0 messages")
            
            # Update session with sorted messages
            session['messages'] = messages
            session['message_count'] = len(messages)
            
            return session
            
        except Exception as e:
            print(f"❌ Error retrieving chat session: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def delete_chat_session(self, user_id: str, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            self.table.delete_item(
                Key={'user_id': user_id, 'session_id': session_id}
            )
            
            print(f"🗑️ Deleted chat session: {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting chat session: {str(e)}")
            return False
    
    def update_session_title(self, user_id: str, session_id: str, new_title: str) -> bool:
        """Update the title of a chat session"""
        try:
            self.table.update_item(
                Key={'user_id': user_id, 'session_id': session_id},
                UpdateExpression="SET title = :title, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':title': new_title,
                    ':updated_at': datetime.now().isoformat()
                }
            )
            
            print(f"✏️ Updated session title: {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating session title: {str(e)}")
            return False
    
    def _generate_title_from_message(self, message: str) -> str:
        """Generate a meaningful title from the first user message"""
        if not message:
            return "New Chat"
        
        # Truncate and clean the message
        title = message.strip()[:50]
        if len(message) > 50:
            title += "..."
        
        return title
    
    def get_session_summary(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get a summary of a chat session (title, message count, last updated)"""
        try:
            response = self.table.get_item(
                Key={'user_id': user_id, 'session_id': session_id},
                ProjectionExpression='session_id, title, message_count, updated_at, created_at'
            )
            
            if 'Item' not in response:
                return {}
            
            return response['Item']
            
        except Exception as e:
            print(f"❌ Error getting session summary: {str(e)}")
            return {}

# Global instance
chat_history_service = ChatHistoryService() 