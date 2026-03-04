"""
Act Skill - Draft emails, calendar integration, tracker updates
"""
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MatchResult:
    opportunity_id: str
    score: int
    confidence: str
    fits: List[str]
    gaps: List[str]
    angle: str


class OpportunityActor:
    """Handles notifications, calendar, and application actions."""
    
    def __init__(self, config: dict = None):
        if config is None:
            with open("config.json", 'r') as f:
                config = json.load(f)
        self.config = config
        self.user = config.get('profile', {})
        self.notifications = config.get('notifications', {})
    
    def generate_digest(self, matches: List[Dict], db_path: str) -> str:
        """Generate daily opportunity digest message."""
        high_matches = [m for m in matches if m.get('score', 0) >= 80]
        medium_matches = [m for m in matches if 60 <= m.get('score', 0) < 80]
        
        lines = [
            f"🎯 Opportunity Digest — {datetime.now().strftime('%b %d, %Y')}",
            "",
        ]
        
        if high_matches:
            lines.append(f"High Matches (80+): {len(high_matches)}")
            for i, m in enumerate(high_matches[:5], 1):
                lines.append(f"\n{i}. [{m.get('company', 'Unknown')}] {m.get('title', 'Untitled')} — Score: {m['score']}")
                fits = m.get('fits', [])
                if fits:
                    lines.append(f"   ✅ {fits[0]}")
                if m.get('url'):
                    lines.append(f"   🔗 {m['url']}")
            lines.append("")
        
        if medium_matches:
            lines.append(f"Medium Matches (60-79): {len(medium_matches)}")
            for i, m in enumerate(medium_matches[:3], 1):
                lines.append(f"   • [{m.get('company', 'Unknown')}] {m.get('title', 'Untitled')} — Score: {m['score']}")
            lines.append("")
        
        lines.extend([
            "Actions:",
            'Reply "apply <number>" → I\'ll draft the email',
            'Reply "save <number>" → Add to tracker + calendar',
            'Reply "skip <number>" → Mark rejected, learn from it',
            'Reply "more <number>" → Show full details',
        ])
        
        return "\n".join(lines)
    
    def notify(self, opportunities: List[Dict]) -> bool:
        """Send notification digest for scored opportunities."""
        db_path = Path(__file__).parent.parent / "data" / "opportunities.db"
        message = self.generate_digest(opportunities, str(db_path))
        return self.send_notification(message)
    
    def send_notification(self, message: str) -> bool:
        """Send notification via configured channel."""
        channel = self.notifications.get('channel', 'telegram')
        
        if channel == 'imessage':
            return self._send_imessage(message)
        elif channel == 'telegram':
            return self._send_telegram(message)
        else:
            print(f"[act] Unknown notification channel: {channel}")
            return False
    
    def _send_imessage(self, message: str) -> bool:
        """Send iMessage via AppleScript (macOS only)."""
        recipient = self.notifications.get('imessage_recipient', '')
        if not recipient:
            print("[act] No iMessage recipient configured")
            return False
        
        # Truncate if too long (iMessage has practical limits)
        if len(message) > 4000:
            message = message[:3950] + "\n... (truncated)"
        
        script = f'''
        tell application "Messages"
            set targetService to 1st service whose service type = iMessage
            set targetBuddy to buddy "{recipient}" of targetService
            send "{message.replace(chr(34), chr(92)+chr(34))}" to targetBuddy
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"[act] iMessage sent to {recipient}")
                return True
            else:
                print(f"[act] iMessage error: {result.stderr}")
                return False
        except Exception as e:
            print(f"[act] Failed to send iMessage: {e}")
            return False
    
    def _send_telegram(self, message: str) -> bool:
        """Send Telegram message (placeholder - requires bot token)."""
        # TODO: Implement Telegram bot integration
        # Requires: TELEGRAM_BOT_TOKEN, chat_id
        print("[act] Telegram not yet implemented")
        return False
    
    def add_calendar_event(self, title: str, date: str, event_type: str = "deadline") -> bool:
        """Add event to Apple Calendar via AppleScript."""
        calendar_name = self.config.get('calendar', {}).get('name', 'Job Hunt')
        
        # Parse date and add time if needed
        if 'T' not in date:
            if event_type == "deadline":
                date = f"{date}T17:00:00"  # End of business day
            elif event_type == "followup":
                date = f"{date}T09:00:00"  # Morning reminder
            else:
                date = f"{date}T10:00:00"
        
        notes = f"Type: {event_type}\nAuto-created by Opportunity Agent"
        
        script = f'''
        tell application "Calendar"
            tell calendar "{calendar_name}"
                set startDate to date "{date}"
                make new event with properties {{summary:"[Job Hunt] {title}", start date:startDate, end date:startDate + (1 * hours), description:"{notes}"}}
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"[act] Calendar event added: {title}")
                return True
            else:
                print(f"[act] Calendar error: {result.stderr}")
                return False
        except Exception as e:
            print(f"[act] Failed to add calendar event: {e}")
            return False
    
    def draft_email(self, match: Dict, template_type: str = "application") -> str:
        """Draft application email/cover letter."""
        user = self.user
        op = match['opportunity']
        analysis = match.get('analysis', {})
        
        if template_type == "application":
            angle = analysis.get('angle', 'my unique background and skills')
            
            email = f"""Subject: Application for {op['title']} - {user.get('name', 'Applicant')}

Dear Hiring Manager,

I am writing to express my strong interest in the {op['title']} position at {op['company']}. {angle}

Key qualifications I bring:
"""
            for fit in analysis.get('fits', [])[:3]:
                email += f"• {fit}\n"
            
            email += f"""
I would welcome the opportunity to discuss how I can contribute to your team.

Best regards,
{user.get('name', '')}
{user.get('email', '')}
{user.get('phone', '')}
"""
            return email
        
        elif template_type == "followup":
            return f"""Subject: Follow-up: {op['title']} Application

Dear Hiring Manager,

I hope this message finds you well. I wanted to follow up on my application for the {op['title']} position at {op['company']} submitted recently.

I remain very interested in the opportunity and would appreciate any update you might have on the hiring timeline.

Thank you for your time and consideration.

Best regards,
{user.get('name', '')}
"""
        
        return "Unknown template type"
    
    def update_tracker(self, opportunity_id: str, status: str, db_path: str):
        """Update opportunity status in database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE opportunities 
            SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), opportunity_id))
        
        conn.commit()
        conn.close()
        print(f"[act] Updated {opportunity_id} → {status}")
    
    def save_feedback(self, opportunity_id: str, feedback: str, db_path: str):
        """Save 👍/👎 feedback for learning loop."""
        feedback_file = db_path.replace('.db', '_feedback.json')
        
        try:
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except FileNotFoundError:
            feedback_data = {"feedback": []}
        
        feedback_data["feedback"].append({
            "opportunity_id": opportunity_id,
            "feedback": feedback,  # 'positive' or 'negative'
            "timestamp": datetime.now().isoformat()
        })
        
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        print(f"[act] Feedback saved: {opportunity_id} → {feedback}")


if __name__ == "__main__":
    # Test the act skill
    actor = OpportunityActor()
    
    # Test digest generation
    test_matches = [
        {
            'opportunity': {'title': 'AI Product Manager', 'company': 'TechCorp', 'url': 'https://example.com'},
            'score': 85,
            'fits': ['Strong AI background', 'Product experience']
        }
    ]
    digest = actor.generate_digest(test_matches, "data/opportunities.db")
    print(digest)
