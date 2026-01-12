import json
import anthropic
from django.conf import settings

class ClaudeVideoAnalysisService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        # self.model = "claude-sonnet-4-20250514"   # sonnet 4
        self.model = "claude-sonnet-4-5-20250929"   # sonnet 4.5
        self.question_limit = 10
    
    def build_system_prompt(self, transcript_data, guidelines):
        """Build system prompt ONCE with guidelines + transcript (like Streamlit)"""
        return f"""{guidelines}

VIDEO ANALYSIS DATA:
{json.dumps(transcript_data, indent=2)}

Use this multimodal analysis data to provide comprehensive feedback and answer any questions about the video performance. The data includes voice features, facial expressions, head movement, eye contact, and transcript text."""
    
    def get_initial_analysis(self, system_prompt):
        """Generate initial analysis (like Streamlit first load)"""
        try:
            initial_prompt = "Please provide a complete analysis of this video following your guidelines."
            
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                max_tokens=1500,
                messages=[{"role": "user", "content": initial_prompt}]
            )
            
            response_text = response.content[0].text
            # Convert markdown bold to HTML
 
            return {
                'success': True,
                'analysis': response_text,
                'initial_prompt': initial_prompt
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_chat_message(self, system_prompt, message_history, new_message):
        """Send new message with full conversation context (like Streamlit chat)"""
        try:
            # Add new user message to history
            updated_history = message_history + [{"role": "user", "content": new_message}]
            
            # Send ALL messages with system prompt (exact Streamlit logic)
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                max_tokens=400,
                messages=updated_history
            )
            
            assistant_response = response.content[0].text
            
            # Add assistant response to history
            final_history = updated_history + [{"role": "assistant", "content": assistant_response}]
            
            return {
                'success': True,
                'response': assistant_response,
                'updated_history': final_history
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_question_limit(self, message_history):
        """Check if user has reached question limit"""
        user_questions = len([msg for msg in message_history if msg["role"] == "user"]) - 1  # Subtract initial prompt
        return {
            'questions_asked': user_questions,
            'limit_reached': user_questions >= self.question_limit,
            'remaining': max(0, self.question_limit - user_questions)
        }